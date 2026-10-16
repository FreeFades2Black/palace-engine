# engine/scraper.py
import json
import re
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

USER_AGENT = "omarchy:palace-engine-scraper:v1.0 (by /u/FreeFades2Black)"

# Core AWS services and high-frequency exam discriminators
TRACKED_SERVICES = {
    "Route 53": ["route 53", "route53", "dns", "latency routing", "failover routing"],
    "Global Accelerator": ["global accelerator", "anycast", "static ip"],
    "GuardDuty": ["guardduty", "threat detection", "malicious"],
    "WAF & Shield": ["waf", "shield", "ddos", "layer 7", "sql injection"],
    "Organizations & SCP": ["scp", "organizations", "service control policy"],
    "Aurora": ["aurora", "aurora serverless", "blue green", "read replica"],
    "Storage Disambiguation": ["efs", "ebs", "fsx", "datasync", "storage gateway"],
    "Integration Decoupling": ["sqs", "sns", "eventbridge", "step functions", "fanout"],
    "IAM Identity Center": ["identity center", "aws sso", "permission sets"],
    "Data Analytics": ["athena", "glue", "redshift spectrum", "quicksight", "zero-etl"],
}


def fetch_reddit_exam_intel(subreddit="AWSCertifications", limit=25):
    """Pulls recent passing debriefs from Reddit using public JSON endpoints."""
    url = (
        f"https://www.reddit.com/r/{subreddit}/search.json"
        f"?q=passed+SAA-C03&restrict_sr=1&sort=new&limit={limit}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    extracted_posts = []
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for child in data.get("data", {}).get("children", []):
                pdata = child.get("data", {})
                title = pdata.get("title", "")
                selftext = pdata.get("selftext", "")
                created_utc = pdata.get("created_utc", 0)
                extracted_posts.append({
                    "title": title,
                    "content": selftext,
                    "created_utc": created_utc,
                    "url": f"https://reddit.com{pdata.get('permalink', '')}",
                })
    except Exception as e:
        print(f"[!] Warning: Failed fetching Reddit data: {e}")

    return extracted_posts


def analyze_trends(posts):
    """Scores service frequency and extracts common test-day friction points."""
    service_hits = Counter()
    extracted_notes = []

    for post in posts:
        full_text = (post["title"] + " " + post["content"]).lower()
        matched_any = False

        for service, aliases in TRACKED_SERVICES.items():
            if any(alias in full_text for alias in aliases):
                service_hits[service] += 1
                matched_any = True

        if matched_any:
            # Grab snippets mentioning 'exam', 'saw', 'questions', or 'tricky'
            sentences = re.split(r"\. |\n", post["content"])
            for s in sentences:
                s_lower = s.lower()
                if any(
                    w in s_lower
                    for w in ["tricky", "heavy on", "focus on", "lots of", "make sure you know"]
                ):
                    if 30 < len(s.strip()) < 200:
                        extracted_notes.append(s.strip())

    return service_hits, extracted_notes[:10]


def update_palace_intel(output_file="data/exam_trends.json"):
    print("[*] Harvesting recent SAA-C03 candidate debriefs...")
    out_path = Path(output_file)
    posts = fetch_reddit_exam_intel()

    if not posts and out_path.exists():
        print("[*] Using cached exam_trends.json (live endpoint unreachable or rate-limited).")
        with open(out_path, "r", encoding="utf-8") as f:
            return json.load(f)

    service_hits, key_notes = analyze_trends(posts)

    trends_payload = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_posts_analyzed": len(posts),
        "service_frequency_rankings": dict(service_hits.most_common()),
        "curated_test_takeaways": key_notes,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(trends_payload, f, indent=2)
        f.write("\n")

    print(f"[✓] Successfully dumped latest exam trends to {output_file}")
    return trends_payload


if __name__ == "__main__":
    data = update_palace_intel()
    print("\n--- TOP EXAM TOPICS SPOTTED IN RECENT PASSES ---")
    for svc, count in list(data["service_frequency_rankings"].items())[:5]:
        print(f"• {svc}: mentioned {count} times")
