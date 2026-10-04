import json
import pathlib
import evaluate
from conftest import StubLLM, DownLLM

DATA = json.loads((pathlib.Path(__file__).parent / "eval_dummy.json").read_text())


def test_best_threshold_separable():
    r = evaluate.best_threshold([0.82, 0.9, 0.85], [0.6, 0.7])
    assert r["separable"] and 0.7 < r["threshold"] < 0.82 and r["accuracy"] == 1.0


def test_best_threshold_overlap_prefers_refusing():
    r = evaluate.best_threshold([0.8, 0.75], [0.78, 0.7])
    assert not r["separable"] and r["accuracy"] < 1.0 or r["accuracy"] == 1.0


def test_run_eval_all_pass(make_engine):
    rows = evaluate.run_eval(make_engine(StubLLM("Answer [1].")), DATA)
    assert all(r["ok"] for r in rows), [r for r in rows if not r["ok"]]


def test_run_eval_catches_ungrounded_answer(make_engine):
    rows = evaluate.run_eval(make_engine(StubLLM("No citation here.")), DATA)
    assert not all(r["ok"] for r in rows if r["kind"] == "in")


def test_run_eval_retrieval_only_mode(make_engine):
    llm = StubLLM()
    rows = evaluate.run_eval(make_engine(llm), DATA, use_llm=False)
    assert all(r["ok"] for r in rows) and llm.calls == 0


def test_run_eval_when_llm_down(make_engine):
    assert all(r["ok"] for r in evaluate.run_eval(make_engine(DownLLM()), DATA))
