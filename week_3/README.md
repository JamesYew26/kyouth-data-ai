# Week 3 — Containerised Chat & Resume Analysis App

A two-service web app on top of the week 2 logic:

- **frontend** (FastAPI + Jinja, port 80): a single chat page with resume upload.
- **backend** (FastAPI, port 8001): `POST /chat` and `GET /health`. It imports
  `prompt_model.py` and `find_skill_gaps.py` directly from `../week_2` (the Dockerfile
  copies them in), so there is one copy of the business logic.

| You send | Backend does | Reply |
|---|---|---|
| text only | LLM chat | model's answer |
| resume only (.pdf/.txt) | skill-gap analysis against `jobs_d1.db` | ranked list of missing skills |
| text + resume | LLM answers your question with the resume as context | model's answer |

## Run with Docker

```bash
cp .env.example .env     # add GEMINI_API_KEY
docker compose up --build
# open http://localhost      backend health: http://localhost:8001/health
docker compose down
```

The backend mounts `../week_2/data` read-only at `/app/data`, so the tagged database must
exist there first (run week 2's `tag_data.py`).

## Run without Docker

```bash
cd backend && uv sync
PYTHONPATH=src:../../week_2 uv run uvicorn app:app --port 8001
uv run pytest            # API tests, LLM mocked
```

## Design decisions

- **One source of truth.** The backend is built with the repo root as Docker context and
  copies the week 2 modules in, instead of keeping a copy-pasted duplicate that drifts.
- **Safe uploads.** Files go to a `tempfile` with a server-chosen name (the client's
  filename is never used as a path), only `.pdf`/`.txt` are accepted, there's a 5 MB cap,
  and the temp file is always deleted in `finally`.
- **Failure handling.** LLM outages become HTTP 502 with a readable message; the UI shows
  it instead of a generic "could not reach server".
- **Container hygiene.** Slim base image, dependencies installed in their own cached
  layer, non-root user, a healthcheck the frontend waits on, and a root `.dockerignore`
  allow-list so `.env` and raw data never enter the build context.
- **Config by environment.** `BACKEND_URL`, `LLM_MODEL`, `DATABASE_PATH`,
  `ALLOWED_ORIGINS` are env vars; CORS is limited to the frontend origin.

## Limitations

- No authentication or rate limiting — local/demo use only.
- Stateless: chat history lives only in the browser tab.
- The browser calls the backend directly; in production you'd put both behind one
  reverse proxy (nginx) so there's a single origin and no CORS.
