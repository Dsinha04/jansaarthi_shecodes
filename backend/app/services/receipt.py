"""Plain-text receipts (32 columns, suits 58 mm thermal printers)."""
import textwrap
from datetime import datetime

W = 32
LINE = "-" * W


def _wrap(s: str) -> list[str]:
    out = []
    for para in (s or "").splitlines() or [""]:
        out += textwrap.wrap(para, W) or [""]
    return out


def build(title: str, lines: list[str], reference: str | None = None, footer: str | None = None) -> str:
    parts = ["JANSAARTHI".center(W), title.center(W), LINE]
    if reference:
        parts += [f"Ref: {reference}"]
    parts += [datetime.now().strftime("%d-%m-%Y %H:%M"), LINE]
    for l in lines:
        parts += _wrap(l)
    parts += [LINE]
    if footer:
        parts += _wrap(footer)
    parts += ["", "Thank you".center(W), ""]
    return "\n".join(parts)
