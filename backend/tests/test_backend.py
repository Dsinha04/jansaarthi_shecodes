import pytest
import io
from app.errors import AppError


def test_health_degraded_without_ai(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["components"]["database"]["ok"] is True
    assert r.json()["status"] == "degraded"       # AI core not running in tests


def test_login_rfid_ok_and_unknown(client):
    ok = client.post("/api/auth/rfid", json={"uid": "DEMO0001", "language": "hi"})
    assert ok.status_code == 200 and ok.json()["user"]["member_no"] == "42"
    bad = client.post("/api/auth/rfid", json={"uid": "NOPE123"})
    assert bad.status_code == 401 and bad.json()["error"]["code"] == "card_not_registered"


def test_login_validation(client):
    r = client.post("/api/auth/rfid", json={"uid": "x"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    r = client.post("/api/auth/guest", json={"language": "xx"})
    assert r.status_code == 422


def test_fingerprint_and_guest(client):
    r = client.post("/api/auth/fingerprint", json={"template_id": 2})
    assert r.status_code == 200 and r.json()["user"]["member_no"] == "108"
    assert client.post("/api/auth/fingerprint", json={"template_id": 99}).status_code == 401
    assert client.post("/api/auth/guest", json={"language": "en"}).json()["user"] is None


def test_protected_routes_need_token(client):
    for method, path in [("get", "/api/auth/me"), ("get", "/api/history"), ("post", "/api/ai/ask")]:
        r = getattr(client, method)(path)
        assert r.status_code == 401
    assert client.get("/api/history", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_logout_invalidates(client, auth):
    assert client.get("/api/auth/me", headers=auth).status_code == 200
    client.post("/api/auth/logout", headers=auth)
    assert client.get("/api/auth/me", headers=auth).status_code == 401


def test_session_expiry(client, auth, monkeypatch):
    from app.db import get_conn
    with get_conn() as c:
        c.execute("UPDATE sessions SET expires_at='2000-01-01 00:00:00'")
    r = client.get("/api/auth/me", headers=auth)
    assert r.status_code == 401 and r.json()["error"]["code"] == "session_expired"


def test_ask_saves_history_and_echoes_language(client, auth, fake_ai):
    r = client.post("/api/ai/ask", json={"text": "How do I complain?", "language": "hi"}, headers=auth)
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "full" and body["conversation_id"]
    assert body["translation_ok"] is False          # passthrough mode: honest flag
    h = client.get("/api/history", headers=auth).json()["items"]
    assert len(h) == 1 and h[0]["kind"] == "ask"
    assert client.get(f"/api/history/{body['conversation_id']}", headers=auth).json()["result"]["grounded"]


def test_history_is_private_between_guests(client, fake_ai):
    a = {"Authorization": "Bearer " + client.post("/api/auth/guest", json={}).json()["token"]}
    b = {"Authorization": "Bearer " + client.post("/api/auth/guest", json={}).json()["token"]}
    cid = client.post("/api/ai/ask", json={"text": "hello there"}, headers=a).json()["conversation_id"]
    assert client.get("/api/history", headers=b).json()["items"] == []
    assert client.get(f"/api/history/{cid}", headers=b).status_code == 404


def test_ai_unreachable_gives_503(client, auth, monkeypatch):
    def boom(*a, **k):
        raise AppError(503, "ai_unavailable", "down")
    monkeypatch.setattr("app.services.ai_client.call", boom)
    r = client.post("/api/ai/ask", json={"text": "hello there"}, headers=auth)
    assert r.status_code == 503 and r.json()["error"]["code"] == "ai_unavailable"


def test_other_ai_endpoints(client, auth, fake_ai):
    assert client.post("/api/ai/notice", json={"text": "Share OTP now"}, headers=auth).json()["verdict"] == "likely_fraud"
    assert client.post("/api/ai/schemes", json={"owns_land": True, "occupation": ["farmer"]},
                       headers=auth).json()["schemes"][0]["id"] == "pm"
    assert client.post("/api/ai/contract", json={"text": "x" * 20}, headers=auth).json()["risk_level"] == "high"
    assert client.post("/api/ai/schemes", json={"occupation": ["astronaut"]}, headers=auth).status_code == 422


def test_complaint_flow_and_print(client, auth, fake_ai):
    r = client.post("/api/complaints", json={"category": "loan_dispute", "details": "Extra 800 deducted"}, headers=auth)
    assert r.status_code == 200
    c = r.json()
    assert c["reference"].startswith("JS-")
    assert "Ramesh Kumar" in c["letter_english"]            # member name defaulted from the login
    assert client.get("/api/complaints", headers=auth).json()["complaints"][0]["id"] == c["id"]
    pv = client.post("/api/receipt/preview", json={"kind": "complaint", "complaint_id": c["id"]}, headers=auth)
    assert "COMPLAINT" in pv.json()["receipt"]
    p = client.post("/api/print", json={"kind": "complaint", "complaint_id": c["id"]}, headers=auth).json()
    assert p["printed"] is False and p["reason"] == "no_printer_configured"
    assert client.get(f"/api/complaints/{c['id']}", headers=auth).json()["status"] == "printed"


def test_complaint_not_visible_to_others(client, auth, fake_ai):
    cid = client.post("/api/complaints", json={"category": "other"}, headers=auth).json()["id"]
    other = {"Authorization": "Bearer " + client.post("/api/auth/guest", json={}).json()["token"]}
    assert client.get(f"/api/complaints/{cid}", headers=other).status_code == 404
    assert client.post("/api/print", json={"kind": "complaint", "complaint_id": cid}, headers=other).status_code == 404


def test_print_answer(client, auth, fake_ai):
    cid = client.post("/api/ai/ask", json={"text": "How do I complain?"}, headers=auth).json()["conversation_id"]
    r = client.post("/api/receipt/preview", json={"kind": "answer", "conversation_id": cid}, headers=auth)
    assert "Complain in writing" in r.json()["receipt"]
    assert client.post("/api/print", json={"kind": "answer"}, headers=auth).status_code == 422


def test_ocr_mock_and_validation(client, auth):
    png = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 50)
    r = client.post("/api/ocr/scan", files={"file": ("a.png", png, "image/png")}, data={"language": "hi"}, headers=auth)
    assert r.status_code == 200 and r.json()["engine"] == "mock" and r.json()["document_id"]
    r = client.post("/api/ocr/scan", files={"file": ("a.txt", io.BytesIO(b"hi"), "text/plain")}, headers=auth)
    assert r.status_code == 415
    assert len(client.get("/api/ocr/documents", headers=auth).json()["documents"]) == 1


def test_upload_size_limit(client, auth, monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "0.0001")
    r = client.post("/api/ocr/scan", files={"file": ("a.png", io.BytesIO(b"0" * 5000), "image/png")}, headers=auth)
    assert r.status_code == 413


def test_speech_mock(client, auth):
    r = client.post("/api/speech/transcribe", files={"audio": ("a.webm", io.BytesIO(b"1234"), "audio/webm")},
                    data={"language": "hi"}, headers=auth)
    assert r.status_code == 200 and r.json()["engine"] == "mock" and r.json()["text"] == ""


def test_translate_passthrough_and_api(client, auth, monkeypatch):
    r = client.post("/api/translate", json={"text": "hello", "source": "en", "target": "hi"}, headers=auth).json()
    assert r["text"] == "hello" and r["translated"] is False
    monkeypatch.setenv("TRANSLATE_MODE", "api")
    monkeypatch.setenv("TRANSLATE_API_URL", "http://x/t")
    monkeypatch.setattr("httpx.post", lambda *a, **k: type("R", (), {"raise_for_status": lambda s: None,
                                                                      "json": lambda s: {"text": "नमस्ते"}})())
    r = client.post("/api/translate", json={"text": "hello", "source": "en", "target": "hi"}, headers=auth).json()
    assert r["text"] == "नमस्ते" and r["translated"] is True


def test_admin_endpoints(client):
    assert client.get("/api/admin/logs").status_code == 401
    ok = client.get("/api/admin/logs", headers={"X-Admin-Key": "adm"})
    assert ok.status_code == 200
    r = client.post("/api/admin/users", json={"name": "New", "rfid_uid": "DEMO0001"}, headers={"X-Admin-Key": "adm"})
    assert r.status_code == 409
    r = client.post("/api/admin/users", json={"name": "New", "rfid_uid": "NEW0001"}, headers={"X-Admin-Key": "adm"})
    assert r.status_code == 200


def test_logs_record_unknown_card(client):
    client.post("/api/auth/rfid", json={"uid": "BAD0001"})
    logs = client.get("/api/admin/logs", headers={"X-Admin-Key": "adm"}).json()["logs"]
    assert any(l["message"] == "unknown rfid card" for l in logs)


# ---- profile update (needs admin approval) ----
ADM = {"X-Admin-Key": "adm"}


def test_profile_update_needs_admin_approval(client, auth):
    r = client.post("/api/auth/profile/update-request", json={"phone": "9876543210", "profession": "Dairy farmer"}, headers=auth)
    assert r.status_code == 200 and r.json()["status"] == "pending"
    rid = r.json()["request_id"]
    p = client.get("/api/auth/profile", headers=auth).json()
    assert p["user"]["profession"] == "Farmer"                      # not applied yet
    assert p["update_request"]["status"] == "pending" and p["update_request"]["changes"]["phone"] == "9876543210"
    # second request while one is pending is refused
    again = client.post("/api/auth/profile/update-request", json={"address": "New village road"}, headers=auth)
    assert again.status_code == 409 and again.json()["error"]["code"] == "update_already_pending"
    # admin sees current + requested, approves
    lst = client.get("/api/admin/profile-updates", headers=ADM).json()["requests"]
    assert lst[0]["id"] == rid and lst[0]["current"]["profession"] == "Farmer"
    assert client.post(f"/api/admin/profile-updates/{rid}/approve", headers=ADM, json={}).status_code == 200
    p = client.get("/api/auth/profile", headers=auth).json()
    assert p["user"]["profession"] == "Dairy farmer" and p["user"]["phone"] == "9876543210"
    assert p["update_request"]["status"] == "approved"
    assert client.post(f"/api/admin/profile-updates/{rid}/approve", headers=ADM, json={}).status_code == 404


def test_profile_update_reject_and_validation(client, auth):
    assert client.post("/api/auth/profile/update-request", json={"profession": "Farmer"}, headers=auth).json()["error"]["code"] == "no_changes"
    assert client.post("/api/auth/profile/update-request", json={"phone": "12ab"}, headers=auth).status_code == 422
    rid = client.post("/api/auth/profile/update-request", json={"land_owned": False}, headers=auth).json()["request_id"]
    assert client.post(f"/api/admin/profile-updates/{rid}/reject", headers=ADM, json={"note": "Bring land papers"}).status_code == 200
    p = client.get("/api/auth/profile", headers=auth).json()
    assert p["user"]["land_owned"] is True and p["user"]["land_area"] == "2 acres"
    assert p["update_request"]["status"] == "rejected" and p["update_request"]["admin_note"] == "Bring land papers"
    # after a decision the member can submit again
    assert client.post("/api/auth/profile/update-request", json={"land_owned": False}, headers=auth).status_code == 200


def test_profile_update_admin_and_guest_guards(client):
    assert client.get("/api/admin/profile-updates").status_code == 401
    g = client.post("/api/auth/guest", json={"language": "en"}).json()["token"]
    r = client.post("/api/auth/profile/update-request", json={"phone": "9876543210"}, headers={"Authorization": f"Bearer {g}"})
    assert r.status_code == 403


# ---- document scanning ----
def _tesseract_ready():
    from app.services import ocr
    return ocr._setup_problem() is None


def test_scan_docx_and_bad_type(client, auth):
    import io
    docx = pytest.importorskip("docx")
    d = docx.Document(); d.add_paragraph("Loan agreement. Interest 24 percent per year."); buf = io.BytesIO(); d.save(buf)
    r = client.post("/api/ocr/scan", headers=auth, data={"language": "en"},
                    files={"file": ("a.docx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
    assert r.status_code == 200 and "Loan agreement" in r.json()["text"]
    bad = client.post("/api/ocr/scan", headers=auth, data={"language": "en"}, files={"file": ("a.exe", b"x", "application/octet-stream")})
    assert bad.status_code == 415


def test_scan_image_and_scanned_pdf(client, auth, monkeypatch):
    import io
    PIL = pytest.importorskip("PIL.Image"); pytest.importorskip("fitz")
    if not _tesseract_ready():
        pytest.skip("tesseract not installed")
    monkeypatch.setenv("OCR_MODE", "auto")
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (1200, 300), "white"); dr = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("DejaVuSans.ttf", 60)
    except OSError: font = ImageFont.load_default()
    dr.text((40, 100), "Sign only after reading", fill="black", font=font)
    buf = io.BytesIO(); img.save(buf, "PNG")
    r = client.post("/api/ocr/scan", headers=auth, data={"language": "en"}, files={"file": ("p.png", buf.getvalue(), "image/png")})
    assert r.status_code == 200 and "reading" in r.json()["text"].lower()
    pdf = io.BytesIO(); img.save(pdf, "PDF")                      # image-only PDF = scanned document
    r = client.post("/api/ocr/scan", headers=auth, data={"language": "en"}, files={"file": ("s.pdf", pdf.getvalue(), "application/pdf")})
    assert r.status_code == 200 and "reading" in r.json()["text"].lower() and r.json()["engine"] == "tesseract-pdf"


def test_scan_without_ocr_explains_setup(client, auth, monkeypatch):
    import io
    monkeypatch.setenv("OCR_MODE", "mock")
    from PIL import Image
    buf = io.BytesIO(); Image.new("RGB", (50, 50), "white").save(buf, "PNG")
    r = client.post("/api/ocr/scan", headers=auth, data={"language": "en"}, files={"file": ("p.png", buf.getvalue(), "image/png")})
    assert r.status_code == 200 and r.json()["text"] == "" and "OCR is not set up" in r.json()["note"]