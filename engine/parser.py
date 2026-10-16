# engine/parser.py
import json
from pathlib import Path
import frontmatter


def load_palace_map(data_dir="data"):
    """Load and validate the palace_map.json schema."""
    palace_file = Path(data_dir) / "palace_map.json"
    with open(palace_file, "r", encoding="utf-8") as f:
        palace = json.load(f)
    if "loci" not in palace or not isinstance(palace["loci"], list):
        raise ValueError("Invalid palace_map.json: missing 'loci' list")
    return palace


def load_taxonomy(data_dir="data"):
    """Load the SAA-C03 taxonomy definitions."""
    taxonomy_file = Path(data_dir) / "saa_taxonomy.json"
    with open(taxonomy_file, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_recall_logs(data_dir="data"):
    """Parse all markdown session logs with YAML frontmatter in data/recall_history."""
    sessions = []
    log_files = sorted(Path(data_dir, "recall_history").glob("*.md"))
    for log_path in log_files:
        post = frontmatter.load(log_path)
        session_date = post.get("date")
        sessions.append({
            "file": log_path.name,
            "date": str(session_date) if session_date else None,
            "loci_reviewed": post.get("loci_reviewed", []),
            "notes": post.content.strip(),
        })
    return sessions
