# Jansaarthi AI Core: API Contract

Base URL (default): `http://<pi-ip>:8001`. All bodies are JSON. This service speaks **English only**.

## Language
The service does not translate. The backend sends **English text in** (after IndicTrans2 / OCR) and gets **English text out**, then translates the answer back. The optional `"language"` field (default `"en"`) is **echoed back unchanged** in every response so the caller knows which language to translate to.

## Security
- If the env var `AI_CORE_KEY` is set, every endpoint except `/health` needs the header `X-API-Key: <key>` (401 otherwise).
- If `CORS_ORIGINS` is set (comma-separated), browsers from those origins may call it directly. Otherwise call it from the backend.

## Every response (except /health) includes
`language`, `disclaimer` (show it to the user).

## Status codes
| Code | Meaning |
|---|---|
| 200 | OK (also when the LLM is down: see `mode`) |
| 401 | Missing or wrong `X-API-Key` |
| 422 | Invalid request (text too short or too long, unknown category, and so on) |
| 503 | Knowledge base not built yet. Run `python ingest.py` |

---
## GET /health
`{"ok": true, "index_ready": true, "llm_configured": true}`
`llm_configured: false` means answers will use `retrieval_only` mode.

## POST /ask
Request: `{"text": "<question, 2-1000 chars>", "language": "hi"}`

`mode` tells the frontend how to behave:

| mode | Meaning | What to show |
|---|---|---|
| `full` | AI answer from retrieved official passages. `grounded` is true if it cites a valid source `[n]` | The answer and the sources |
| `retrieval_only` | LLM unavailable (no internet, no key, API error) | The `sources` passages (offline-safe) and the message in `answer` |
| `no_evidence` | Nothing relevant in the documents | The `answer` text. Do not guess |

If `mode` is `full` but `grounded` is `false`, treat the answer as unverified (show the sources, or hide the answer).

Response:
```json
{
  "answer": "Give a written complaint to the Secretary first [1].",
  "sources": [
    {
      "n": 1,
      "file": "dummy_act.txt",
      "page": null,
      "section": "Section 6. Complaint to the Registrar",
      "score": 0.365,
      "excerpt": "to the Secretary and obtain a stamped acknowledgment. Section 6. Complaint to th..."
    }
  ],
  "mode": "full",
  "grounded": true,
  "top_score": 0.365,
  "language": "en",
  "disclaimer": "General information from official documents, not legal advice. Verify important decisions with your Registrar or a qualified professional."
}
```
`page` and `section` can be `null` (text files have no pages; headings may not be detected).

## POST /analyze-contract
Request: `{"text": "<contract text, 10-30000 chars>", "explain": false, "language": "en"}`
`explain: true` adds `legal_context` (same shape as an `/ask` response) to the top 3 findings. It uses the LLM, so it is slower. If the knowledge base is missing, flags are still returned and `explain_available` is `false`.

`risk_level`: `none` / `low` / `medium` / `high`. Findings are sorted most serious first.
```json
{
  "risk_level": "high",
  "score": 8,
  "findings": [
    {
      "rule": "blank_signature",
      "severity": "high",
      "title": "Blank signature / blank document",
      "clause": "1. Sign on blank stamp paper.",
      "explanation": "Never sign or give a thumb impression on a blank or half-filled paper. It can be filled in later against you."
    }
  ],
  "explain_available": false,
  "language": "en",
  "disclaimer": "General information from official documents, not legal advice. Verify important decisions with your Registrar or a qualified professional."
}
```

## POST /check-notice
Request: `{"text": "<SMS / notice text, 5-5000 chars>"}`
`verdict`: `likely_fraud` / `suspicious` / `low_concern` / `no_flags`. `advice` is filled for the first two.
```json
{
  "verdict": "likely_fraud",
  "score": 9,
  "flags": [
    {
      "rule": "share_otp",
      "severity": "high",
      "title": "Asks for OTP / PIN / password",
      "match": "share OTP",
      "explanation": "No bank, society or government office will ever ask for your OTP, PIN or password."
    },
    {
      "rule": "advance_fee",
      "severity": "high",
      "title": "Asks you to pay first to receive money",
      "match": "Pay Rs 5000 processing fee",
      "explanation": "Genuine loans, subsidies and refunds are not released after you send a 'fee' to a person or UPI ID."
    }
  ],
  "advice": [
    "Do not share OTP, PIN or password with anyone, even if they say they are from the society or a bank."
  ],
  "note": null,
  "language": "en",
  "disclaimer": "General information from official documents, not legal advice. Verify important decisions with your Registrar or a qualified professional."
}
```

## POST /schemes/recommend
Request: `{"owns_land": true, "occupation": ["farmer"], "is_society_member": true, "state": "Uttar Pradesh", "include_not_eligible": false}`
- `occupation` values: `farmer, tenant_farmer, sharecropper, dairy, fisher, poultry, shg_member, artisan, other`
- Missing fields are fine: the scheme then shows `check_details`.
- `status`: `likely_eligible` / `check_details` / `not_eligible` (the last is only returned if `include_not_eligible` is true).
- `verified: false` means the scheme data has not been checked by the team yet.
```json
{
  "schemes": [
    {
      "id": "pm_kisan",
      "name": "PM-KISAN",
      "summary": "Income support for landholding farmer families.",
      "status": "likely_eligible",
      "checks": [
        {
          "label": "Family owns cultivable land",
          "result": "pass"
        }
      ],
      "exclusions": [
        "Check the official exclusion list (for example institutional landholders, income tax payers, serving or retired government employees)."
      ],
      "documents": [
        "Aadhaar",
        "Land record",
        "Bank account details"
      ],
      "where_to_apply": "Common Service Centre, local agriculture office or the official portal",
      "source_url": "https://pmkisan.gov.in",
      "verified": false
    }
  ],
  "note": "This is a guide, not an official decision. Confirm eligibility and dates with the scheme's official office.",
  "language": "en",
  "disclaimer": "General information from official documents, not legal advice. Verify important decisions with your Registrar or a qualified professional."
}
```

## POST /grievance/guide
Request:
```json
{"category": "loan_dispute", "society_type": "state", "member_name": "Ramesh", "society_name": "Sunrise PACS", "member_no": "42", "details": "Extra Rs. 800 was deducted.", "language": "en"}
```
- `category`: `loan_dispute, wrong_charges, membership_shares, management_election, fraud_misappropriation, other`
- `society_type`: `state` / `multi_state` / `unknown` (default)
- Only `category` is required. `evidence` is empty when the knowledge base is not built.
```json
{
  "category": "loan_dispute",
  "label": "a loan dispute",
  "steps": [
    {
      "n": 1,
      "title": "Collect your papers",
      "detail": "Keep copies of: Loan sanction letter; Loan account statement or passbook; Receipts of every payment made."
    },
    {
      "n": 2,
      "title": "Complain to the society in writing",
      "detail": "Give a written complaint to the Secretary or the managing committee. Ask for a stamped acknowledgment and keep your copy."
    }
  ],
  "evidence": [
    {
      "file": "dummy_act.txt",
      "page": null,
      "section": "Section 6. Complaint to the Registrar",
      "excerpt": "to the Secretary and obtain a stamped acknowledgment. Sectio..."
    }
  ],
  "complaint_template": "(letter text with the member's details filled in)",
  "note": "Time limits and fees depend on your state and Act. Confirm them with the Registrar's office.",
  "language": "en",
  "disclaimer": "General information from official documents, not legal advice. Verify important decisions with your Registrar or a qualified professional."
}
```
