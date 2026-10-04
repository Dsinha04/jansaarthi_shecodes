"""Translation. Modes: api (external/local IndicTrans2 server), passthrough (no translation).
auto = api if TRANSLATE_API_URL is set, else passthrough. Never raises: on failure returns the
original text and reports translated=False so the UI can say so."""
import httpx
from ..config import settings


def mode() -> str:
    m = settings.translate_mode
    if m == "auto":
        return "api" if settings.translate_api_url else "passthrough"
    return m


def translate(text: str, source: str, target: str) -> tuple[str, bool]:
    if not text or source == target:
        return text, True
    if mode() != "api" or not settings.translate_api_url:
        return text, False
    try:
        r = httpx.post(settings.translate_api_url, json={"text": text, "source": source, "target": target}, timeout=30.0)
        r.raise_for_status()
        out = r.json().get("text")
        return (out, True) if out else (text, False)
    except Exception:
        return text, False
