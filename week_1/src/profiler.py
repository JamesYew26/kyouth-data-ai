"""Data-quality profile of the gold jobs table."""

import sqlite3
from pathlib import Path

PROFILE_SQL = """
SELECT
    COUNT(*)                                                  AS total,
    COUNT(DISTINCT source_id)                                 AS distinct_ids,
    SUM(job_title   IS NULL OR TRIM(job_title)   = '')        AS missing_title,
    SUM(company     IS NULL OR TRIM(company)     = '')        AS missing_company,
    SUM(description IS NULL OR TRIM(description) = '')        AS missing_description,
    SUM(tech_stack  IS NULL OR TRIM(tech_stack)  = '')        AS untagged,
    CAST(AVG(LENGTH(description)) AS INTEGER)                 AS avg_desc_len,
    MIN(LENGTH(description))                                  AS min_desc_len,
    MAX(LENGTH(description))                                  AS max_desc_len
FROM jobs
"""


def run_data_profile(db_path: Path) -> dict | None:
    """Print and return a data-quality report for the jobs table."""
    db_path = Path(db_path)
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return None

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        report = dict(conn.execute(PROFILE_SQL).fetchone())
        top_companies = conn.execute(
            "SELECT company, COUNT(*) AS n FROM jobs GROUP BY company "
            "ORDER BY n DESC, company LIMIT 5"
        ).fetchall()
    conn.close()

    if not report["total"]:
        print("jobs table is empty")
        return report

    print("--- DATA QUALITY REPORT ---")
    print(f"Rows: {report['total']}  (distinct source_id: {report['distinct_ids']})")
    print(
        f"Missing -> title: {report['missing_title']}, company: {report['missing_company']}, "
        f"description: {report['missing_description']}, tech_stack: {report['untagged']}"
    )
    print(
        f"Description length -> avg {report['avg_desc_len']}, "
        f"min {report['min_desc_len']}, max {report['max_desc_len']}"
    )
    print(
        "Top companies: "
        + ", ".join(f"{r['company']} ({r['n']})" for r in top_companies)
    )
    return report
