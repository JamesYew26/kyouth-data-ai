import json
import sqlite3

import pytest
from pydantic import ValidationError
from src.ingestor import extract_html_from_mhtml, ingest_all_mhtml
from src.loader import load_all_jsons
from src.processor import parse_job_html, process_all_html
from src.profiler import run_data_profile

JOB_HTML = """
<html><head><meta property="og:url" content="https://my.jobstreet.com/job/12345/"></head>
<body>
  <h1 data-automation="job-detail-title">  Data   Engineer </h1>
  <span data-automation="advertiser-name">Acme Sdn Bhd</span>
  <div data-automation="jobAdDetails"><p>Build pipelines with Python and SQL.</p></div>
</body></html>
"""

MHTML = (
    b"MIME-Version: 1.0\r\n"
    b'Content-Type: multipart/related; boundary="B"\r\n\r\n'
    b"--B\r\nContent-Type: text/html\r\nContent-Transfer-Encoding: quoted-printable\r\n\r\n"
    b"<html><body>caf=C3=A9</body></html>\r\n"
    b"--B--\r\n"
)


def test_extract_html_from_mhtml_decodes_quoted_printable():
    assert extract_html_from_mhtml(MHTML) == "<html><body>café</body></html>".encode()


def test_extract_html_from_mhtml_returns_none_without_html_part():
    assert extract_html_from_mhtml(b"Content-Type: text/plain\r\n\r\nhi") is None


def test_ingest_counts_failures(tmp_path):
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    (src / "good.mhtml").write_bytes(MHTML)
    (src / "bad.mhtml").write_bytes(b"Content-Type: text/plain\r\n\r\nhi")
    stats = ingest_all_mhtml(src, out)
    assert stats == {"total": 2, "extracted": 1, "failed": 1}
    assert (out / "good.html").exists()


def test_parse_job_html_extracts_and_cleans_fields():
    job = parse_job_html(JOB_HTML)
    assert job.source_id == "12345"
    assert job.job_title == "Data Engineer"  # whitespace collapsed
    assert job.company == "Acme Sdn Bhd"
    assert "Python and SQL" in job.description


@pytest.mark.parametrize(
    "remove, error",
    [
        (
            '<meta property="og:url" content="https://my.jobstreet.com/job/12345/">',
            "og:url",
        ),
        ('<span data-automation="advertiser-name">Acme Sdn Bhd</span>', "company"),
    ],
)
def test_parse_job_html_fails_early_on_missing_fields(remove, error):
    with pytest.raises(ValueError, match=error):
        parse_job_html(JOB_HTML.replace(remove, ""))


def test_parse_job_html_rejects_too_short_description():
    with pytest.raises(ValidationError):
        parse_job_html(JOB_HTML.replace("Build pipelines with Python and SQL.", "Hi"))


def test_end_to_end_load_is_idempotent(tmp_path):
    bronze, silver, db = (
        tmp_path / "bronze",
        tmp_path / "silver",
        tmp_path / "gold" / "jobs.db",
    )
    bronze.mkdir()
    (bronze / "job.html").write_text(JOB_HTML)
    (bronze / "broken.html").write_text("<html></html>")

    assert process_all_html(bronze, silver) == {
        "total": 2,
        "processed": 1,
        "rejected": 1,
    }
    assert json.loads((silver / "job.json").read_text())["source_id"] == "12345"

    first = load_all_jsons(silver, db)
    second = load_all_jsons(silver, db)
    assert first["inserted"] == 1
    assert second == {"total": 1, "inserted": 0, "skipped": 1, "failed": 0}

    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 1

    report = run_data_profile(db)
    assert report["total"] == 1 and report["untagged"] == 1
