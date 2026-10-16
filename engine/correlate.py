# engine/correlate.py
import json


def calculate_priority_score(
    competency_stage: int, heat_score: int, stability: float
) -> float:
    """
    Priority Score = (5 - competency_stage) * 2.0 + (heat_score * 1.5) - (stability * 1.0)
    Higher score means higher urgency in the daily drill queue.
    """
    return round(
        (5 - int(competency_stage)) * 2.0
        + (float(heat_score) * 1.5)
        - (float(stability) * 1.0),
        2,
    )


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
        competency_stage = locus.get("competency_stage", 1)
        priority_score = calculate_priority_score(
            competency_stage=competency_stage,
            heat_score=heat_score,
            stability=stability,
        )

        status = "HEALTHY"
        if heat_score > 3 and stability < 0.8:
            status = "CRITICAL DEFICIT (Hot in Exam, Low Locus Stability)"
        elif heat_score > 3:
            status = "HIGH PRIORITY RECALL"

        results.append({
            "id": locus["id"],
            "name": locus_name,
            "status": status,
            "competency_stage": competency_stage,
            "heat_score": heat_score,
            "stability": stability,
            "priority_score": priority_score,
            "services": assigned,
        })

    results.sort(key=lambda r: r["priority_score"], reverse=True)

    for r in results:
        print(
            f"[{r['status']}] {r['name']} (Priority Score: {r['priority_score']:.2f})"
        )
        print(
            f"  Stage: {r['competency_stage']} | Heat Score: {r['heat_score']} "
            f"| Stability: {r['stability']:.2f} | Services: {r['services']}\n"
        )

    return results


if __name__ == "__main__":
    correlate_palace_with_trends()
