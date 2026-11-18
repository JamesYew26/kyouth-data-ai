"""Silver layer: parse bronze HTML into validated JobListing JSON records (2_silver)."""

import logging
from pathlib import Path

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, ValidationError, field_validator

logger = logging.getLogger(__name__)


# --- Data contract -----------------------------------------------------------
class JobListing(BaseModel):
    """Schema every silver record must satisfy. Anything else is rejected (fail early)."""

    source_id: str = Field(..., min_length=1)
    job_title: str = Field(..., min_length=1)
    company: str = Field(..., min_length=1)
    description: str = Field(..., min_length=10)

    @field_validator("job_title", "company", "description", mode="before")
    @classmethod
    def collapse_whitespace(cls, v):
        return " ".join(v.split()) if isinstance(v, str) else v


# --- Extraction --------------------------------------------------------------
def _text(el) -> str | None:
    return el.get_text(separator=" ", strip=True) if el else None


def parse_job_html(html: str) -> JobListing:
    """Extract one JobListing from a JobStreet job page.

    Raises ValueError (missing element) or pydantic.ValidationError (bad value).
    """
    soup = BeautifulSoup(html, "html.parser")

    og_url = soup.find("meta", property="og:url")
    if not og_url or not og_url.get("content"):
        raise ValueError("missing og:url meta tag")
    source_id = og_url["content"].rstrip("/").split("/")[-1]

    # Prefer JobStreet's stable data-automation hooks; fall back to generic tags.
    title = _text(
        soup.find(attrs={"data-automation": "job-detail-title"}) or soup.find("h1")
    )
    company = _text(
        soup.find(attrs={"data-automation": "advertiser-name"})
        or soup.find(class_="company")
    )
    description = _text(
        soup.find("div", attrs={"data-automation": "jobAdDetails"})
        or soup.find(class_="description")
    )

    for name, value in (
        ("job_title", title),
        ("company", company),
        ("description", description),
    ):
        if not value:
            raise ValueError(f"missing {name}")

    return JobListing(
        source_id=source_id, job_title=title, company=company, description=description
    )


def process_all_html(input_dir: Path, output_dir: Path) -> dict[str, int]:
    """Parse every bronze HTML file; write valid records as JSON, skip and log the rest."""
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {"total": 0, "processed": 0, "rejected": 0}
    for html_file in sorted(input_dir.glob("*.html")):
        stats["total"] += 1
        try:
            job = parse_job_html(html_file.read_text(encoding="utf-8", errors="ignore"))
            (output_dir / f"{html_file.stem}.json").write_text(
                job.model_dump_json(indent=4), encoding="utf-8"
            )
            stats["processed"] += 1
        except (ValueError, ValidationError) as exc:
            # ValidationError subclasses ValueError, but naming it documents intent.
            stats["rejected"] += 1
            logger.warning("Rejected %s: %s", html_file.name, str(exc).splitlines()[0])

    logger.info(
        "Silver summary: total=%(total)d processed=%(processed)d rejected=%(rejected)d",
        stats,
    )
    return stats
