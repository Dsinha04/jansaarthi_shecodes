import json

from fastapi import APIRouter, Depends

from .. import schemas
from ..db import db_dep, log_event
from ..errors import AppError
from ..security import current_session, new_session
from ..services import hardware


router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_dict(row):
    pending = []

    try:
        pending = json.loads(row["pending_schemes"] or "[]")
    except Exception:
        pending = []

    return {
        "id": row["id"],
        "name": row["name"],
        "member_no": row["member_no"],
        "society_name": row["society_name"],
        "preferred_language": row["preferred_language"],

        # Registration details
        "phone": row["phone"],
        "address": row["address"],
        "profession": row["profession"],

        # Land details
        "land_owned": (
            None
            if row["land_owned"] is None
            else bool(row["land_owned"])
        ),
        "land_area": row["land_area"],

        # Account status
        "registration_status": row["registration_status"],
        "is_active": bool(row["is_active"]),

        # Schemes
        "pending_schemes": pending,
    }


def _login(conn, user, method, language):
    sess = new_session(
        conn,
        user["id"] if user else None,
        method,
        language,
    )

    log_event(
        conn,
        "info",
        "auth",
        f"login {method}",
        f"user_id={user['id'] if user else None}",
    )

    return {
        "token": sess["token"],
        "expires_at": sess["expires_at"],
        "method": method,
        "language": language,
        "user": _user_dict(user) if user else None,
    }


@router.post("/register")
def register(
    body: schemas.RegistrationIn,
    conn=Depends(db_dep),
):
    cur = conn.execute(
        """
        INSERT INTO users(
            name,
            preferred_language,
            phone,
            address,
            profession,
            land_owned,
            land_area,
            society_name,
            registration_status,
            is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (
            body.name.strip(),
            body.language,
            body.phone,
            body.address.strip(),
            body.profession.strip(),
            int(body.land_owned),
            body.land_area,
            body.society_name,
            "pending",
        ),
    )

    log_event(
        conn,
        "info",
        "auth",
        "new registration",
        f"registration_id={cur.lastrowid}",
    )

    return {
        "registration_id": cur.lastrowid,
        "status": "pending",
        "message": (
            "Registration submitted. Login is disabled until "
            "an administrator assigns your member ID and login credentials."
        ),
    }


@router.post("/rfid")
def login_rfid(
    body: schemas.RfidLogin,
    conn=Depends(db_dep),
):
    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE rfid_uid=?
          AND is_active=1
          AND registration_status='approved'
        """,
        (body.uid,),
    ).fetchone()

    if not user:
        log_event(
            conn,
            "warn",
            "auth",
            "unknown rfid card",
            body.uid[:8] + "...",
        )
        conn.commit()

        raise AppError(
            401,
            "card_not_registered",
            "This card is not registered or is still awaiting approval.",
        )

    return _login(conn, user, "rfid", body.language)


@router.post("/fingerprint")
def login_fingerprint(
    body: schemas.FingerprintLogin,
    conn=Depends(db_dep),
):
    fid = hardware.scan_fingerprint(body.template_id)

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE fingerprint_id=?
          AND is_active=1
          AND registration_status='approved'
        """,
        (fid,),
    ).fetchone()

    if not user:
        raise AppError(
            401,
            "fingerprint_not_registered",
            "Fingerprint not recognised or account is not approved yet.",
        )

    return _login(conn, user, "fingerprint", body.language)


@router.post("/guest")
def login_guest(
    body: schemas.GuestLogin,
    conn=Depends(db_dep),
):
    return _login(
        conn,
        None,
        "guest",
        body.language,
    )


@router.get("/me")
def me(sess=Depends(current_session)):
    return {
        "method": sess["method"],
        "language": sess["language"],
        "expires_at": sess["expires_at"],
        "user": (
            None
            if sess["user_id"] is None
            else {
                "id": sess["user_id"],
                "name": sess["user_name"],
                "member_no": sess["member_no"],
                "society_name": sess["society_name"],
            }
        ),
    }


@router.get("/profile")
def profile(
    sess=Depends(current_session),
    conn=Depends(db_dep),
):
    if sess["user_id"] is None:
        raise AppError(
            403,
            "profile_requires_login",
            "A registered user account is required for the profile.",
        )

    user_row = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id=?
        """,
        (sess["user_id"],),
    ).fetchone()

    if not user_row:
        raise AppError(
            404,
            "user_not_found",
            "User profile could not be found.",
        )

    complaints = conn.execute(
        """
        SELECT
            id,
            reference,
            category,
            status,
            created_at,
            details
        FROM complaints
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 20
        """,
        (sess["user_id"],),
    ).fetchall()

    documents = conn.execute(
        """
        SELECT
            id,
            filename,
            created_at
        FROM scanned_documents
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 20
        """,
        (sess["user_id"],),
    ).fetchall()

    user = _user_dict(user_row)

    return {
        "user": user,

        "complaints": [
            dict(row)
            for row in complaints
        ],

        "pending_schemes": user["pending_schemes"],

        "owned_documents": [
            dict(row)
            for row in documents
        ],
    }


@router.put("/language")
def set_language(
    body: schemas.LanguageUpdate,
    sess=Depends(current_session),
    conn=Depends(db_dep),
):
    conn.execute(
        """
        UPDATE sessions
        SET language=?
        WHERE token=?
        """,
        (
            body.language,
            sess["token"],
        ),
    )

    return {
        "language": body.language
    }


@router.post("/logout")
def logout(
    sess=Depends(current_session),
    conn=Depends(db_dep),
):
    conn.execute(
        """
        UPDATE sessions
        SET ended_at=datetime('now')
        WHERE token=?
        """,
        (sess["token"],),
    )

    return {
        "ok": True
    }