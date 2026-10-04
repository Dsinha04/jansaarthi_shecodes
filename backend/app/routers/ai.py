import json
from fastapi import APIRouter, Depends
from .. import schemas
from ..db import db_dep
from ..security import current_session
from ..services import ai_client, pipeline

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _store(conn, sess, kind, lang, question, question_en, answer, payload, mode=None) -> int:
    cur = conn.execute(
        "INSERT INTO conversations(session_token, user_id, kind, language, question, question_en, answer, payload, mode) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (sess["token"], sess["user_id"], kind, lang, question, question_en, answer,
         json.dumps(payload, ensure_ascii=False), mode))
    return cur.lastrowid


def _finish(conn, sess, kind, lang, q, q_en, result, answer=None, mode=None):
    local, ok = pipeline.localize(result, lang)
    local["translation_ok"] = ok
    local["conversation_id"] = _store(conn, sess, kind, lang, q, q_en, answer or local.get("answer"), local, mode)
    return local


@router.post("/ask")
def ask(body: schemas.AskIn, sess=Depends(current_session), conn=Depends(db_dep)):
    q_en, in_ok = pipeline.to_english(body.text, body.language)
    result = ai_client.call("/ask", {"text": q_en, "language": "en"})
    out = _finish(conn, sess, "ask", body.language, body.text, q_en, result, mode=result.get("mode"))
    out["translation_ok"] = out["translation_ok"] and in_ok
    return out


@router.post("/contract")
def contract(body: schemas.ContractIn, sess=Depends(current_session), conn=Depends(db_dep)):
    text_en, in_ok = pipeline.to_english(body.text, body.language)
    result = ai_client.call("/analyze-contract", {"text": text_en, "explain": body.explain, "language": "en"})
    summary = f"Risk level: {result.get('risk_level')} ({len(result.get('findings', []))} findings)"
    out = _finish(conn, sess, "contract", body.language, body.text[:500], text_en[:500], result, answer=summary)
    out["translation_ok"] = out["translation_ok"] and in_ok
    return out


@router.post("/notice")
def notice(body: schemas.NoticeIn, sess=Depends(current_session), conn=Depends(db_dep)):
    text_en, in_ok = pipeline.to_english(body.text, body.language)
    result = ai_client.call("/check-notice", {"text": text_en, "language": "en"})
    out = _finish(conn, sess, "notice", body.language, body.text[:500], text_en[:500], result,
                  answer=f"Verdict: {result.get('verdict')}")
    out["translation_ok"] = out["translation_ok"] and in_ok
    return out


@router.post("/schemes")
def schemes(body: schemas.SchemesIn, sess=Depends(current_session), conn=Depends(db_dep)):
    result = ai_client.call("/schemes/recommend", {**body.model_dump(), "language": "en"})
    n = len(result.get("schemes", []))
    return _finish(conn, sess, "schemes", body.language, json.dumps(body.model_dump(exclude={"language"})),
                   None, result, answer=f"{n} schemes found")
