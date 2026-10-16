# engine/suggest.py
import json
from pathlib import Path


def suggest_next_drills(data_dir="data", top_n=3):
    """Identify lowest-scoring loci and generate targeted SAA-C03 drill topics."""
    palace_file = Path(data_dir) / "palace_map.json"
    taxonomy_file = Path(data_dir) / "saa_taxonomy.json"

    with open(palace_file, "r", encoding="utf-8") as f:
        palace = json.load(f)

    taxonomy_traps = {}
    if taxonomy_file.exists():
        with open(taxonomy_file, "r", encoding="utf-8") as f:
            taxonomy = json.load(f)
        for domain in taxonomy.get("domains", []):
            for svc in domain.get("services", []):
                taxonomy_traps.setdefault(svc, []).extend(domain.get("key_traps", []))

    sorted_loci = sorted(
        palace.get("loci", []),
        key=lambda l: (l.get("stability_score", 0.0), l.get("last_reviewed", "")),
    )

    suggestions = []
    for locus in sorted_loci[:top_n]:
        traps = []
        for svc in locus.get("aws_services", []):
            for trap in taxonomy_traps.get(svc, []):
                if trap not in traps:
                    traps.append(trap)
        suggestions.append({
            "id": locus["id"],
            "name": locus["name"],
            "stability_score": locus["stability_score"],
            "last_reviewed": locus["last_reviewed"],
            "aws_services": locus["aws_services"],
            "networking_primitives": locus.get("networking_primitives", []),
            "exam_traps_to_drill": traps,
        })

    return suggestions


if __name__ == "__main__":
    drills = suggest_next_drills()
    print("=== NEXT RECOMMENDED LOCI DRILLS ===")
    for d in drills:
        print(
            f"[{d['name']}] (Stability: {d['stability_score']:.2f}, Last Reviewed: {d['last_reviewed']})"
        )
        print(f"  Services: {', '.join(d['aws_services'])}")
        print(f"  Primitives: {', '.join(d['networking_primitives'])}")
        for trap in d["exam_traps_to_drill"]:
            print(f"  * Trap: {trap}")
