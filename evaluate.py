"""Evaluate retrieval quality and tune MIN_SCORE on your real knowledge base.

Question file (JSON):
  {"in_scope":     [{"q": "...", "expect_source": "file name part", "expect_phrase": "optional text in the right passage"}],
   "out_of_scope": ["question the documents cannot answer", ...]}

  python evaluate.py tune eval/questions.json       # suggests a MIN_SCORE
  python evaluate.py run  eval/questions.json       # full check (uses the LLM API)
  python evaluate.py run  eval/questions.json --retrieval-only
"""
import argparse
import json
import sys


def top_score(engine, q):
    hits = engine.retrieve(q, 1)
    return hits[0]["score"] if hits else 0.0


def best_threshold(in_scores, out_scores):
    """Pick the cut-off that answers most in-scope and refuses most out-of-scope questions.
    Ties go to the higher cut-off: for legal answers, refusing wrongly is safer than answering wrongly."""
    allv = sorted(set(in_scores + out_scores))
    if not allv:
        raise ValueError("no scores")
    cands = [allv[0] - 0.01] + [(a + b) / 2 for a, b in zip(allv, allv[1:])] + [allv[-1] + 0.01]
    n = len(in_scores) + len(out_scores)
    best = None
    for t in cands:
        acc = (sum(s >= t for s in in_scores) + sum(s < t for s in out_scores)) / n
        if best is None or acc >= best["accuracy"]:
            best = {"threshold": round(t, 3), "accuracy": round(acc, 3)}
    best["in_answered"] = sum(s >= best["threshold"] for s in in_scores)
    best["out_refused"] = sum(s < best["threshold"] for s in out_scores)
    best["separable"] = min(in_scores, default=1) > max(out_scores, default=0)
    return best


def run_eval(engine, data, use_llm=True):
    rows = []
    for item in data.get("in_scope", []):
        hits = [h for h in engine.retrieve(item["q"]) if h["score"] >= engine.min_score]
        src_ok = any(item["expect_source"].lower() in h["source"].lower() for h in hits)
        phrase = item.get("expect_phrase")
        phrase_ok = True if not phrase else any(phrase.lower() in h["text"].lower() for h in hits)
        res = engine.ask(item["q"], use_llm=use_llm)
        ok = src_ok and phrase_ok and (res["mode"] == "retrieval_only" or
                                       (res["mode"] == "full" and res["grounded"]))
        rows.append({"kind": "in", "q": item["q"], "ok": ok, "mode": res["mode"], "grounded": res["grounded"],
                     "src_ok": src_ok, "phrase_ok": phrase_ok})
    for q in data.get("out_of_scope", []):
        res = engine.ask(q, use_llm=use_llm)
        rows.append({"kind": "out", "q": q, "ok": res["mode"] == "no_evidence", "mode": res["mode"],
                     "grounded": None, "src_ok": None, "phrase_ok": None})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["tune", "run"])
    ap.add_argument("file")
    ap.add_argument("--retrieval-only", action="store_true")
    a = ap.parse_args()
    data = json.load(open(a.file, encoding="utf-8"))
    from rag import RAGEngine
    engine = RAGEngine()
    if a.cmd == "tune":
        ins = [top_score(engine, i["q"]) for i in data["in_scope"]]
        outs = [top_score(engine, q) for q in data["out_of_scope"]]
        print(f"in-scope top scores : min {min(ins):.3f}  max {max(ins):.3f}")
        print(f"out-of-scope scores : min {min(outs):.3f}  max {max(outs):.3f}")
        print("suggestion:", best_threshold(ins, outs))
        print("Set MIN_SCORE in config.py to the suggested threshold, then run:  python evaluate.py run", a.file)
        return
    rows = run_eval(engine, data, use_llm=not a.retrieval_only)
    for r in rows:
        print(("PASS" if r["ok"] else "FAIL"), r["kind"], r["mode"], "|", r["q"])
    passed = sum(r["ok"] for r in rows)
    print(f"\n{passed}/{len(rows)} passed")
    sys.exit(0 if passed == len(rows) else 1)


if __name__ == "__main__":
    main()
