# engine/evaluator_rubric.py
import json
from typing import Dict, List
from engine.competency_gate import CompetencyEvidence

RUBRIC_EVALUATION_PROMPT = """
You are a Lead AWS Solutions Architect evaluating a candidate's answer to an architectural challenge.
Do not accept surface-level keyword stuffing. Analyze their reasoning against four strict dimensions:

1. FACTUAL_PRECISION: Are service limits and capabilities exact (not approximate)?
2. BOUNDARY_DISCRIMINATION: Did they explicitly articulate why alternative/distractor services fail in this scenario?
3. TRADEOFF_DEPTH: Did they analyze cost, latency, blast radius, or operational overhead?
4. FAILURE_MODE_AWARENESS: Did they address retries, poison pills, throttling, or disaster recovery?

Output JSON format strictly:
{
  "factual_precision": true,
  "boundary_discrimination": true,
  "tradeoffs_identified": ["cost", "operational_overhead"],
  "failure_modes_covered": ["duplicate_message_handling"],
  "score_out_of_10": 8.5,
  "critique": "Candidate correctly separated SQS from Kinesis based on individual message acking vs partition ordering, but failed to address DLQ redrive policies."
}
"""

TRADEOFF_KEYWORDS = {
    "cost": ["cost", "pricing", "hourly", "data transfer", "billing", "expensive", "free"],
    "latency": ["latency", "millisecond", "sub-second", "anycast", "caching", "ttl", "edge"],
    "operational_overhead": ["operational", "managed", "serverless", "maintenance", "patching", "overhead"],
    "blast_radius": ["blast radius", "multi-account", "scp", "isolation", "boundary", "least privilege"],
}

FAILURE_MODE_KEYWORDS = {
    "poison_pill": ["poison pill", "dlq", "dead-letter", "redrive"],
    "duplicate_execution": ["idempotent", "idempotency", "duplicate", "fifo", "deduplication", "exactly-once"],
    "throttling": ["throttling", "backoff", "jitter", "rate limit", "quota", "burst"],
    "regional_outage": ["failover", "multi-region", "health check", "rto", "rpo", "dr"],
}


def evaluate_candidate_response(
    response_text: str,
    distractors: List[str] = None,
) -> Dict:
    """Evaluates an architectural justification against the 4 rubric dimensions."""
    lower = response_text.lower()
    distractors = distractors or []

    # Check boundary discrimination (mentions comparison / why alternative fails)
    boundary_markers = ["vs", "instead of", "whereas", "unlike", "fails", "cannot", "boundary"]
    mentioned_distractor = any(d.lower().split()[0] in lower for d in distractors if d)
    boundary_discrimination = mentioned_distractor or any(m in lower for m in boundary_markers)

    tradeoffs_identified = [
        dim for dim, words in TRADEOFF_KEYWORDS.items() if any(w in lower for w in words)
    ]
    failure_modes_covered = [
        mode for mode, words in FAILURE_MODE_KEYWORDS.items() if any(w in lower for w in words)
    ]

    factual_precision = any(char.isdigit() for char in response_text) or len(response_text.strip()) >= 40

    raw_score = (
        (2.5 if factual_precision else 0.0)
        + (2.5 if boundary_discrimination else 0.0)
        + min(2.5, len(tradeoffs_identified) * 1.0)
        + min(2.5, len(failure_modes_covered) * 1.25)
    )

    return {
        "factual_precision": factual_precision,
        "boundary_discrimination": boundary_discrimination,
        "tradeoffs_identified": tradeoffs_identified,
        "failure_modes_covered": failure_modes_covered,
        "score_out_of_10": round(raw_score, 1),
        "critique": (
            f"Identified {len(tradeoffs_identified)} trade-off dimension(s) and "
            f"{len(failure_modes_covered)} failure mode(s). "
            f"Boundary discrimination: {'PASS' if boundary_discrimination else 'FAIL'}."
        ),
    }


def rubric_to_evidence(rubric_output: Dict, factual_latency_ms: int) -> CompetencyEvidence:
    """Converts a rubric evaluation JSON object into a CompetencyEvidence instance."""
    return CompetencyEvidence(
        factual_latency_ms=factual_latency_ms,
        correct_boundary_identified=bool(
            rubric_output.get("factual_precision", True)
            and rubric_output.get("boundary_discrimination", False)
        ),
        tradeoffs_addressed=list(rubric_output.get("tradeoffs_identified", [])),
        failure_modes_mitigated=list(rubric_output.get("failure_modes_covered", [])),
    )
