import json
import secrets
from datetime import datetime
from fastapi import APIRouter, Depends
from .. import schemas
from ..db import db_dep, log_event
from ..errors import AppError
from ..security import current_session
from ..services import ai_client, pipeline

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


def _row(r, full=False):
    d = {k: r[k] for k in ("id", "reference", "category", "society_type", "member_name", "society_name",
                           "member_no", "language", "status", "created_at")}
    if full:
        d["details"] = r["details"]
        d["letter_text"] = r["letter_text"]
    return d


def _owned(conn, sess, cid):
    r = conn.execute("SELECT * FROM complaints WHERE id=?", (cid,)).fetchone()
    if not r or r["session_token"] != sess["token"] and (sess["user_id"] is None or r["user_id"] != sess["user_id"]):
        raise AppError(404, "complaint_not_found", "Complaint not found.")
    return r


@router.post("")
def create(body: schemas.ComplaintIn, sess=Depends(current_session), conn=Depends(db_dep)):
    details_en, in_ok = pipeline.to_english(body.details or "", body.language)
    guide = ai_client.call("/grievance/guide", {
        "category": body.category, "society_type": body.society_type,
        "member_name": body.member_name or sess.get("user_name"),
        "society_name": body.society_name or sess.get("society_name"),
        "member_no": body.member_no or sess.get("member_no"),
        "details": details_en or None, "language": "en"})
    reference = f"JS-{datetime.now():%Y%m%d}-{secrets.token_hex(2).upper()}"
    letter = guide.get("complaint_template", "")
    cur = conn.execute(
        "INSERT INTO complaints(reference, user_id, session_token, category, society_type, member_name, "
        "society_name, member_no, details, language, letter_text) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (reference, sess["user_id"], sess["token"], body.category, body.society_type, body.member_name,
         body.society_name, body.member_no, body.details, body.language, letter))
    log_event(conn, "info", "complaint", f"created {reference}")
    local, ok = pipeline.localize(guide, body.language)
    return {"id": cur.lastrowid, "reference": reference, "guide": local,
            "letter_english": letter, "translation_ok": ok and in_ok}


@router.get("")
def list_mine(sess=Depends(current_session), conn=Depends(db_dep)):
    if sess["user_id"] is not None:
        rows = conn.execute("SELECT * FROM complaints WHERE user_id=? ORDER BY id DESC LIMIT 50",
                            (sess["user_id"],)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM complaints WHERE session_token=? ORDER BY id DESC",
                            (sess["token"],)).fetchall()
    return {"complaints": [_row(r) for r in rows]}


@router.get("/{cid}")
def get_one(cid: int, sess=Depends(current_session), conn=Depends(db_dep)):
    return _row(_owned(conn, sess, cid), full=True)
