import json
import shutil
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient

from engine.adaptive_srs import calculate_sm2, process_daily_test_results
from engine.cognitive_linter import audit_loci_quality
from engine.competency_gate import (
    CompetencyEvidence,
    CompetencyGate,
    apply_competency_transition,
)
from engine.correlate import correlate_palace_with_trends
from engine.db import get_telemetry_metrics, init_db, record_interaction
from engine.evaluator_rubric import (
    RUBRIC_EVALUATION_PROMPT,
    evaluate_candidate_response,
    rubric_to_evidence,
)
from engine.parser import load_palace_map, load_taxonomy, parse_recall_logs
from engine.scoring import evaluate_gaps
from engine.scraper import analyze_trends
from engine.server import app
from engine.suggest import suggest_next_drills


def test_schemas_and_parser():
    palace = load_palace_map("data")
    assert len(palace["loci"]) >= 3
    ids = {l["id"] for l in palace["loci"]}
    assert {
        "driveway_curb",
        "front_door_perimeter",
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


def test_competency_gate_and_rubric(tmp_path):
    assert "FACTUAL_PRECISION" in RUBRIC_EVALUATION_PROMPT
    assert "BOUNDARY_DISCRIMINATION" in RUBRIC_EVALUATION_PROMPT

    # Stage 1 -> Stage 2 promotion (<= 2200ms and boundary identified)
    gate1 = CompetencyGate("porch_mailbox", current_stage=1)
    ev1 = CompetencyEvidence(factual_latency_ms=1800, correct_boundary_identified=True)
    res1 = gate1.evaluate_promotion(ev1)
    assert res1["new_stage"] == 2
    assert res1["action"] == "PROMOTE"

    # Stage 2 -> Stage 1 demotion on boundary failure
    gate2 = CompetencyGate("driveway_curb", current_stage=2)
    ev_fail = CompetencyEvidence(factual_latency_ms=1500, correct_boundary_identified=False)
    res_demote = gate2.evaluate_promotion(ev_fail)
    assert res_demote["new_stage"] == 1
    assert res_demote["action"] == "DEMOTE"

    # Stage 2 -> Stage 3 promotion (boundary + >= 2 tradeoffs)
    ev2 = CompetencyEvidence(
        factual_latency_ms=2500,
        correct_boundary_identified=True,
        tradeoffs_addressed=["cost", "latency"],
    )
    res2 = gate2.evaluate_promotion(ev2)
    assert res2["new_stage"] == 3
    assert res2["action"] == "PROMOTE"

    # Stage 3 -> Stage 4 mastery (boundary + >= 3 tradeoffs + >= 1 failure mode)
    gate3 = CompetencyGate("front_door_perimeter", current_stage=3)
    ev3 = CompetencyEvidence(
        factual_latency_ms=3000,
        correct_boundary_identified=True,
        tradeoffs_addressed=["cost", "latency", "operational_overhead"],
        failure_modes_mitigated=["poison_pill", "duplicate_execution"],
    )
    res3 = gate3.evaluate_promotion(ev3)
    assert res3["new_stage"] == 4
    assert res3["action"] == "PROMOTE_TO_MASTERY"

    rubric = evaluate_candidate_response(
        "SQS FIFO 14-day retention vs Kinesis: addresses cost, latency, and operational overhead while using a DLQ redrive policy for poison pill and duplicate messages.",
        distractors=["Amazon Kinesis Data Streams"],
    )
    assert rubric["boundary_discrimination"] is True
    assert len(rubric["tradeoffs_identified"]) >= 3
    assert len(rubric["failure_modes_covered"]) >= 1

    evidence_obj = rubric_to_evidence(rubric, factual_latency_ms=1900)
    temp_palace = tmp_path / "palace_map.json"
    shutil.copy(Path("data/palace_map.json"), temp_palace)
    transition = apply_competency_transition("front_door_perimeter", evidence_obj, str(temp_palace))
    assert transition["stage_before"] == 1
    assert transition["stage_after"] == 2


def test_adaptive_srs_and_sm2(tmp_path):
    rep, ef, interval = calculate_sm2(repetition=4, ease_factor=2.5, interval=15, quality=2)
    assert rep == 0
    assert interval == 1
    assert ef < 2.5

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
    assert loci_by_id["porch_mailbox"]["interval_days"] == 1
    assert "AWS Control Tower Guardrails" in loci_by_id["porch_mailbox"]["confusion_pairs"]


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
    assert len(radar) >= 3
    statuses = {r["id"]: r["status"] for r in radar}
    assert "CRITICAL DEFICIT" in statuses["porch_mailbox"]


def test_scoring_and_suggestions(tmp_path):
    temp_data = tmp_path / "data"
    shutil.copytree(Path("data"), temp_data)

    gaps, loci_map = evaluate_gaps(str(temp_data))
    assert len(gaps) >= 1
    assert loci_map["driveway_curb"]["stability_score"] >= 0.85
    assert loci_map["front_door_perimeter"]["stability_score"] >= 0.90

    saved = json.loads((temp_data / "palace_map.json").read_text(encoding="utf-8"))
    assert "loci" in saved

    drills = suggest_next_drills(str(temp_data), top_n=2)
    assert len(drills) == 2
    assert drills[0]["id"] == "porch_mailbox"


def test_db_and_fastapi_deck(tmp_path):
    test_db = tmp_path / "interactions.db"
    init_db(test_db)
    record_interaction(
        "driveway_curb",
        1800,
        5,
        stage_before=1,
        stage_after=2,
        boundary_passed=True,
        tradeoffs_logged=["cost", "latency"],
        failure_modes_logged=["poison_pill"],
        db_path=test_db,
    )
    metrics = get_telemetry_metrics(test_db)
    assert metrics["total_drills"] == 1
    assert metrics["avg_latency_ms"] == 1800.0
    assert metrics["pass_rate"] == 100.0

    with sqlite3.connect(test_db) as conn:
        row = conn.execute(
            "SELECT stage_before, stage_after, boundary_passed, tradeoffs_logged, failure_modes_logged FROM drill_interactions"
        ).fetchone()
    assert row == (1, 2, 1, '["cost", "latency"]', '["poison_pill"]')

    client = TestClient(app)
    resp = client.get("/", headers={"Cf-Access-Authenticated-User-Email": "architect@omarchy.local"})
    assert resp.status_code == 200
    assert "[PALACE-DECK]" in resp.text
    assert 'rel="manifest" href="/static/manifest.json"' in resp.text
    assert "width=device-width, initial-scale=1.0" in resp.text
    assert "architect@omarchy.local" in resp.text

    manifest_resp = client.get("/static/manifest.json")
    assert manifest_resp.status_code == 200
    assert manifest_resp.json()["short_name"] == "PalaceDeck"

    locus_resp = client.get("/api/locus/driveway_curb")
    assert locus_resp.status_code == 200
    assert locus_resp.json()["id"] == "driveway_curb"

    next_resp = client.get("/api/drill/next")
    assert next_resp.status_code == 200
    assert "id" in next_resp.json()
