import config
from conftest import StubLLM, DownLLM
import rag

Q_IN = "How do I complain to the Registrar of Cooperative Societies?"


def test_in_scope_full_mode(make_engine):
    llm = StubLLM()
    r = make_engine(llm).ask(Q_IN)
    assert r["mode"] == "full" and r["grounded"] is True and llm.calls == 1
    top = r["sources"][0]
    assert top["file"] == "dummy_act.txt" and "Registrar" in top["excerpt"] + (top["section"] or "")
    assert set(top) == {"n", "file", "page", "section", "score", "excerpt"}


def test_out_of_scope_does_not_guess_or_call_llm(make_engine):
    llm = StubLLM()
    r = make_engine(llm).ask("What is the capital of France?")
    assert r["mode"] == "no_evidence" and r["sources"] == [] and llm.calls == 0
    assert r["answer"] == rag.NO_EVIDENCE


def test_llm_down_falls_back_to_passages(make_engine):
    r = make_engine(DownLLM()).ask(Q_IN)
    assert r["mode"] == "retrieval_only" and r["answer"] == rag.RETRIEVAL_ONLY
    assert r["sources"] and len(r["sources"][0]["excerpt"]) > 0


def test_use_llm_false_never_calls_llm(make_engine):
    llm = StubLLM()
    r = make_engine(llm).ask(Q_IN, use_llm=False)
    assert r["mode"] == "retrieval_only" and llm.calls == 0


def test_llm_disabled_by_config(make_engine, monkeypatch):
    monkeypatch.setattr(config, "LLM_ENABLED", False)
    llm = StubLLM()
    assert make_engine(llm).ask(Q_IN)["mode"] == "retrieval_only" and llm.calls == 0


def test_missing_api_key_falls_back(make_engine, monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", "")
    assert make_engine(None).ask(Q_IN)["mode"] == "retrieval_only"


def test_answer_without_citation_is_flagged_ungrounded(make_engine):
    r = make_engine(StubLLM("You should just complain somewhere.")).ask(Q_IN)
    assert r["mode"] == "full" and r["grounded"] is False


def test_invalid_citation_is_flagged_ungrounded(make_engine):
    r = make_engine(StubLLM("See the rule [9].")).ask(Q_IN)
    assert r["grounded"] is False


def test_prompt_marks_user_text_untrusted():
    assert "untrusted" in rag.SYSTEM_PROMPT


def test_top_score_reported_even_when_refusing(make_engine):
    r = make_engine(StubLLM()).ask("What is the capital of France?")
    assert r["top_score"] is not None
