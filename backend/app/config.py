import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Load KEY=VALUE lines from backend/.env without overriding real environment variables.
    Inline comments ("VALUE   # note") are stripped and empty values are skipped."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if value[:1] in ("'", '"') and value[-1:] == value[:1] and len(value) > 1:
            value = value[1:-1]
        else:
            value = re.sub(r"(^|\s)#.*$", "", value).strip()
        if key.strip() and value:
            os.environ.setdefault(key.strip(), value)


_load_dotenv(ROOT / ".env")


def _env(name, default=""):
    return os.getenv(name, default)


class Settings:
    """Read at call time so tests can override environment variables."""

    @property
    def ai_core_url(self): return _env("AI_CORE_URL", "http://127.0.0.1:8001").rstrip("/")
    @property
    def ai_core_key(self): return _env("AI_CORE_KEY")
    @property
    def db_path(self): return Path(_env("DB_PATH", str(ROOT / "data" / "jansaarthi.db")))
    @property
    def data_dir(self): return self.db_path.parent
    @property
    def session_hours(self): return float(_env("SESSION_HOURS", "1"))
    @property
    def cors_origins(self): return [o.strip() for o in _env("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
    @property
    def hardware_mode(self): return _env("HARDWARE_MODE", "mock")
    @property
    def stt_mode(self): return _env("STT_MODE", "auto")
    @property
    def ocr_mode(self): return _env("OCR_MODE", "auto")
    @property
    def tesseract_cmd(self): return _env("TESSERACT_CMD")
    @property
    def ocr_api_url(self): return _env("OCR_API_URL") or _env("LLM_API_URL") or "https://api.openai.com/v1/chat/completions"
    @property
    def ocr_api_key(self): return _env("OCR_API_KEY") or _env("LLM_API_KEY")
    @property
    def ocr_model(self): return _env("OCR_MODEL") or _env("LLM_MODEL")      # must be a model that accepts images
    @property
    def ocr_token_param(self): return _env("OCR_TOKEN_PARAM") or _env("LLM_TOKEN_PARAM", "max_tokens")
    @property
    def ocr_timeout(self): return float(_env("OCR_TIMEOUT", "90"))
    @property
    def translate_mode(self): return _env("TRANSLATE_MODE", "auto")
    @property
    def translate_api_url(self): return _env("TRANSLATE_API_URL")
    @property
    def printer_name(self): return _env("PRINTER_NAME")
    @property
    def admin_key(self): return _env("ADMIN_KEY")
    @property
    def max_upload_mb(self): return float(_env("MAX_UPLOAD_MB", "10"))


settings = Settings()
SUPPORTED_LANGUAGES = ["en", "hi", "bn", "mr", "ta", "te", "gu", "pa"]