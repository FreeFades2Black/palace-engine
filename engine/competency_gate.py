# engine/competency_gate.py
# "The gun does not make the gunslinger; the judgment directs the shot."

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

STAGE_LABELS = {
    1: "Stage 1: Mnemonic Retrieval",
    2: "Stage 2: Boundary Disambiguation",
    3: "Stage 3: Trade-Off Synthesis",
    4: "Stage 4: Production Instinct",
}


@dataclass
class CompetencyEvidence:
    factual_latency_ms: int
    correct_boundary_identified: bool
    tradeoffs_addressed: List[str] = field(default_factory=list)  # e.g., ["cost", "operational_overhead", "latency"]
    failure_modes_mitigated: List[str] = field(default_factory=list)  # e.g., ["poison_pill", "duplicate_execution"]


class CompetencyGate:
    def __init__(self, locus_id: str, current_stage: int):
        self.locus_id = locus_id
        self.current_stage = current_stage

    def evaluate_promotion(self, evidence: CompetencyEvidence) -> Dict:
        """
        Determines promotion, retention, or demotion strictly based on evidence.
        """
        if self.current_stage == 1:
            # Gate 1 -> 2: Must demonstrate sub-2.2-second recall with zero errors
            if evidence.factual_latency_ms <= 2200 and evidence.correct_boundary_identified:
                return {
                    "new_stage": 2,
                    "action": "PROMOTE",
                    "reason": "Hard constraints verified under latency threshold. Mnemonic active scene fading initiated.",
                }
            return {
                "new_stage": 1,
                "action": "RETAIN",
                "reason": "Recall latency or accuracy unproven.",
            }

        elif self.current_stage == 2:
            # Gate 2 -> 3: Must successfully reject distractors and state boundary lines
            if evidence.correct_boundary_identified and len(evidence.tradeoffs_addressed) >= 2:
                return {
                    "new_stage": 3,
                    "action": "PROMOTE",
                    "reason": "Boundary line verified against distractor services. Locus moved to full architectural synthesis.",
                }
            elif not evidence.correct_boundary_identified:
                return {
                    "new_stage": 1,
                    "action": "DEMOTE",
                    "reason": "Boundary failure detected. Snapping back to Stage 1 mnemonic anchoring for reinforcement.",
                }
            return {
                "new_stage": 2,
                "action": "RETAIN",
                "reason": "Boundary clear, but trade-off justification lacks depth.",
            }

        elif self.current_stage == 3:
            if not evidence.correct_boundary_identified:
                return {
                    "new_stage": 1,
                    "action": "DEMOTE",
                    "reason": "Boundary failure detected. Snapping back to Stage 1 mnemonic anchoring for reinforcement.",
                }
            # Gate 3 -> 4: Must anticipate failure modes and optimize cost/resilience
            has_resilience = len(evidence.failure_modes_mitigated) >= 1
            has_tradeoffs = len(evidence.tradeoffs_addressed) >= 3

            if has_resilience and has_tradeoffs:
                return {
                    "new_stage": 4,
                    "action": "PROMOTE_TO_MASTERY",
                    "reason": "Production intuition verified. Complete retirement of mnemonic scaffolding.",
                }
            return {
                "new_stage": 3,
                "action": "RETAIN",
                "reason": "Demonstrates trade-offs but misses edge-case failure modes.",
            }

        if not evidence.correct_boundary_identified:
            return {
                "new_stage": 1,
                "action": "DEMOTE",
                "reason": "Regression on boundary test in Stage 4. Snapping back to Stage 1 mnemonic anchoring.",
            }
        return {
            "new_stage": 4,
            "action": "MAINTAIN",
            "reason": "Stage 4 Production Mastery active.",
        }


def apply_competency_transition(
    locus_id: str,
    evidence: CompetencyEvidence,
    palace_path: str = "data/palace_map.json",
) -> Dict:
    """Evaluates evidence for a locus and persists stage transitions to palace_map.json."""
    path = Path(palace_path)
    with open(path, "r", encoding="utf-8") as f:
        palace = json.load(f)

    result = None
    for locus in palace.get("loci", []):
        if locus["id"] == locus_id:
            stage_before = int(locus.get("competency_stage", 1))
            gate = CompetencyGate(locus_id=locus_id, current_stage=stage_before)
            outcome = gate.evaluate_promotion(evidence)
            stage_after = outcome["new_stage"]
            locus["competency_stage"] = stage_after
            locus["scaffolding_retired"] = stage_after == 4
            if stage_after > stage_before:
                verified = locus.setdefault("verified_competencies", [])
                gate_tag = f"Gate {stage_before}->{stage_after}: {STAGE_LABELS.get(stage_after)}"
                if gate_tag not in verified:
                    verified.append(gate_tag)
            result = {
                "locus_id": locus_id,
                "stage_before": stage_before,
                "stage_after": stage_after,
                "stage_label": STAGE_LABELS.get(stage_after, f"Stage {stage_after}"),
                **outcome,
            }
            break

    if result is None:
        raise ValueError(f"Locus '{locus_id}' not found in {palace_path}")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(palace, f, indent=2)
        f.write("\n")

    return result


if __name__ == "__main__":
    with open("data/palace_map.json", "r", encoding="utf-8") as f:
        palace_data = json.load(f)
    print("=== EVIDENTIARY COMPETENCY GATE STATUS ===")
    for loc in palace_data.get("loci", []):
        stg = loc.get("competency_stage", 1)
        print(
            f"[{STAGE_LABELS.get(stg, stg)}] {loc['name']} "
            f"(Stability: {loc.get('stability_score', 0.0):.2f})"
        )
