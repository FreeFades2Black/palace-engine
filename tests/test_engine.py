import json
import shutil
from pathlib import Path
from engine.parser import load_palace_map, load_taxonomy, parse_recall_logs
from engine.scoring import evaluate_gaps
from engine.suggest import suggest_next_drills


def test_schemas_and_parser():
    palace = load_palace_map("data")
    assert len(palace["loci"]) >= 3
    ids = {l["id"] for l in palace["loci"]}
    assert {"driveway_road", "front_door", "hallway_thermostat"}.issubset(ids)

    taxonomy = load_taxonomy("data")
    assert taxonomy["exam"].startswith("AWS Certified Solutions Architect")

    sessions = parse_recall_logs("data")
    assert len(sessions) >= 1
    assert sessions[0]["date"] == "2026-10-16"


def test_scoring_and_suggestions(tmp_path):
    temp_data = tmp_path / "data"
    shutil.copytree(Path("data"), temp_data)

    gaps, loci_map = evaluate_gaps(str(temp_data))
    assert len(gaps) >= 1
    assert loci_map["driveway_road"]["stability_score"] >= 0.85
    assert loci_map["front_door"]["stability_score"] >= 0.90

    # Verify updated palace_map.json is valid JSON
    saved = json.loads((temp_data / "palace_map.json").read_text(encoding="utf-8"))
    assert "loci" in saved

    drills = suggest_next_drills(str(temp_data), top_n=2)
    assert len(drills) == 2
    assert drills[0]["id"] == "hallway_thermostat"
