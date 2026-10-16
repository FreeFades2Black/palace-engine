# engine/scoring.py
import json
import frontmatter
from pathlib import Path
from datetime import datetime, timezone


def evaluate_gaps(data_dir="data"):
    palace_file = Path(data_dir) / "palace_map.json"
    with open(palace_file, "r", encoding="utf-8") as f:
        palace = json.load(f)

    loci_map = {l["id"]: l for l in palace["loci"]}
    identified_gaps = []

    # Parse all markdown sessions
    log_files = sorted(Path(data_dir, "recall_history").glob("*.md"))
    for log_path in log_files:
        post = frontmatter.load(log_path)
        reviews = post.get("loci_reviewed", [])
        raw_date = post.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        session_date = str(raw_date)

        for review in reviews:
            lid = review.get("id")
            score = review.get("recall_accuracy", 3)
            gaps = review.get("gaps_identified", [])

            if lid in loci_map:
                # Basic stability adjustment (SM-2 style)
                current_score = loci_map[lid]["stability_score"]
                weight = (score - 3) * 0.1
                loci_map[lid]["stability_score"] = round(
                    max(0.1, min(1.0, current_score + weight)), 2
                )
                loci_map[lid]["last_reviewed"] = session_date

                if gaps or score <= 3:
                    identified_gaps.append({
                        "locus": loci_map[lid]["name"],
                        "services": loci_map[lid]["aws_services"],
                        "weaknesses": gaps,
                        "score": score,
                    })

    # Save updated palace state
    with open(palace_file, "w", encoding="utf-8") as f:
        json.dump(palace, f, indent=2)
        f.write("\n")

    return identified_gaps, loci_map


if __name__ == "__main__":
    gaps, updated_loci = evaluate_gaps()
    print("=== SAA-C03 KNOWLEDGE GAPS IDENTIFIED ===")
    for g in gaps:
        print(f"[{g['locus']}] Score: {g['score']}/5 | Services: {', '.join(g['services'])}")
        for w in g["weaknesses"]:
            print(f"  - {w}")
