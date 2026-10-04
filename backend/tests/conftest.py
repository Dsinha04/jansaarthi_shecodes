import os
import tempfile
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    d = tempfile.mkdtemp()
    monkeypatch.setenv("DB_PATH", os.path.join(d, "t.db"))
    monkeypatch.setenv("HARDWARE_MODE", "mock")
    monkeypatch.setenv("STT_MODE", "mock")
    monkeypatch.setenv("OCR_MODE", "mock")
    monkeypatch.setenv("TRANSLATE_MODE", "passthrough")
    monkeypatch.setenv("PRINTER_NAME", "")
    monkeypatch.setenv("ADMIN_KEY", "adm")
    from app.main import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture()
def auth(client):
    r = client.post("/api/auth/rfid", json={"uid": "DEMO0001", "language": "hi"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}


FAKE_ASK = {"answer": "Complain in writing [1].", "sources": [{"n": 1, "file": "a.txt", "page": None,
            "section": "Sec 6", "score": 0.4, "excerpt": "x"}], "mode": "full", "grounded": True,
            "top_score": 0.4, "language": "en", "disclaimer": "Not legal advice."}


@pytest.fixture()
def fake_ai(monkeypatch):
    calls = []

    def fake(path, payload, timeout=90.0):
        calls.append((path, payload))
        if path == "/ask":
            return dict(FAKE_ASK)
        if path == "/grievance/guide":
            return {"category": payload["category"], "label": "a loan dispute",
                    "steps": [{"n": 1, "title": "Collect papers", "detail": "d"}], "evidence": [],
                    "complaint_template": f"To the Registrar. I am {payload['member_name']}.",
                    "note": "n", "language": "en", "disclaimer": "d"}
        if path == "/check-notice":
            return {"verdict": "likely_fraud", "score": 9, "flags": [{"rule": "r", "severity": "high",
                    "title": "Asks for OTP", "match": "OTP", "explanation": "e"}], "advice": ["Do not share OTP"],
                    "note": None, "language": "en", "disclaimer": "d"}
        if path == "/schemes/recommend":
            return {"schemes": [{"id": "pm", "name": "PM-KISAN", "summary": "s", "status": "likely_eligible",
                    "checks": [], "exclusions": [], "documents": [], "where_to_apply": "CSC",
                    "source_url": "u", "verified": False}], "note": "n", "language": "en", "disclaimer": "d"}
        if path == "/analyze-contract":
            return {"risk_level": "high", "score": 8, "findings": [], "explain_available": False,
                    "language": "en", "disclaimer": "d"}
        raise AssertionError(path)
    monkeypatch.setattr("app.services.ai_client.call", fake)
    return calls
