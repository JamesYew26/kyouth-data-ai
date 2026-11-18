# Job Market Skill-Gap Platform

An end-to-end data project built over three weeks: scrape-free ingestion of JobStreet job
listings into a medallion-style warehouse, LLM enrichment of each listing with its tech
stack, and a containerised web app that tells a candidate which in-demand skills their
resume is missing.

```text
 week_1: batch ETL (medallion)              week_2: AI enrichment            week_3: serving
 ─────────────────────────────              ─────────────────────            ───────────────
 0_source  MHTML snapshots (100)
    │ ingestor.py   decode MIME
 1_bronze  raw HTML (100)
    │ processor.py  BeautifulSoup + Pydantic contract
 2_silver  validated JSON (84, 16 rejected)
    │ loader.py     INSERT OR IGNORE (idempotent)
 3_gold    SQLite jobs table ──────────────▶ tag_data.py ──▶ jobs.tech_stack
                                             (LLM, incremental,         │
                                              batched, retried)         ▼
                                                              find_skill_gaps.py ◀── resume
                                                              (LLM extracts resume skills,
                                                               SQL/Python ranks gaps)
                                                                        │
                                                       FastAPI backend ◀┘ ◀── chat UI (frontend)
                                                       (Docker Compose)
```

| Folder | What it is | Key tech |
|---|---|---|
| [`week_1/`](week_1/README.md) | Bronze → Silver → Gold batch pipeline + data-quality profiler | Python, BeautifulSoup, Pydantic, SQLite |
| [`week_2/`](week_2/README.md) | LLM tagging of job tech stacks; resume skill-gap analysis | Gemini / Ollama, retries, prompt → JSON |
| [`week_3/`](week_3/README.md) | Chat + resume-upload web app over the week_2 logic | FastAPI, Docker Compose |

## Quick start

```bash
# week 1: build the warehouse
cd week_1 && uv sync && uv run main.py all

# week 2: tag jobs and analyse a resume (needs GEMINI_API_KEY in week_2/.env)
cd week_2 && uv sync && uv run tag_data.py && uv run find_skill_gaps.py

# week 3: run the app at http://localhost
cd week_3 && cp .env.example .env && docker compose up --build
```

## Tests

Every module has offline unit tests (the LLM is mocked):

```bash
cd week_1 && uv run pytest          # parsing, data contract, idempotent load
cd week_2 && uv run pytest          # JSON parsing of LLM output, retries, gap ranking
cd week_3/backend && uv run pytest  # API routing, upload safety, LLM failure → 502
```

Raw data (`data/` folders) and secrets (`.env`) are git-ignored.
