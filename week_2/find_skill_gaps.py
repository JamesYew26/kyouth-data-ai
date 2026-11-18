"""Compare a candidate's resume against the tagged jobs table and report missing skills.

Hybrid design:
  1. LLM (non-deterministic): extract the candidate's skills from free-text resume.
  2. SQL + Python (deterministic): count how many jobs require each skill, subtract
     what the candidate already has, and rank the gaps by market demand.

    uv run find_skill_gaps.py [--resume data/resume_d3.txt] [--db data/jobs_d1.db]
"""

import argparse
import logging
import sqlite3
from collections import Counter
from pathlib import Path

from prompt_model import LLMError, parse_json_response, prompt_model, with_retry
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"

# Soft skills / methodologies are not "technical gaps" for this report.
NON_TECHNICAL = {
    "leadership",
    "management",
    "project management",
    "communication",
    "agile",
    "scrum",
    "teamwork",
    "problem solving",
    "interpersonal skills",
    "pmp",
    "scrum master",
}

# Map common spelling variants onto one canonical name so set arithmetic lines up.
SYNONYMS = {
    "dotnet": ".net",
    ".net core": ".net",
    "dot net": ".net",
    "postgres": "postgresql",
    "js": "javascript",
    "node": "node.js",
    "nodejs": "node.js",
    "k8s": "kubernetes",
    "gcp": "google cloud",
    "powerbi": "power bi",
}

RESUME_PROMPT = """Extract every technical skill, programming language, framework, tool,
cloud service and database mentioned in this resume. Return ONLY a JSON array of strings.

Resume:
{resume}"""


class SkillGap(BaseModel):
    skill: str
    jobs_requiring: int


class SkillGapResult(BaseModel):
    candidate_skills: list[str] = []
    gaps: list[SkillGap] = []
    jobs_analysed: int = 0
    error: str | None = None


def normalise_skill(skill: str) -> str:
    s = " ".join(skill.lower().split()).strip(" .,;")
    return SYNONYMS.get(s, s)


def read_resume(path: Path) -> str:
    """Read a .pdf or plain-text resume."""
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_candidate_skills(resume_text: str, model: str | None = None) -> set[str]:
    def call() -> list:
        skills = parse_json_response(
            prompt_model(model, RESUME_PROMPT.format(resume=resume_text))
        )
        if not isinstance(skills, list):
            raise LLMError("expected a JSON array of skills")
        return skills

    skills = with_retry(call, retry_on=(LLMError,), log=logger.warning)
    return {normalise_skill(str(s)) for s in skills if str(s).strip()}


def skill_demand(db_path: Path) -> tuple[Counter, int]:
    """Return (Counter{skill: number of jobs listing it}, number of tagged jobs)."""
    demand: Counter = Counter()
    jobs = 0
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT tech_stack FROM jobs WHERE tech_stack IS NOT NULL AND TRIM(tech_stack) != ''"
        )
        for (
            tech_stack,
        ) in cursor:  # the cursor streams rows; no need to load all at once
            jobs += 1
            demand.update(
                {normalise_skill(s) for s in tech_stack.split(",") if s.strip()}
            )
    conn.close()
    return demand, jobs


def compute_gaps(
    candidate: set[str], demand: Counter, top_n: int | None = None
) -> list[SkillGap]:
    """Skills the market asks for that the candidate lacks, most in-demand first.

    Pure function: same input -> same output (ties broken alphabetically).
    """
    missing = [
        (skill, n)
        for skill, n in demand.items()
        if skill not in candidate and skill not in NON_TECHNICAL
    ]
    missing.sort(key=lambda item: (-item[1], item[0]))
    return [SkillGap(skill=s, jobs_requiring=n) for s, n in missing[:top_n]]


def find_skill_gaps(
    resume_path: Path, db_path: Path, model: str | None = None, top_n: int | None = 15
) -> SkillGapResult:
    """End-to-end gap analysis. Never raises: errors are returned in `result.error`."""
    try:
        demand, jobs = skill_demand(db_path)
        if not jobs:
            return SkillGapResult(
                error="No tagged jobs in the database; run tag_data.py first"
            )
        candidate = (
            extract_candidate_skills(read_resume(resume_path), model) - NON_TECHNICAL
        )
        return SkillGapResult(
            candidate_skills=sorted(candidate),
            gaps=compute_gaps(candidate, demand, top_n),
            jobs_analysed=jobs,
        )
    except Exception as exc:  # API boundary: report instead of crashing the caller
        logger.exception("Skill gap analysis failed")
        return SkillGapResult(error=str(exc))


def format_report(result: SkillGapResult) -> str:
    if result.error:
        return f"Skill gap analysis failed: {result.error}"
    if not result.gaps:
        return f"No gaps found against {result.jobs_analysed} jobs. Nice!"
    lines = [f"Top skill gaps across {result.jobs_analysed} job listings:"]
    lines += [
        f"  {i:>2}. {g.skill} — required by {g.jobs_requiring} job(s)"
        for i, g in enumerate(result.gaps, start=1)
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(
        description="Resume vs. job-market skill gap report"
    )
    parser.add_argument("--resume", type=Path, default=DATA_DIR / "resume_d3.txt")
    parser.add_argument("--db", type=Path, default=DATA_DIR / "jobs_d1.db")
    parser.add_argument("--model", default=None)
    parser.add_argument("--top", type=int, default=15)
    args = parser.parse_args()
    print(format_report(find_skill_gaps(args.resume, args.db, args.model, args.top)))
