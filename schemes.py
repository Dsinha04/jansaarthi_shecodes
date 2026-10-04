"""Scheme recommendation: transparent rule matching on the member's profile.
Scheme facts live in data/schemes.json and must be verified by the team. Nothing here decides eligibility officially."""
import json
import config

NOTE = "This is a guide, not an official decision. Confirm eligibility and dates with the scheme's official office."


def load_schemes(path=None):
    data = json.loads((path or config.SCHEMES_PATH).read_text(encoding="utf-8"))
    return data["schemes"]


def _check(rule, profile):
    """Return 'pass', 'fail' or 'unknown' for one rule."""
    value = profile.get(rule["field"])
    if value is None or value == []:
        return "unknown"
    op = rule["op"]
    if op == "eq":
        return "pass" if value == rule["value"] else "fail"
    if op == "any_of":
        have = value if isinstance(value, list) else [value]
        return "pass" if set(have) & set(rule["value"]) else "fail"
    if op == "truthy":
        return "pass" if value else "fail"
    return "unknown"


def recommend(profile, include_not_eligible=False, schemes=None):
    results = []
    for s in (schemes if schemes is not None else load_schemes()):
        checks = [{"label": r["label"], "result": _check(r, profile)} for r in s["rules"]]
        outcomes = {c["result"] for c in checks}
        status = "not_eligible" if "fail" in outcomes else \
                 "check_details" if "unknown" in outcomes else "likely_eligible"
        if status == "not_eligible" and not include_not_eligible:
            continue
        results.append({"id": s["id"], "name": s["name"], "summary": s["summary"], "status": status,
                        "checks": checks, "exclusions": s.get("exclusions", []),
                        "documents": s.get("documents", []), "where_to_apply": s.get("where_to_apply"),
                        "source_url": s.get("source_url"), "verified": s.get("verified", False)})
    order = {"likely_eligible": 0, "check_details": 1, "not_eligible": 2}
    results.sort(key=lambda r: order[r["status"]])
    return {"schemes": results, "note": NOTE}
