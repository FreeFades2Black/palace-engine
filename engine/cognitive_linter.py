# engine/cognitive_linter.py
# "The mind that shoots true forgets not the sound of the horn."
import json
import sys
from pathlib import Path

# Sensory & kinetic triggers required for durable loci pegs
KINETIC_VERBS = [
    "smash",
    "explode",
    "burn",
    "freeze",
    "lock",
    "spray",
    "crush",
    "slice",
    "flood",
    "shock",
    "spin",
    "screaming",
    "blaring",
    "slam",
    "vaporize",
    "deflect",
]

# Major System consonant phonetic mapping: 0=s/z, 1=t/d, 2=n, 3=m, 4=r, 5=l, 6=j/ch/sh, 7=k/g, 8=f/v, 9=p/b
MAJOR_SYSTEM_EXAMPLES = {
    "15": ["hotel", "tall", "towel"],  # 1=t/d, 5=l (Lambda 15 min)
    "5": ["oil", "owl", "law"],        # 5=l (S3 5 TB max object)
    "14": ["door", "tire", "otter"],   # 1=t/d, 4=r (SQS 14 day retention)
}


def audit_loci_quality(palace_path="data/palace_map.json"):
    with open(Path(palace_path), "r", encoding="utf-8") as f:
        palace = json.load(f)

    issues = []
    print("=== [COGNITIVE AUDIT] Evaluating Memory Encoding Quality ===")

    for locus in palace.get("loci", []):
        name = locus.get("name")
        anchor_scene = locus.get("scene_narrative", "")

        # Check 1: Kinetic / Emotional Salience (Von Restorff check)
        has_kinetic = any(v in anchor_scene.lower() for v in KINETIC_VERBS)
        if not has_kinetic:
            issues.append({
                "locus": name,
                "type": "LOW_SALIENCE",
                "message": "Scene is too passive. Needs active physical conflict, kinetic impact, or sensory contrast.",
            })

        # Check 2: Technical Limits & Major System Anchoring
        limits = locus.get("encoded_limits", [])
        for limit in limits:
            if not limit.get("major_system_peg"):
                issues.append({
                    "locus": name,
                    "type": "MISSING_MAJOR_PEG",
                    "message": f"Service limit '{limit.get('metric')}' missing Major System phonetic peg.",
                })

    return issues


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    audit_results = audit_loci_quality()
    if not audit_results:
        print("[✓] All palace loci meet high-retention cognitive benchmarks.")
    else:
        for err in audit_results:
            print(f"[-] [{err['type']}] {err['locus']}: {err['message']}")
        sys.exit(1)
