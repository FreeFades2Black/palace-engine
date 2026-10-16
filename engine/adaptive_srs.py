# engine/adaptive_srs.py
# "Ka is a wheel; its one purpose is to turn."
import json
import sys
from datetime import datetime, timedelta, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def calculate_sm2(repetition: int, ease_factor: float, interval: int, quality: int):
    """
    quality scale:
    5 - Instant recall (< 10s)
    4 - Correct after brief hesitation
    3 - Correct with serious effort
    2 - Incorrect, but recognized the right answer upon review
    1 - Incorrect, total memory palace blackout
    0 - Complete confusion / misconception
    """
    if quality >= 3:
        if repetition == 0:
            new_interval = 1
        elif repetition == 1:
            new_interval = 6
        else:
            new_interval = int(round(interval * ease_factor))
        new_repetition = repetition + 1
    else:
        new_interval = 1
        new_repetition = 0

    # SM-2 EF update formula
    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, round(new_ef, 3))

    return new_repetition, new_ef, new_interval


def process_daily_test_results(
    test_results_path="data/daily_test.json", palace_path="data/palace_map.json"
):
    with open(test_results_path, "r", encoding="utf-8") as f:
        test_session = json.load(f)
    with open(palace_path, "r", encoding="utf-8") as f:
        palace = json.load(f)

    loci_dict = {l["id"]: l for l in palace["loci"]}
    now = datetime.now(timezone.utc)

    for record in test_session.get("questions_evaluated", []):
        locus_id = record.get("locus_id")
        quality = record.get("score")  # 0 to 5

        if locus_id in loci_dict:
            target = loci_dict[locus_id]
            rep = target.get("repetitions", 0)
            ef = target.get("ease_factor", 2.5)
            interval = target.get("interval_days", 1)

            new_rep, new_ef, new_interval = calculate_sm2(rep, ef, interval, quality)

            target["repetitions"] = new_rep
            target["ease_factor"] = new_ef
            target["interval_days"] = new_interval
            target["next_due"] = (now + timedelta(days=new_interval)).strftime("%Y-%m-%d")
            target["last_tested_score"] = quality

            # Record cross-concept confusion if missed
            if quality < 3 and "distractor_service" in record:
                confusion = target.setdefault("confusion_pairs", [])
                if record["distractor_service"] not in confusion:
                    confusion.append(record["distractor_service"])

    with open(palace_path, "w", encoding="utf-8") as f:
        json.dump(palace, f, indent=2)
        f.write("\n")

    print("[✓] Memory palace updated with performance-calibrated retention intervals.")
    return palace


if __name__ == "__main__":
    process_daily_test_results()
