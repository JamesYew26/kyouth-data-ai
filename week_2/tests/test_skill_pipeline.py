"""Unit tests. The LLM is always mocked, so these run offline and deterministically."""

import sqlite3
from collections import Counter

import find_skill_gaps as fsg
import pytest
import tag_data
from prompt_model import LLMError, parse_json_response, with_retry


@pytest.fixture
def jobs_db(tmp_path):
    db = tmp_path / "jobs.db"
    with sqlite3.connect(db) as conn:
        conn.execute(
            "CREATE TABLE jobs (source_id TEXT PRIMARY KEY, description TEXT, tech_stack TEXT)"
        )
        conn.executemany(
            "INSERT INTO jobs VALUES (?, ?, ?)",
            [
                ("1", "Python and SQL and Docker", "Python, SQL, Docker"),
                ("2", "Python, Spark on AWS", "python, Spark, AWS, Agile"),
                ("3", "Untagged job", None),
            ],
        )
    return db


@pytest.mark.parametrize(
    "raw",
    [
        '["a", "b"]',
        '```json\n["a", "b"]\n```',
        '<think>reasoning...</think>\n["a", "b"]',
        'Sure! Here you go:\n```\n["a", "b"]\n```',
    ],
)
def test_parse_json_response_handles_messy_llm_output(raw):
    assert parse_json_response(raw) == ["a", "b"]


def test_parse_json_response_raises_llm_error():
    with pytest.raises(LLMError):
        parse_json_response("I could not find any skills")


def test_with_retry_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr("prompt_model.time.sleep", lambda _: None)
    calls = iter([LLMError("boom"), LLMError("boom"), "ok"])

    def flaky():
        result = next(calls)
        if isinstance(result, Exception):
            raise result
        return result

    assert with_retry(flaky, retry_on=(LLMError,), log=lambda _: None) == "ok"


def test_normalise_skill_maps_synonyms():
    assert fsg.normalise_skill("  Postgres ") == "postgresql"
    assert fsg.normalise_skill("DotNet") == ".net"


def test_compute_gaps_ranks_by_demand_and_excludes_soft_skills():
    demand = Counter({"python": 2, "aws": 1, "spark": 1, "docker": 1, "agile": 5})
    gaps = fsg.compute_gaps({"python", "docker"}, demand)
    assert [(g.skill, g.jobs_requiring) for g in gaps] == [("aws", 1), ("spark", 1)]


def test_skill_demand_counts_jobs_not_mentions(jobs_db):
    demand, jobs = fsg.skill_demand(jobs_db)
    assert jobs == 2
    assert demand["python"] == 2  # "Python" and "python" normalised together


def test_find_skill_gaps_end_to_end(jobs_db, tmp_path, monkeypatch):
    resume = tmp_path / "resume.txt"
    resume.write_text("I use Python and Docker daily.")
    monkeypatch.setattr(
        fsg, "prompt_model", lambda model, prompt: '["Python", "Docker", "Teamwork"]'
    )

    result = fsg.find_skill_gaps(resume, jobs_db)
    assert result.error is None
    assert result.candidate_skills == ["docker", "python"]  # soft skill filtered out
    assert [g.skill for g in result.gaps] == ["aws", "spark", "sql"]


def test_find_skill_gaps_reports_errors_instead_of_raising(jobs_db, tmp_path):
    result = fsg.find_skill_gaps(tmp_path / "missing.txt", jobs_db)
    assert result.error and result.gaps == []


def test_tag_data_only_updates_pending_rows(jobs_db, monkeypatch):
    monkeypatch.setattr(
        tag_data,
        "prompt_model",
        lambda model, prompt: '{"3": "Go, Kafka", "999": "ignored"}',
    )
    stats = tag_data.tag_data(jobs_db, batch_size=5)
    assert stats == {"pending": 1, "tagged": 1, "failed_batches": 0}
    with sqlite3.connect(jobs_db) as conn:
        assert (
            conn.execute("SELECT tech_stack FROM jobs WHERE source_id='3'").fetchone()[
                0
            ]
            == "Go, Kafka"
        )
        assert (
            conn.execute("SELECT COUNT(*) FROM jobs WHERE source_id='999'").fetchone()[
                0
            ]
            == 0
        )
