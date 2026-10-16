# engine/db.py
# "The gun does not choose its target; the hand directs the lead."
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DB_PATH = Path("data/interactions.db")

COMPETENCY_COLUMNS = {
    "stage_before": "INTEGER",
    "stage_after": "INTEGER",
    "boundary_passed": "BOOLEAN",
    "tradeoffs_logged": "TEXT",
    "failure_modes_logged": "TEXT",
}


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
                passed BOOLEAN NOT NULL,
                stage_before INTEGER,
                stage_after INTEGER,
                boundary_passed BOOLEAN,
                tradeoffs_logged TEXT,
                failure_modes_logged TEXT
            );
        """)
        # Ensure existing tables are migrated with competency gate columns
        cursor = conn.execute("PRAGMA table_info(drill_interactions)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        for col_name, col_type in COMPETENCY_COLUMNS.items():
            if col_name not in existing_cols:
                conn.execute(
                    f"ALTER TABLE drill_interactions ADD COLUMN {col_name} {col_type};"
                )

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
    distractor: Optional[str] = None,
    stage_before: Optional[int] = None,
    stage_after: Optional[int] = None,
    boundary_passed: Optional[bool] = None,
    tradeoffs_logged: Optional[List[str]] = None,
    failure_modes_logged: Optional[List[str]] = None,
    db_path: Path = DB_PATH,
):
    init_db(db_path)
    tradeoffs_str = (
        json.dumps(tradeoffs_logged) if tradeoffs_logged is not None else None
    )
    failure_modes_str = (
        json.dumps(failure_modes_logged) if failure_modes_logged is not None else None
    )
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO drill_interactions (
                timestamp, locus_id, latency_ms, score, distractor_selected, passed,
                stage_before, stage_after, boundary_passed, tradeoffs_logged, failure_modes_logged
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                datetime.now(timezone.utc).isoformat(),
                locus_id,
                latency_ms,
                score,
                distractor,
                score >= 3,
                stage_before,
                stage_after,
                boundary_passed,
                tradeoffs_str,
                failure_modes_str,
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
