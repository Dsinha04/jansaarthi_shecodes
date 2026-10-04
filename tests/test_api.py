import pytest
from fastapi.testclient import TestClient
import api
import config
from conftest import StubLLM, DownLLM

FRAUD = "You have won the lucky draw. Pay Rs 5000 processing fee and share OTP."
CONTRACT = "1. Sign on blank stamp paper.\n2. Penal interest at 36% per annum on default.\n3. Guarantor is jointly and severally liable for all dues."


@pytest.fixture
def client(make_engine, monkeypatch):
    monkeypatch.setattr(api, "_engine", make_engine(StubLLM()))
    return TestClient(api.app)


@pytest.fixture
def no_kb_client(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "_engine", None)
    monkeypatch.setattr(config, "FAISS_PATH", tmp_path / "missing.index")
    return TestClient(api.app)


def test_health(client):
    r = client.get("/health").json()
    assert r["ok"] is True and "index_ready" in r and "llm_configured" in r


def test_ask_contract_keys(client):
    r = client.post("/ask", json={"text": "How do I complain to the Registrar of Cooperative Societies?", "language": "hi"}).json()
    assert {"answer", "sources", "mode", "grounded", "top_score", "language", "disclaimer"} <= set(r)
    assert r["language"] == "hi" and r["mode"] == "full"


def test_ask_out_of_scope(client):
    assert client.post("/ask", json={"text": "What is the capital of France?"}).json()["mode"] == "no_evidence"


def test_ask_when_llm_down_still_200(make_engine, monkeypatch):
    monkeypatch.setattr(api, "_engine", make_engine(DownLLM()))
    r = TestClient(api.app).post("/ask", json={"text": "How do I complain to the Registrar of Cooperative Societies?"})
    assert r.status_code == 200 and r.json()["mode"] == "retrieval_only"


def test_ask_validation(client):
    assert client.post("/ask", json={"text": "x"}).status_code == 422
    assert client.post("/ask", json={"text": "y" * 1001}).status_code == 422


def test_ask_without_index_is_503(no_kb_client):
    assert no_kb_client.post("/ask", json={"text": "hello there"}).status_code == 503


def test_analyze_contract_rules_only(client):
    r = client.post("/analyze-contract", json={"text": CONTRACT}).json()
    assert r["risk_level"] == "high" and r["explain_available"] is False and "disclaimer" in r


def test_analyze_contract_with_explain(client):
    r = client.post("/analyze-contract", json={"text": CONTRACT, "explain": True}).json()
    assert r["explain_available"] and "legal_context" in r["findings"][0] and "mode" in r["findings"][0]["legal_context"]


def test_analyze_contract_explain_without_kb_still_returns_flags(no_kb_client):
    r = no_kb_client.post("/analyze-contract", json={"text": CONTRACT, "explain": True})
    assert r.status_code == 200 and r.json()["findings"] and r.json()["explain_available"] is False


def test_analyze_contract_size_limit(client):
    assert client.post("/analyze-contract", json={"text": "y" * 30001}).status_code == 422


def test_check_notice(client):
    r = client.post("/check-notice", json={"text": FRAUD}).json()
    assert r["verdict"] == "likely_fraud" and r["advice"]


def test_schemes_endpoint(client):
    r = client.post("/schemes/recommend", json={"owns_land": True, "occupation": ["farmer"]}).json()
    assert {s["id"] for s in r["schemes"]} == {"pm_kisan", "kcc", "pmfby"}
    assert client.post("/schemes/recommend", json={"occupation": ["astronaut"]}).status_code == 422


def test_grievance_endpoint_with_kb(client):
    body = {"category": "loan_dispute", "society_type": "multi_state", "member_name": "Ramesh"}
    r = client.post("/grievance/guide", json=body).json()
    assert r["steps"] and r["evidence"] and "Ramesh" in r["complaint_template"]


def test_grievance_endpoint_without_kb(no_kb_client):
    r = no_kb_client.post("/grievance/guide", json={"category": "loan_dispute"})
    assert r.status_code == 200 and r.json()["evidence"] == [] and r.json()["steps"]


def test_grievance_validation(client):
    assert client.post("/grievance/guide", json={"category": "bogus"}).status_code == 422


def test_api_key_protection(client, monkeypatch):
    monkeypatch.setattr(config, "SERVICE_KEY", "secret")
    assert client.get("/health").status_code == 200
    assert client.post("/check-notice", json={"text": FRAUD}).status_code == 401
    assert client.post("/check-notice", json={"text": FRAUD}, headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.post("/check-notice", json={"text": FRAUD}, headers={"X-API-Key": "secret"}).status_code == 200
