# Week 2 — AI Enrichment & Skill-Gap Analysis

Adds an LLM step on top of the week 1 warehouse:

1. **`tag_data.py`** reads untagged job descriptions from SQLite, asks an LLM to extract
   each job's tech stack, and writes it to `jobs.tech_stack`.
2. **`find_skill_gaps.py`** uses the LLM to extract a candidate's skills from a resume
   (`.txt` or `.pdf`), then deterministically ranks the skills the market asks for that
   the candidate lacks.
3. **`prompt_model.py`** is the single gateway to the model (Gemini in the cloud or a
   local Ollama model), plus shared helpers for retries and JSON parsing.

```text
jobs.db (description) ──▶ tag_data.py ──LLM──▶ jobs.tech_stack
                                                    │  SQL: count jobs per skill
resume.txt/.pdf ──LLM──▶ candidate skills ──────────┴─▶ demand − candidate = ranked gaps
```

## Run

```bash
cp .env.example .env        # or create .env with GEMINI_API_KEY=...  (LLM_MODEL optional)
uv sync
uv run tag_data.py --batch-size 5            # --model deepseek to use local Ollama
uv run find_skill_gaps.py --resume data/resume_d3.txt --top 10
uv run pytest                                # offline: the LLM is mocked
```

Example output:

```text
Top skill gaps across 7 job listings:
   1. aws — required by 5 job(s)
   2. google cloud — required by 4 job(s)
   3. mysql — required by 4 job(s)
```

## Design decisions

- **LLM only where it adds value.** The model turns free text into a skill list; the gap
  itself is plain set arithmetic and counting, so the report is reproducible and can't
  hallucinate a requirement that isn't in the data.
- **Incremental and resumable.** `tag_data.py` only selects rows where `tech_stack` is
  empty and commits after every batch, so a crash or rate limit just means "run it again".
- **Batching vs. reliability.** Several jobs per prompt cuts API calls (free-tier Gemini is
  ~5–10 requests/minute), but a bigger batch means a bad response loses more work. The
  default is 5 and it's a CLI flag.
- **Defensive parsing.** LLMs wrap JSON in ```` ``` ```` fences or `<think>` blocks;
  `parse_json_response` strips those, and ids the model invents are ignored.
- **Retries with exponential backoff** (2s, 4s) for transient LLM failures, shared by both
  scripts through `with_retry`.
- **Errors are exceptions, not `sys.exit`.** Library code raises `LLMError`, so the week 3
  API can return a clean 502 instead of the process dying.
- **Normalisation.** Skills are lower-cased and mapped through a synonym table
  (`postgres → postgresql`, `k8s → kubernetes`) before comparison.

## Limitations / next steps

- Synonym matching is a hand-written table; embeddings or a curated skill taxonomy
  would generalise better.
- Store `tech_stack` in a normalised `job_skills(source_id, skill)` table instead of a
  comma-separated string, so demand is a simple `GROUP BY`.
- Use the model's structured-output / JSON-schema mode to remove most parsing failures.
- Track which model and prompt version tagged each row, so re-tagging is auditable.
