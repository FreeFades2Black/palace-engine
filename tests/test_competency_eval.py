# tests/test_competency_eval.py
import shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from engine.competency_gate import CompetencyGate, CompetencyEvidence
from engine.correlate import calculate_priority_score
from engine.evaluator_rubric import rubric_to_evidence
from engine.server import app


def test_stage_1_to_2_promotion_on_fast_recall():
    gate = CompetencyGate(locus_id="porch_mailbox", current_stage=1)

    # Sub-2-second recall with accurate boundary
    evidence = CompetencyEvidence(
        factual_latency_ms=1450,
        correct_boundary_identified=True,
        tradeoffs_addressed=[],
        failure_modes_mitigated=[],
    )
    result = gate.evaluate_promotion(evidence)
    assert result["action"] == "PROMOTE"
    assert result["new_stage"] == 2


def test_stage_2_demotion_on_boundary_failure():
    gate = CompetencyGate(locus_id="porch_mailbox", current_stage=2)

    # Distractor confusion: picked Kinesis over SQS without justifying shard vs queue limits
    evidence = CompetencyEvidence(
        factual_latency_ms=3200,
        correct_boundary_identified=False,
        tradeoffs_addressed=["cost"],
        failure_modes_mitigated=[],
    )
    result = gate.evaluate_promotion(evidence)
    assert result["action"] == "DEMOTE"
    assert result["new_stage"] == 1
    assert "Snapping back to Stage 1" in result["reason"]


def test_stage_2_to_3_promotion_with_tradeoffs():
    gate = CompetencyGate(locus_id="driveway_curb", current_stage=2)

    # Correct boundary + multi-variable trade-off analysis
    evidence = CompetencyEvidence(
        factual_latency_ms=2800,
        correct_boundary_identified=True,
        tradeoffs_addressed=["latency", "caching_layer_overhead", "non_http_protocol"],
        failure_modes_mitigated=[],
    )
    result = gate.evaluate_promotion(evidence)
    assert result["action"] == "PROMOTE"
    assert result["new_stage"] == 3


def test_priority_score_formula():
    # Priority Score = (5 - competency_stage) * 2.0 + (heat_score * 1.5) - (stability * 1.0)
    score = calculate_priority_score(competency_stage=1, heat_score=8, stability=0.75)
    assert score == 19.25
