# engine/db.py
# "The gun does not choose its target; the hand directs the lead."
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("data/interactions.db")


def init_db(db_path: Path = DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS drill_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                locus_id TEXT NOT NULL,
                latency_ms INTEGER NOT NULL,
                score INTEGER NOT NULL,
                distractor_selected TEXT,
                passed BOOLEAN NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_exam_scores (
                date TEXT PRIMARY KEY,
                exam_type TEXT NOT NULL,
                score_percent REAL NOT NULL,
                weakest_domain TEXT NOT NULL
            );
        """)
        conn.commit()


def record_interaction(
    locus_id: str,
    latency_ms: int,
    score: int,
    distractor: str = None,
    db_path: Path = DB_PATH,
):
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO drill_interactions (timestamp, locus_id, latency_ms, score, distractor_selected, passed)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                datetime.now(timezone.utc).isoformat(),
                locus_id,
                latency_ms,
                score,
                distractor,
                score >= 3,
            ),
        )
        conn.commit()


def get_telemetry_metrics(db_path: Path = DB_PATH):
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("""
            SELECT COUNT(*), AVG(latency_ms), AVG(score), SUM(CASE WHEN passed THEN 1 ELSE 0 END)
            FROM drill_interactions
        """)
        total, avg_latency, avg_score, passed_count = cursor.fetchone()
    total = total or 0
    return {
        "total_drills": total,
        "avg_latency_ms": round(avg_latency or 0.0, 1),
        "avg_score": round(avg_score or 0.0, 2),
        "pass_rate": round((passed_count / total) * 100.0, 1) if total > 0 else 0.0,
    }
