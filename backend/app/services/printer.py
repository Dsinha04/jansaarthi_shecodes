"""Printing. Always saves the receipt as a .txt under data/receipts, then sends to CUPS (lp) if a
printer is configured and `lp` exists."""
import shutil
import subprocess
from pathlib import Path
from ..config import settings


def print_text(name: str, text: str) -> dict:
    out_dir = settings.data_dir / "receipts"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.txt"
    path.write_text(text, encoding="utf-8")
    if not settings.printer_name:
        return {"printed": False, "saved": str(path), "reason": "no_printer_configured"}
    if shutil.which("lp") is None:
        return {"printed": False, "saved": str(path), "reason": "cups_not_installed"}
    try:
        subprocess.run(["lp", "-d", settings.printer_name, str(path)], check=True, timeout=20,
                       capture_output=True)
        return {"printed": True, "saved": str(path), "reason": None}
    except Exception:
        return {"printed": False, "saved": str(path), "reason": "print_failed"}


def available() -> dict:
    if not settings.printer_name:
        return {"configured": False}
    return {"configured": True, "name": settings.printer_name, "cups": shutil.which("lp") is not None}
