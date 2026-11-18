import app as backend
from fastapi.testclient import TestClient
from find_skill_gaps import SkillGap, SkillGapResult
from prompt_model import LLMError

client = TestClient(backend.app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_empty_request_gets_help_message():
    assert (
        "upload a resume" in client.post("/chat", data={"message": " "}).json()["reply"]
    )


def test_text_only_goes_to_llm(monkeypatch):
    monkeypatch.setattr(
        backend, "prompt_model", lambda model, prompt: f"echo: {prompt}"
    )
    assert client.post("/chat", data={"message": "hi"}).json() == {"reply": "echo: hi"}


def test_file_only_runs_gap_analysis_and_cleans_up(monkeypatch):
    seen = {}

    def fake_find(path, db):
        seen["path"] = path
        assert path.read_text() == "Python, SQL"
        return SkillGapResult(
            gaps=[SkillGap(skill="aws", jobs_requiring=5)], jobs_analysed=7
        )

    monkeypatch.setattr(backend, "find_skill_gaps", fake_find)
    resp = client.post(
        "/chat", files={"file": ("cv.txt", b"Python, SQL", "text/plain")}
    )
    assert "aws — required by 5 job(s)" in resp.json()["reply"]
    assert not seen["path"].exists()  # temp file removed


def test_malicious_filename_is_not_used_as_a_path(monkeypatch):
    monkeypatch.setattr(
        backend, "find_skill_gaps", lambda p, db: SkillGapResult(jobs_analysed=1)
    )
    resp = client.post(
        "/chat", files={"file": ("../../etc/evil.txt", b"x", "text/plain")}
    )
    assert resp.status_code == 200


def test_rejects_unsupported_file_type():
    resp = client.post(
        "/chat", files={"file": ("cv.exe", b"MZ", "application/octet-stream")}
    )
    assert resp.status_code == 415


def test_llm_failure_returns_502_not_crash(monkeypatch):
    def boom(model, prompt):
        raise LLMError("quota exceeded")

    monkeypatch.setattr(backend, "prompt_model", boom)
    resp = client.post("/chat", data={"message": "hi"})
    assert resp.status_code == 502 and "quota exceeded" in resp.json()["detail"]
