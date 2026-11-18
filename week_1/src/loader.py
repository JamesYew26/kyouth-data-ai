"""Gold layer: load silver JSON records into the SQLite warehouse (3_gold/jobs.db)."""

import json
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    source_id   TEXT PRIMARY KEY,   -- natural key from the job URL; makes loads idempotent
    job_title   TEXT NOT NULL,
    company     TEXT NOT NULL,
    description TEXT NOT NULL,
    tech_stack  TEXT,               -- filled in later by week_2/tag_data.py
    loaded_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

INSERT = """
INSERT OR IGNORE INTO jobs (source_id, job_title, company, description)
VALUES (:source_id, :job_title, :company, :description)
"""


def load_all_jsons(input_dir: Path, db_path: Path) -> dict[str, int]:
    """Insert every silver record into the jobs table. Re-running is safe (idempotent)."""
    input_dir, db_path = Path(input_dir), Path(db_path)
    stats = {"total": 0, "inserted": 0, "skipped": 0, "failed": 0}

    if not input_dir.is_dir():
        logger.error("Input directory %s does not exist", input_dir)
        return stats

    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:  # commits on success, rolls back on error
        conn.execute(SCHEMA)
        for json_file in sorted(input_dir.glob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                stats["failed"] += 1
                logger.warning("Unreadable %s: %s", json_file.name, exc)
                continue

            for record in data if isinstance(data, list) else [data]:
                stats["total"] += 1
                try:
                    cur = conn.execute(INSERT, record)
                except (sqlite3.Error, KeyError) as exc:
                    stats["failed"] += 1
                    logger.warning("Bad record in %s: %s", json_file.name, exc)
                    continue
                stats["inserted" if cur.rowcount else "skipped"] += 1
    conn.close()

    logger.info(
        "Gold summary: total=%(total)d inserted=%(inserted)d "
        "skipped(duplicate)=%(skipped)d failed=%(failed)d",
        stats,
    )
    return stats
