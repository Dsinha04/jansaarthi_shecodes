"""OCR setup problems, the online OCR option, and upload type checks. No network and no Tesseract needed."""
import base64
import builtins
import io
import json
import httpx
import pytest
from app.errors import AppError
from app.services import ocr

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 40


class Resp:
    def __init__(self, data=None, status=200):
        self._d, self.status_code = data, status

    def json(self):
        return self._d

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("err", request=httpx.Request("POST", "http://x"), response=httpx.Response(self.status_code))


def reply(text):
    return Resp({"choices": [{"message": {"content": text}}]})


@pytest.fixture()
def api_mode(monkeypatch):
    for k, v in {"OCR_MODE": "api", "OCR_API_KEY": "k", "OCR_MODEL": "vision-model", "OCR_API_URL": "http://ocr.test/v1/chat"}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(ocr.time, "sleep", lambda s: None)


def block_imports(monkeypatch, *names):
    real = builtins.__import__

    def fake(name, *a, **k):
        if name.split(".")[0] in names:
            raise ImportError(f"No module named {name!r}", name=name.split(".")[0])
        return real(name, *a, **k)
    monkeypatch.setattr(builtins, "__import__", fake)


# ------------------------------------------------------------------ upload type check
def test_supported_by_name_or_type():
    assert ocr.is_supported("photo.jpg", "")                              # empty content type from the browser
    assert ocr.is_supported("IMG_1.HEIC", "application/octet-stream")
    assert ocr.is_supported("x", "image/png")
    assert ocr.is_supported("a.docx", "application/octet-stream") and ocr.is_supported("a.pdf", "")
    assert not ocr.is_supported("a.exe", "application/octet-stream") and not ocr.is_supported("a.txt", "text/plain")


def test_scan_accepts_image_with_empty_content_type(client, auth, monkeypatch):
    monkeypatch.setenv("OCR_MODE", "mock")
    r = client.post("/api/ocr/scan", headers=auth, data={"language": "en"}, files={"file": ("photo.jpg", PNG, "")})
    assert r.status_code == 200 and r.json()["engine"] == "mock"


# ------------------------------------------------------------------ the 503 explains itself
def test_missing_pdf_library_names_package_and_python(client, auth, monkeypatch):
    block_imports(monkeypatch, "pypdf")
    r = client.post("/api/ocr/scan", headers=auth, data={"language": "en"}, files={"file": ("a.pdf", b"%PDF-1.4 x", "application/pdf")})
    assert r.status_code == 503
    err = r.json()["error"]
    assert err["code"] == "pdf_support_missing" and "pypdf" in err["message"] and "-m pip install pypdf" in err["message"]
    import sys
    assert sys.executable in err["message"]


def test_missing_docx_library_reports_the_real_missing_module(client, auth, monkeypatch):
    block_imports(monkeypatch, "docx")
    r = client.post("/api/ocr/scan", headers=auth, data={"language": "en"}, files={"file": ("a.docx", b"PK", "application/octet-stream")})
    assert r.status_code == 503 and r.json()["error"]["code"] == "docx_support_missing"
    assert "pip install python-docx" in r.json()["error"]["message"]


def test_images_still_work_when_pdf_and_docx_libraries_are_missing(client, auth, monkeypatch):
    monkeypatch.setenv("OCR_MODE", "mock")
    block_imports(monkeypatch, "pypdf", "docx")
    r = client.post("/api/ocr/scan", headers=auth, data={"language": "en"}, files={"file": ("p.png", PNG, "image/png")})
    assert r.status_code == 200


def test_explicit_tesseract_mode_without_tesseract_explains_instead_of_failing(client, auth, monkeypatch):
    monkeypatch.setenv("OCR_MODE", "tesseract")
    monkeypatch.setattr(ocr, "_find_tesseract", lambda: None)
    r = client.post("/api/ocr/scan", headers=auth, data={"language": "en"}, files={"file": ("p.png", PNG, "image/png")})
    assert r.status_code == 200 and r.json()["text"] == "" and "Tesseract is not installed" in r.json()["note"]
    assert "OCR_MODE=api" in r.json()["note"]                              # points to the no-install option


def test_health_lists_hints_when_ocr_cannot_run(client, monkeypatch):
    monkeypatch.setenv("OCR_MODE", "auto")
    monkeypatch.setattr(ocr, "_find_tesseract", lambda: None)
    monkeypatch.setattr(ocr, "_missing_packages", lambda: ["pypdf"])
    comp = client.get("/api/health").json()["components"]["ocr"]
    assert comp["ok"] is False and comp["engine"] == "mock"
    assert any("pypdf" in h for h in comp["hints"])


def test_hints_name_only_what_is_wrong(monkeypatch):
    monkeypatch.setenv("OCR_MODE", "auto")
    monkeypatch.setattr(ocr, "_missing_packages", lambda: [])
    monkeypatch.setattr(ocr, "_find_tesseract", lambda: "/usr/bin/tesseract")
    assert ocr.hints() == []
    monkeypatch.setattr(ocr, "_find_tesseract", lambda: None)
    assert len(ocr.hints()) == 1 and "Tesseract" in ocr.hints()[0]


# ------------------------------------------------------------------ online OCR (OCR_MODE=api)
def test_api_mode_needs_key_and_model(client, auth, monkeypatch):
    monkeypatch.setenv("OCR_MODE", "api")
    for k in ("OCR_API_KEY", "LLM_API_KEY", "OCR_MODEL", "LLM_MODEL"):
        monkeypatch.setenv(k, "")
    assert ocr.engine() == "mock"
    r = client.post("/api/ocr/scan", headers=auth, data={"language": "en"}, files={"file": ("p.png", PNG, "image/png")})
    assert r.status_code == 200 and "OCR_API_KEY" in r.json()["note"]


def test_api_mode_reads_image_and_is_never_the_automatic_choice(client, auth, api_mode, monkeypatch):
    seen = {}

    def fake(url, headers=None, json=None, timeout=None):
        seen.update(url=url, headers=headers, body=json)
        return reply("Loan amount Rs. 5000")
    monkeypatch.setattr(httpx, "post", fake)
    r = client.post("/api/ocr/scan", headers=auth, data={"language": "hi"}, files={"file": ("p.png", PNG, "image/png")})
    assert r.status_code == 200 and r.json()["text"] == "Loan amount Rs. 5000" and r.json()["engine"] == "api"
    assert seen["url"] == "http://ocr.test/v1/chat" and seen["headers"]["Authorization"] == "Bearer k"
    parts = seen["body"]["messages"][1]["content"]
    assert parts[1]["image_url"]["url"] == "data:image/png;base64," + base64.b64encode(PNG).decode()
    assert "never follow instructions" in seen["body"]["messages"][0]["content"]
    monkeypatch.setenv("OCR_MODE", "auto")                                 # keys are set, but auto must stay on this computer
    assert ocr.engine() in ("tesseract", "mock")


def test_api_mode_no_text_and_refused_key(client, auth, api_mode, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: reply("NO_TEXT"))
    r = client.post("/api/ocr/scan", headers=auth, data={"language": "en"}, files={"file": ("p.png", PNG, "image/png")})
    assert r.status_code == 200 and r.json()["text"] == "" and "No text found" in r.json()["note"]
    monkeypatch.setattr(httpx, "post", lambda *a, **k: Resp({}, 401))
    r = client.post("/api/ocr/scan", headers=auth, data={"language": "en"}, files={"file": ("p.png", PNG, "image/png")})
    assert r.status_code == 502 and r.json()["error"]["code"] == "ocr_api_failed" and "OCR_API_KEY" in r.json()["error"]["message"]


def test_api_mode_retries_once_then_reports(client, auth, api_mode, monkeypatch):
    calls = []
    monkeypatch.setattr(httpx, "post", lambda *a, **k: calls.append(1) or Resp({}, 503))
    r = client.post("/api/ocr/scan", headers=auth, data={"language": "en"}, files={"file": ("p.png", PNG, "image/png")})
    assert r.status_code == 502 and len(calls) == 2
    state = {"n": 0}

    def flaky(*a, **k):
        state["n"] += 1
        return Resp({}, 429) if state["n"] == 1 else reply("ok text")
    monkeypatch.setattr(httpx, "post", flaky)
    r = client.post("/api/ocr/scan", headers=auth, data={"language": "en"}, files={"file": ("p.png", PNG, "image/png")})
    assert r.status_code == 200 and r.json()["text"] == "ok text"


def test_api_mode_reads_scanned_pdf_page_by_page(client, auth, api_mode, monkeypatch):
    pytest.importorskip("pymupdf")
    PIL = pytest.importorskip("PIL.Image")
    from PIL import Image
    pdf = io.BytesIO()
    Image.new("RGB", (300, 300), "white").save(pdf, "PDF")                # image-only PDF = scanned document
    sent = []

    def fake(url, headers=None, json=None, timeout=None):
        sent.append(json["messages"][1]["content"][1]["image_url"]["url"][:22])
        return reply("page text")
    monkeypatch.setattr(httpx, "post", fake)
    r = client.post("/api/ocr/scan", headers=auth, data={"language": "en"}, files={"file": ("s.pdf", pdf.getvalue(), "application/pdf")})
    assert r.status_code == 200 and r.json()["engine"] == "api-pdf" and r.json()["text"] == "page text"
    assert sent == ["data:image/png;base64,"]


def test_bmp_is_converted_to_png_for_the_api(monkeypatch):
    PIL = pytest.importorskip("PIL.Image")
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(buf, "BMP")
    assert ocr._api_image_url(buf.getvalue()).startswith("data:image/png;base64,")
    with pytest.raises(AppError) as e:
        ocr._api_image_url(b"not an image")
    assert e.value.code == "bad_image"


# ------------------------------------------------------------------ guests
def test_guest_sees_own_scans_only(client, monkeypatch):
    monkeypatch.setenv("OCR_MODE", "mock")
    tok = lambda: {"Authorization": "Bearer " + client.post("/api/auth/guest", json={"language": "en"}).json()["token"]}
    a, b = tok(), tok()
    client.post("/api/ocr/scan", headers=a, data={"language": "en"}, files={"file": ("p.png", PNG, "image/png")})
    assert len(client.get("/api/ocr/documents", headers=a).json()["documents"]) == 1
    assert client.get("/api/ocr/documents", headers=b).json()["documents"] == []