# engine/correlate.py
import json
from pathlib import Path


def correlate_palace_with_trends(
    palace_path="data/palace_map.json", trends_path="data/exam_trends.json"
):
    with open(palace_path, "r", encoding="utf-8") as f:
        palace = json.load(f)
    with open(trends_path, "r", encoding="utf-8") as f:
        trends = json.load(f)

    print("=== PALACE INTEL RADAR: HIGH FREQUENCY TEST TOPICS ===")
    loci = palace.get("loci", [])
    rankings = trends.get("service_frequency_rankings", {})
    results = []

    for locus in loci:
        locus_name = locus["name"]
        assigned = locus.get("aws_services", [])

        # Check if any assigned service is currently hot in exam debriefs
        heat_score = sum(rankings.get(svc, 0) for svc in assigned)
        stability = locus.get("stability_score", 0.5)

        status = "HEALTHY"
        if heat_score > 3 and stability < 0.8:
            status = "CRITICAL DEFICIT (Hot in Exam, Low Locus Stability)"
        elif heat_score > 3:
            status = "HIGH PRIORITY RECALL"

        results.append({
            "id": locus["id"],
            "name": locus_name,
            "status": status,
            "heat_score": heat_score,
            "stability": stability,
            "services": assigned,
        })

        print(f"[{status}] {locus_name}")
        print(f"  Services: {assigned} | Heat Score: {heat_score} | Stability: {stability:.2f}\n")

    return results


if __name__ == "__main__":
    correlate_palace_with_trends()
