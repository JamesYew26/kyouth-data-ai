"""FastAPI backend: LLM chat + resume skill-gap analysis.

The business logic lives in ../../week_2 (prompt_model.py, find_skill_gaps.py). The
Dockerfile copies those modules next to this file, so there is one source of truth.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from find_skill_gaps import find_skill_gaps, format_report, read_resume
from prompt_model import LLMError, prompt_model

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("backend")

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "data/jobs_d1.db"))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost").split(",")
ALLOWED_SUFFIXES = {".pdf", ".txt"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

app = FastAPI(title="Skill Gap Chat Backend", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "database_found": DATABASE_PATH.exists()}


async def save_upload(file: UploadFile) -> Path:
    """Write the upload to a private temp file. Never trust the client's filename."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            415, f"Only {', '.join(sorted(ALLOWED_SUFFIXES))} files are supported"
        )
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File too large (max 5 MB)")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
    return Path(tmp.name)


@app.post("/chat")
async def chat(
    message: Annotated[str, Form()] = "",
    file: Annotated[UploadFile | None, File()] = None,
) -> dict:
    """Route by input:
    - file only        -> deterministic skill-gap report against the jobs database
    - file + message   -> LLM answers the message using the resume as context
    - message only     -> plain LLM chat
    """
    query = message.strip()
    if not query and not file:
        return {
            "reply": "Send a message, or upload a resume (.pdf/.txt) for a skill-gap report."
        }

    tmp_path = await save_upload(file) if file else None
    try:
        if tmp_path and not query:
            logger.info("Flow: skill-gap analysis")
            return {"reply": format_report(find_skill_gaps(tmp_path, DATABASE_PATH))}

        prompt = query
        if tmp_path:
            logger.info("Flow: chat with resume context")
            prompt = (
                f"Resume:\n---\n{read_resume(tmp_path)}\n---\n\nUser question: {query}"
            )
        else:
            logger.info("Flow: chat")
        return {"reply": prompt_model(None, prompt)}
    except LLMError as exc:
        logger.warning("LLM failure: %s", exc)
        raise HTTPException(502, f"The language model is unavailable: {exc}") from exc
    finally:
        if tmp_path:
            tmp_path.unlink(missing_ok=True)
