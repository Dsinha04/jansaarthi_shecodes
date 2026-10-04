"""Speech, document OCR/text extraction and translation endpoints."""
import re, uuid
from fastapi import APIRouter, Depends, File, Form, UploadFile
from ..config import SUPPORTED_LANGUAGES, settings
from .. import schemas
from ..errors import AppError
from ..db import db_dep
from ..security import current_session
from ..services import ocr, speech, translate
router = APIRouter(prefix="/api", tags=["media"])
async def _read_limited(f: UploadFile) -> bytes:
    limit = int(settings.max_upload_mb * 1024 * 1024); data = await f.read(limit + 1)
    if len(data) > limit: raise AppError(413, "file_too_large", f"File is larger than {settings.max_upload_mb:g} MB.")
    if not data: raise AppError(422, "empty_file", "The file is empty.")
    return data
def _lang(language: str) -> str:
    if language not in SUPPORTED_LANGUAGES: raise AppError(422, "bad_language", "Unsupported language.")
    return language
@router.post("/speech/transcribe")
async def transcribe(audio: UploadFile = File(...), language: str = Form("hi"), sess=Depends(current_session)):
    return speech.transcribe(await _read_limited(audio), _lang(language))
@router.post("/ocr/scan")
async def scan(file: UploadFile = File(...), language: str = Form("hi"), sess=Depends(current_session), conn=Depends(db_dep)):
    name = (file.filename or "scan").lower(); content = (file.content_type or "").lower()
    if not ocr.is_supported(name, content): raise AppError(415, "unsupported_document", "Please upload an image, PDF or DOCX document.")
    data = await _read_limited(file); result = ocr.read_document(data, _lang(language), name, content)
    folder = settings.data_dir / "scans"; folder.mkdir(parents=True, exist_ok=True)
    ext = re.sub(r"[^a-z0-9]", "", (name.rsplit(".", 1)[-1] if "." in name else "bin"))[:5] or "bin"; path = folder / f"{uuid.uuid4().hex}.{ext}"; path.write_bytes(data)
    cur = conn.execute("INSERT INTO scanned_documents(user_id, session_token, filename, file_path, language, text, ocr_engine) VALUES (?,?,?,?,?,?,?)", (sess["user_id"], sess["token"], (file.filename or "scan")[:120], str(path), language, result["text"], result["engine"]))
    return {"document_id": cur.lastrowid, **result}
@router.get("/ocr/documents")
def my_documents(sess=Depends(current_session), conn=Depends(db_dep)):
    col, val = ("user_id", sess["user_id"]) if sess["user_id"] is not None else ("session_token", sess["token"])   # guests have no user_id
    rows = conn.execute(f"SELECT id, filename, language, substr(text,1,200) AS preview, created_at FROM scanned_documents WHERE {col}=? ORDER BY id DESC LIMIT 20", (val,)).fetchall()
    return {"documents": [dict(r) for r in rows]}
@router.post("/translate")
def do_translate(body: schemas.TranslateIn, sess=Depends(current_session)):
    out, ok = translate.translate(body.text, body.source, body.target); return {"text": out, "translated": ok, "mode": translate.mode()}