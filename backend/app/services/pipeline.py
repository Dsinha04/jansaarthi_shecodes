"""Translate-in -> AI core -> translate-out, shared by all AI endpoints."""
from . import translate as tr

# string fields we translate back to the user's language
TRANSLATE_KEYS = {"answer", "explanation", "title", "detail", "note", "summary", "label",
                  "where_to_apply", "disclaimer", "advice", "exclusions", "documents"}
SKIP_KEYS = {"sources", "evidence", "clause", "match", "rule", "id", "source_url", "complaint_template"}


def to_english(text: str, lang: str) -> tuple[str, bool]:
    return tr.translate(text, lang, "en")


def localize(obj, lang: str, _cache=None):
    """Return (translated copy, all_ok). Only strings under TRANSLATE_KEYS are translated."""
    if lang == "en":
        return obj, True
    cache = {} if _cache is None else _cache
    ok = [True]

    def tstr(s):
        if s not in cache:
            out, good = tr.translate(s, "en", lang)
            cache[s] = out
            ok[0] = ok[0] and good
        return cache[s]

    def walk(o, translate_here=False):
        if isinstance(o, dict):
            return {k: (o[k] if k in SKIP_KEYS else walk(o[k], k in TRANSLATE_KEYS)) for k in o}
        if isinstance(o, list):
            return [walk(x, translate_here) for x in o]
        if isinstance(o, str) and translate_here:
            return tstr(o)
        return o
    result = walk(obj)
    return result, ok[0]
