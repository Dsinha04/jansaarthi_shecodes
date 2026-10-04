from fastapi import APIRouter, Depends
from ..db import db_dep
from ..security import require_admin
from ..services import ai_client, hardware, ocr, printer, speech, translate
from ..errors import AppError

router = APIRouter(prefix="/api", tags=["system"])

@router.get("/health")
def health(conn=Depends(db_dep)):
    try: conn.execute("SELECT 1").fetchone(); db_ok = True
    except Exception: db_ok = False
    ai = ai_client.health(); comps = {"database":{"ok":db_ok}, "ai_core":{"ok":bool(ai.get("reachable")), **{k:v for k,v in ai.items() if k != "reachable"}}, "speech":{"ok":speech.engine() != "mock", "engine":speech.engine()}, "ocr":{"ok":ocr.engine() != "mock", "engine":ocr.engine(), **({"hints": ocr.hints()} if ocr.hints() else {})}, "translation":{"ok":translate.mode() == "api", "mode":translate.mode()}, "printer":{"ok":printer.available().get("configured",False), **printer.available()}, "hardware":{"mode":hardware.mode()}}
    return {"status":"ok" if db_ok and comps["ai_core"]["ok"] else ("degraded" if db_ok else "down"), "components":comps}

@router.get("/admin/logs", dependencies=[Depends(require_admin)])
def logs(limit: int = 100, level: str | None = None, conn=Depends(db_dep)):
    limit=max(1,min(limit,500)); rows=conn.execute("SELECT * FROM system_logs WHERE level=? ORDER BY id DESC LIMIT ?",(level,limit)) if level else conn.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT ?",(limit,)); return {"logs":[dict(r) for r in rows.fetchall()]}

@router.get("/admin/registrations", dependencies=[Depends(require_admin)])
def registrations(conn=Depends(db_dep)):
    rows=conn.execute("SELECT id,name,phone,address,profession,land_owned,land_area,society_name,registration_status,member_no,rfid_uid,fingerprint_id,created_at FROM users WHERE registration_status='pending' ORDER BY id").fetchall()
    return {"registrations":[dict(r) for r in rows]}

@router.post("/admin/registrations/{user_id}/approve", dependencies=[Depends(require_admin)])
def approve_registration(user_id:int, body:dict, conn=Depends(db_dep)):
    member_no=(body.get("member_no") or "").strip(); rfid=(body.get("rfid_uid") or "").strip(); fingerprint=body.get("fingerprint_id")
    if not member_no or not rfid: raise AppError(422,"approval_data_required","member_no and rfid_uid are required before approval.")
    try:
        conn.execute("UPDATE users SET member_no=?, rfid_uid=?, fingerprint_id=?, registration_status='approved', is_active=1 WHERE id=? AND registration_status='pending'", (member_no,rfid,fingerprint,user_id))
        if conn.total_changes == 0: raise AppError(404,"registration_not_found","Pending registration not found.")
    except AppError: raise
    except Exception as exc: raise AppError(409,"duplicate_login_id","RFID or fingerprint ID is already assigned.") from exc
    return {"ok":True,"user_id":user_id,"status":"approved"}

@router.post("/admin/users", dependencies=[Depends(require_admin)])
def add_user(body:dict, conn=Depends(db_dep)):
    name=(body.get("name") or "").strip()
    if not name: raise AppError(422,"name_required","name is required")
    try:
        cur=conn.execute("INSERT INTO users(name,member_no,society_name,preferred_language,rfid_uid,fingerprint_id,registration_status,is_active) VALUES (?,?,?,?,?,?,?,1)", (name,body.get("member_no"),body.get("society_name"),body.get("preferred_language","hi"),body.get("rfid_uid"),body.get("fingerprint_id"),"approved"))
    except Exception as exc: raise AppError(409,"duplicate_user","RFID or fingerprint id already registered.") from exc
    return {"id":cur.lastrowid}