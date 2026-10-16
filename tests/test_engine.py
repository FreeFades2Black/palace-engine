import json
import shutil
from pathlib import Path
from fastapi.testclient import TestClient

from engine.adaptive_srs import calculate_sm2, process_daily_test_results
from engine.cognitive_linter import audit_loci_quality
from engine.correlate import correlate_palace_with_trends
from engine.db import get_telemetry_metrics, init_db, record_interaction
from engine.parser import load_palace_map, load_taxonomy, parse_recall_logs
from engine.scoring import evaluate_gaps
from engine.scraper import analyze_trends
from engine.server import app
from engine.suggest import suggest_next_drills


def test_schemas_and_parser():
    palace = load_palace_map("data")
    assert len(palace["loci"]) >= 4
    ids = {l["id"] for l in palace["loci"]}
    assert {
        "driveway_road",
        "front_door",
        "hallway_thermostat",
        "porch_mailbox",
    }.issubset(ids)

    taxonomy = load_taxonomy("data")
    assert taxonomy["exam"].startswith("AWS Certified Solutions Architect")

    sessions = parse_recall_logs("data")
    assert len(sessions) >= 1
    assert sessions[0]["date"] == "2026-10-16"


def test_cognitive_linter():
    issues = audit_loci_quality("data/palace_map.json")
    assert issues == [], f"Expected zero cognitive lint issues, found: {issues}"


def test_adaptive_srs_and_sm2(tmp_path):
    # Verify SM-2 collapse on failure (< 3)
    rep, ef, interval = calculate_sm2(repetition=4, ease_factor=2.5, interval=15, quality=2)
    assert rep == 0
    assert interval == 1
    assert ef < 2.5

    # Verify SM-2 progression on instant recall (5)
    rep2, ef2, interval2 = calculate_sm2(repetition=2, ease_factor=2.5, interval=6, quality=5)
    assert rep2 == 3
    assert interval2 == 15
    assert ef2 >= 2.5

    temp_data = tmp_path / "data"
    shutil.copytree(Path("data"), temp_data)
    updated_palace = process_daily_test_results(
        str(temp_data / "daily_test.json"),
        str(temp_data / "palace_map.json"),
    )
    loci_by_id = {l["id"]: l for l in updated_palace["loci"]}
    assert loci_by_id["hallway_thermostat"]["interval_days"] == 1
    assert "AWS Control Tower Guardrails" in loci_by_id["hallway_thermostat"]["confusion_pairs"]


def test_scraper_and_correlate():
    mock_posts = [
        {
            "title": "Just passed SAA-C03!",
            "content": "The exam was heavy on Aurora serverless and Global Accelerator static IP routing. Make sure you know SQS fanout with SNS.",
        }
    ]
    hits, notes = analyze_trends(mock_posts)
    assert hits["Aurora"] == 1
    assert hits["Global Accelerator"] == 1
    assert hits["Integration Decoupling"] == 1
    assert len(notes) >= 1

    radar = correlate_palace_with_trends("data/palace_map.json", "data/exam_trends.json")
    assert len(radar) >= 4
    statuses = {r["id"]: r["status"] for r in radar}
    assert "CRITICAL DEFICIT" in statuses["hallway_thermostat"]


def test_scoring_and_suggestions(tmp_path):
    temp_data = tmp_path / "data"
    shutil.copytree(Path("data"), temp_data)

    gaps, loci_map = evaluate_gaps(str(temp_data))
    assert len(gaps) >= 1
    assert loci_map["driveway_road"]["stability_score"] >= 0.85
    assert loci_map["front_door"]["stability_score"] >= 0.90

    saved = json.loads((temp_data / "palace_map.json").read_text(encoding="utf-8"))
    assert "loci" in saved

    drills = suggest_next_drills(str(temp_data), top_n=2)
    assert len(drills) == 2
    assert drills[0]["id"] == "hallway_thermostat"


def test_db_and_fastapi_deck(tmp_path):
    test_db = tmp_path / "interactions.db"
    init_db(test_db)
    record_interaction("driveway_road", 4200, 5, db_path=test_db)
    metrics = get_telemetry_metrics(test_db)
    assert metrics["total_drills"] == 1
    assert metrics["avg_latency_ms"] == 4200.0
    assert metrics["pass_rate"] == 100.0

    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "[PALACE-DECK]" in resp.text

    locus_resp = client.get("/api/locus/driveway_road")
    assert locus_resp.status_code == 200
    assert locus_resp.json()["id"] == "driveway_road"

    next_resp = client.get("/api/drill/next")
    assert next_resp.status_code == 200
    assert "id" in next_resp.json()
