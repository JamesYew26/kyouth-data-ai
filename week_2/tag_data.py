"""Use an LLM to extract a tech stack from each job description and store it in jobs.tech_stack.

Incremental by design: only rows where tech_stack is NULL/empty are sent to the model,
so a crashed or rate-limited run can simply be restarted and resumes where it stopped.

    uv run tag_data.py [--db data/jobs_d1.db] [--model gemini] [--batch-size 5]
"""

import argparse
import json
import sqlite3
from pathlib import Path

from prompt_model import LLMError, parse_json_response, prompt_model, with_retry

DEFAULT_DB = Path(__file__).parent / "data" / "jobs_d1.db"

PROMPT = """You are a technical data extractor. For each job below, extract the technical
stack (programming languages, frameworks, databases, cloud services, APIs and tools).

Return ONLY a JSON object whose keys are the exact source_id values given and whose
values are comma-separated tech stack strings. No markdown, no explanation.

Jobs:
{jobs}"""


def build_prompt(batch: list[tuple[str, str]]) -> str:
    jobs = [{"source_id": sid, "description": desc} for sid, desc in batch]
    return PROMPT.format(jobs=json.dumps(jobs, ensure_ascii=False))


def extract_tech_stacks(
    batch: list[tuple[str, str]], model: str | None
) -> dict[str, str]:
    """Ask the model for a {source_id: "a, b, c"} mapping; keep only ids we actually sent."""
    parsed = parse_json_response(prompt_model(model, build_prompt(batch)))
    if not isinstance(parsed, dict):
        raise LLMError("expected a JSON object keyed by source_id")
    wanted = {sid for sid, _ in batch}
    return {
        str(sid): str(stack).strip()
        for sid, stack in parsed.items()
        if str(sid) in wanted and str(stack).strip()
    }


def tag_data(
    db_path: Path = DEFAULT_DB, model: str | None = None, batch_size: int = 5
) -> dict:
    stats = {"pending": 0, "tagged": 0, "failed_batches": 0}
    with sqlite3.connect(db_path, timeout=30) as conn:
        pending = conn.execute(
            "SELECT source_id, description FROM jobs "
            "WHERE tech_stack IS NULL OR TRIM(tech_stack) = ''"
        ).fetchall()
        stats["pending"] = len(pending)

        for start in range(0, len(pending), batch_size):
            batch = [
                (str(sid), desc) for sid, desc in pending[start : start + batch_size]
            ]
            try:
                stacks = with_retry(
                    lambda batch=batch: extract_tech_stacks(batch, model),
                    retry_on=(LLMError,),
                )
            except LLMError as exc:
                stats["failed_batches"] += 1
                print(f"Batch starting at row {start} failed, skipping: {exc}")
                continue

            conn.executemany(
                "UPDATE jobs SET tech_stack = ? WHERE source_id = ?",
                [(stack, sid) for sid, stack in stacks.items()],
            )
            conn.commit()  # commit per batch: progress survives a later crash
            stats["tagged"] += len(stacks)
            for sid, stack in stacks.items():
                print(f"Tagged [{sid}]: {stack}")
    conn.close()

    print(f"Summary: {stats}")
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument(
        "--model", default=None, help="defaults to $LLM_MODEL or 'gemini'"
    )
    parser.add_argument("--batch-size", type=int, default=5)
    args = parser.parse_args()
    tag_data(args.db, args.model, args.batch_size)
