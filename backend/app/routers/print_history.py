import json
from fastapi import APIRouter, Depends
from .. import schemas
from ..db import db_dep, log_event
from ..errors import AppError
from ..security import current_session
from ..services import printer, receipt
from .complaints import _owned

router = APIRouter(prefix="/api", tags=["print", "history"])


def _answer_lines(payload: dict) -> list[str]:
    lines = []
    if payload.get("answer"):
        lines.append(payload["answer"])
    for s in payload.get("sources", [])[:3]:
        lines.append(f"[{s['n']}] {s['file']}" + (f", p.{s['page']}" if s.get("page") else "")
                     + (f", {s['section']}" if s.get("section") else ""))
    for f in payload.get("findings", [])[:5]:
        lines.append(f"* {f['title']}: {f['explanation']}")
    for f in payload.get("flags", [])[:5]:
        lines.append(f"* {f['title']}")
    for a in payload.get("advice", []):
        lines.append(f"- {a}")
    for s in payload.get("schemes", [])[:5]:
        lines.append(f"* {s['name']} ({s['status']})")
    return lines or ["(no content)"]


def build_receipt(body: schemas.PrintIn, sess, conn) -> tuple[str, str]:
    """Return (receipt_text, file_stem)."""
    if body.kind == "complaint":
        if body.complaint_id is None:
            raise AppError(422, "missing_id", "complaint_id is required.")
        c = _owned(conn, sess, body.complaint_id)
        text = receipt.build("COMPLAINT", [c["letter_text"] or ""], reference=c["reference"],
                             footer="Submit to the society office or Registrar and keep a stamped copy.")
        conn.execute("UPDATE complaints SET status='printed' WHERE id=?", (c["id"],))
        return text, c["reference"]
    if body.kind == "answer":
        if body.conversation_id is None:
            raise AppError(422, "missing_id", "conversation_id is required.")
        r = conn.execute("SELECT * FROM conversations WHERE id=? AND session_token=?",
                         (body.conversation_id, sess["token"])).fetchone()
        if not r:
            raise AppError(404, "conversation_not_found", "Answer not found.")
        payload = json.loads(r["payload"] or "{}")
        text = receipt.build(r["kind"].upper(), _answer_lines(payload), reference=f"C{r['id']}",
                             footer=payload.get("disclaimer"))
        return text, f"answer_{r['id']}"
    if not body.text:
        raise AppError(422, "missing_text", "text is required.")
    return receipt.build(body.title or "NOTE", [body.text]), "note"


@router.post("/receipt/preview")
def preview(body: schemas.PrintIn, sess=Depends(current_session), conn=Depends(db_dep)):
    text, _ = build_receipt(body, sess, conn)
    return {"receipt": text}


@router.post("/print")
def do_print(body: schemas.PrintIn, sess=Depends(current_session), conn=Depends(db_dep)):
    text, stem = build_receipt(body, sess, conn)
    result = printer.print_text(f"{stem}_{sess['token'][:6]}", text)
    log_event(conn, "info" if result["printed"] else "warn", "printer", f"print {body.kind}", str(result["reason"]))
    return {**result, "receipt": text}


@router.get("/history")
def history(limit: int = 30, sess=Depends(current_session), conn=Depends(db_dep)):
    limit = max(1, min(limit, 100))
    if sess["user_id"] is not None:
        rows = conn.execute("SELECT * FROM conversations WHERE user_id=? ORDER BY id DESC LIMIT ?",
                            (sess["user_id"], limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM conversations WHERE session_token=? ORDER BY id DESC LIMIT ?",
                            (sess["token"], limit)).fetchall()
    return {"items": [{"id": r["id"], "kind": r["kind"], "language": r["language"], "question": r["question"],
                       "answer": r["answer"], "mode": r["mode"], "created_at": r["created_at"]} for r in rows]}


@router.get("/history/{cid}")
def history_item(cid: int, sess=Depends(current_session), conn=Depends(db_dep)):
    r = conn.execute("SELECT * FROM conversations WHERE id=?", (cid,)).fetchone()
    if not r or (r["session_token"] != sess["token"] and (sess["user_id"] is None or r["user_id"] != sess["user_id"])):
        raise AppError(404, "conversation_not_found", "Not found.")
    return {"id": r["id"], "kind": r["kind"], "question": r["question"], "created_at": r["created_at"],
            "result": json.loads(r["payload"] or "{}")}
