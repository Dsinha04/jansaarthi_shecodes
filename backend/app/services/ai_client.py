"""HTTP client for the AI Core (port 8001). English in, English out."""
import httpx
from ..config import settings
from ..errors import AppError


def _headers():
    return {"X-API-Key": settings.ai_core_key} if settings.ai_core_key else {}


def call(path: str, payload: dict, timeout: float = 90.0) -> dict:
    try:
        r = httpx.post(f"{settings.ai_core_url}{path}", json=payload, headers=_headers(), timeout=timeout)
    except httpx.HTTPError as exc:
        raise AppError(503, "ai_unavailable", "The AI service is not reachable right now.") from exc
    if r.status_code == 503:
        raise AppError(503, "knowledge_base_missing", "The knowledge base is not ready yet.")
    if r.status_code == 422:
        raise AppError(422, "ai_rejected_input", "The text was too short or too long. Please try again.")
    if r.status_code >= 400:
        raise AppError(502, "ai_error", "The AI service returned an error.")
    return r.json()


def health() -> dict:
    try:
        r = httpx.get(f"{settings.ai_core_url}/health", timeout=3.0)
        return {"reachable": True, **r.json()}
    except Exception:
        return {"reachable": False}
