import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, Header
from .config import settings
from .db import db_dep
from .errors import AppError

FMT = "%Y-%m-%d %H:%M:%S"


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def new_session(conn, user_id: Optional[int], method: str, language: str) -> dict:
    token = secrets.token_urlsafe(32)
    expires = utcnow() + timedelta(hours=settings.session_hours)
    conn.execute("INSERT INTO sessions(token, user_id, method, language, expires_at) VALUES (?,?,?,?,?)",
                 (token, user_id, method, language, expires.strftime(FMT)))
    return {"token": token, "expires_at": expires.strftime(FMT)}


def current_session(authorization: Optional[str] = Header(None), conn=Depends(db_dep)) -> dict:
    """Require a valid Bearer token. Returns session + user info as a dict."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AppError(401, "not_logged_in", "Please log in first.")
    token = authorization[7:].strip()
    row = conn.execute(
        "SELECT s.*, u.name AS user_name, u.member_no, u.society_name FROM sessions s "
        "LEFT JOIN users u ON u.id = s.user_id WHERE s.token=?", (token,)).fetchone()
    if not row or row["ended_at"]:
        raise AppError(401, "session_invalid", "Session ended. Please log in again.")
    if row["expires_at"] < utcnow().strftime(FMT):
        raise AppError(401, "session_expired", "Session expired. Please log in again.")
    return dict(row)


def require_admin(x_admin_key: Optional[str] = Header(None)):
    if not settings.admin_key:
        raise AppError(403, "admin_disabled", "Admin endpoints are disabled.")
    if not hmac.compare_digest(x_admin_key or "", settings.admin_key):
        raise AppError(401, "bad_admin_key", "Invalid admin key.")
