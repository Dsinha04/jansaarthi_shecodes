"""Speech-to-text. whisper (faster-whisper, offline) or mock. auto = whisper if installed."""
import tempfile
from pathlib import Path
from ..config import settings
from ..errors import AppError

_model = None


def _whisper_available() -> bool:
    try:
        import faster_whisper  # noqa: F401
        return True
    except ImportError:
        return False


def engine() -> str:
    m = settings.stt_mode
    if m == "auto":
        return "whisper" if _whisper_available() else "mock"
    return m


def transcribe(audio: bytes, language: str) -> dict:
    eng = engine()
    if eng == "mock":
        return {"text": "", "engine": "mock", "language": language,
                "note": "Speech engine not installed. Type your question instead."}
    global _model
    from faster_whisper import WhisperModel
    if _model is None:
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(audio)
        path = f.name
    try:
        segments, info = _model.transcribe(path, language=language if language != "auto" else None, vad_filter=True)
        text = " ".join(s.text.strip() for s in segments).strip()
    except Exception as exc:
        raise AppError(500, "stt_failed", "Could not understand the recording. Please try again.") from exc
    finally:
        Path(path).unlink(missing_ok=True)
    return {"text": text, "engine": "whisper", "language": info.language}
