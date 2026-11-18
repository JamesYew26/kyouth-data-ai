# Week 1 — JobStreet Medallion Pipeline

Batch ETL that turns saved JobStreet job pages (MHTML snapshots) into a clean SQLite
table, using a **medallion architecture** so every stage is re-runnable from the one
before it.

| Layer | Folder | Produced by | Contents |
|---|---|---|---|
| Source | `data/0_source/` | you (browser "Save as MHTML") | 100 raw `.mhtml` snapshots |
| Bronze | `data/1_bronze/` | `src/ingestor.py` | decoded HTML, untouched |
| Silver | `data/2_silver/` | `src/processor.py` | one validated JSON record per job |
| Gold | `data/3_gold/jobs.db` | `src/loader.py` | `jobs` table (primary key `source_id`) |
| QA | — | `src/profiler.py` | row counts, nulls, length stats, top companies |

Latest run: **100 → 100 bronze → 84 silver (16 rejected: 8 no title, 5 no description,
3 no company) → 84 gold rows**, and re-running inserts 0 duplicates.

## Run

```bash
uv sync
uv run main.py all          # or: ingest | process | load | profile
uv run main.py all -v       # per-file debug logging
uv run pytest               # offline unit + end-to-end tests
```

## Design decisions

- **Keep bronze raw.** If we later want a new field (e.g. salary), we re-parse bronze
  instead of re-scraping pages that may no longer exist.
- **Data contract at the silver boundary.** `JobListing` (Pydantic) rejects records with
  a missing title/company or a description under 10 chars. Bad pages are logged and
  skipped ("fail early, per record") so one broken page never stops the batch and never
  pollutes gold with NULLs.
- **Idempotent load.** `source_id` (from the job URL) is the primary key and the loader
  uses `INSERT OR IGNORE`, so the pipeline can be re-run safely after a crash.
- **Pure parsing function.** `parse_job_html(html) -> JobListing` has no I/O, which is
  what makes it easy to unit-test.
- **Paths resolved from `main.py`**, not the working directory, so the CLI behaves the
  same wherever it is launched.

## What I'd change at scale

- Store silver as Parquet and gold in a warehouse (Postgres/BigQuery/Snowflake), and let
  SQL do more of the transformation (ELT, e.g. with dbt).
- Orchestrate with Airflow/Dagster: one task per stage, retries, scheduling, backfills.
- Process files in parallel (multiprocessing, or Spark for very large volumes).
- Use an upsert (`ON CONFLICT DO UPDATE`) plus a `scraped_at` column to track job
  postings that change over time (SCD type 2).
- Quarantine rejected records in a `rejects/` folder with the reason, and alert when the
  rejection rate crosses a threshold.
