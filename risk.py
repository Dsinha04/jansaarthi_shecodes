"""Rule-based contract risk detector (fast, offline, explainable). Works on English text."""
import re

SEV = {"high": 3, "medium": 2, "low": 1}

# (id, severity, regex, title, plain-language explanation)
RULES = [
    ("blank_signature", "high",
     r"(sign(ed|ing)?|thumb|signature|stamp)[^.\n]{0,60}(blank|incomplete|without (filling|date|amount))|blank\s+(paper|cheque|check|form|stamp)",
     "Blank signature / blank document",
     "Never sign or give a thumb impression on a blank or half-filled paper. It can be filled in later against you."),
    ("blank_fields", "medium",
     r"(amount|rate|interest|date|period)\s*[:\-]?\s*(_{3,}|\.{4,}|\[\s*\])",
     "Important field left empty",
     "Amount, rate or date is blank. Insist that every field is filled before you sign."),
    ("unilateral_change", "high",
     r"(society|bank|lender|lessor|management)[^.\n]{0,60}(may|can|reserves the right to)[^.\n]{0,40}(change|alter|modify|revise|amend|vary)[^.\n]{0,60}(without|at (its|their) (sole )?discretion)|(change|alter|modify|revise|amend|vary)[^.\n]{0,50}without\s+(prior\s+)?(notice|consent|intimation|informing|telling)",
     "One-sided change of terms",
     "The other party can change terms without your consent. Ask that changes need written notice and your agreement."),
    ("hidden_charges", "medium",
     r"(other|miscellaneous|additional|incidental|service|processing|administrative)\s+(charges|fees)[^.\n]{0,40}(as (applicable|decided|determined)|may be (levied|charged))",
     "Open-ended or hidden charges",
     "Charges are not fixed in writing. Ask for a full list of all fees with amounts."),
    ("penalty", "medium",
     r"penal(ty)?\s+(interest|charges?|rate)|liquidated damages|late (payment )?(fee|charge)",
     "Penalty clause",
     "Check the exact penalty amount, when it starts, and whether it is capped."),
    ("forfeiture", "high",
     r"forfeit|(deposit|shares?|security|collateral)[^.\n]{0,40}(shall|will|may)\s+(be\s+)?(confiscated|seized|appropriated|adjusted)",
     "Forfeiture of money, shares or deposit",
     "You may lose deposits, shares or security. Ask under what exact conditions this can happen."),
    ("waiver_rights", "high",
     r"waive[sd]?\s+(all\s+)?(his|her|their|your|the)?\s*(legal\s+)?(rights?|remedies|claims)|(no|not)\s+(right|entitled)\s+to\s+(approach|move|challenge|appeal)[^.\n]{0,30}(court|tribunal|registrar|authority)|final and binding[^.\n]{0,30}no appeal",
     "Giving up legal rights",
     "This clause takes away your right to complain or go to court. Do not accept it without legal advice."),
    ("one_sided_arbitration", "medium",
     r"sole\s+arbitrator[^.\n]{0,60}(appointed|nominated)\s+by\s+the\s+(society|bank|lender|management)",
     "Arbitrator chosen by the other party",
     "The arbitrator is picked by the society or lender, which may be unfair to you."),
    ("irrevocable_poa", "high",
     r"irrevocable\s+(power of attorney|authority|mandate)|power of attorney[^.\n]{0,40}irrevocable",
     "Irrevocable power of attorney",
     "This gives someone permanent control over your property or money. Very risky."),
    ("unlimited_guarantee", "high",
     r"(guarantor|surety)[^.\n]{0,80}(jointly and severally|unlimited|entire (outstanding|amount)|all dues)|guarantee[^.\n]{0,40}(continuing|unconditional)",
     "Heavy guarantor liability",
     "A guarantor may have to repay the whole loan if the borrower fails. Understand this before signing as guarantor."),
    ("blanket_lien", "high",
     r"(lien|charge|mortgage|hypothecat\w+)\s+(on|over)\s+(all|any)\s+(my|his|her|your|the borrower'?s)?\s*(assets|property|land|crops?|movable)",
     "Claim over all your assets",
     "The lender can claim all your assets, not only the financed one. Ask to limit it to the financed item."),
    ("blank_cheques", "high",
     r"(?=[^.\n]*\b(?:security|hand|give|submit|deposit|retain|hold|keep)\b)[^.\n]*\b(?:blank|undated|post[- ]?dated|signed)\b[^.\n]{0,30}\bcheques?\b",
     "Cheques held as security",
     "Signed or undated cheques can be misused. Give only cheques with the amount and date clearly agreed in writing."),
    ("immediate_recall", "medium",
     r"(recall|demand|call\s+back)[^.\n]{0,40}(entire|full|whole)[^.\n]{0,30}(immediately|on demand|at any time)|repayable\s+on\s+demand",
     "Loan can be recalled any time",
     "The full loan can be demanded at once. Ask for fixed repayment dates and a notice period."),
    ("auto_renew", "low",
     r"automatically\s+(renew|extend)|auto[- ]?renew|(renews?|extended?|renewed)\s+automatically",
     "Automatic renewal",
     "The agreement renews by itself. Note how and when you can cancel."),
    ("urgency_pressure", "low",
     r"sign\s+(immediately|today|now)|offer\s+(valid|expires)\s+(today|only)|no\s+time\s+to\s+read",
     "Pressure to sign quickly",
     "Genuine agreements allow time to read and ask questions. Take a copy home first."),
    ("variable_rate", "medium",
     r"interest[^.\n]{0,50}(?:as|at\s+such\s+rate\s+as)\s+(?:may\s+be\s+)?(?:decided|determined|fixed|notified|prescribed)\s+by\s+the\s+(?:board|society|management|committee|bank)",
     "Interest rate not fixed in writing",
     "The rate can be set later by the society. Ask for the exact rate, and whether it can change, written in the agreement."),
    ("prepayment_penalty", "medium",
     r"(?:prepayment|pre-payment|foreclosure|pre-closure|early\s+(?:closure|repayment))\s+(?:penalty|charges?|fees?)|(?:penalty|charges?|fees?)[^.\n]{0,40}(?:closed|repaid|closure)\s+early",
     "Charge for repaying early",
     "You may be charged for closing the loan early. Ask for this to be removed or clearly capped."),
    ("tied_purchase", "medium",
     r"(?:shall|must|will|agrees?\s+to)\s+(?:purchase|buy|procure)[^.\n]{0,60}\bonly\s+from\s+the\s+(?:society|bank|lender|management)",
     "Forced to buy only from the society",
     "You may have to buy inputs at the society's price even if cheaper options exist."),
    ("auto_deduction", "medium",
     r"(?:deduct|adjust|recover|set\s*off)[^.\n]{0,60}(?:from|against)[^.\n]{0,40}(?:milk\s+(?:bill|payment|proceeds)|sale\s+proceeds|produce|subsid(?:y|ies)|crop\s+payment)",
     "Dues taken from your milk, crop or subsidy payment",
     "Money can be cut from your payments without a separate consent. Ask for notice and a statement each time."),
    ("retained_title_deeds", "medium",
     r"(?:retain|hold|keep|withhold)[^.\n]{0,40}original\s+(?:title\s+)?(?:deeds?|documents?|papers?)|original\s+(?:title\s+)?(?:deeds?|documents?)[^.\n]{0,60}(?:retain|hold|keep)",
     "Original land papers kept by the society",
     "Take a written receipt for every original paper and a promise to return them when the loan is closed."),
    ("compound_interest", "medium",
     r"compound(?:ed|ing)?\s+(?:monthly|quarterly|daily|half[- ]yearly)|interest\s+on\s+interest",
     "Interest on interest",
     "Compounding makes the debt grow faster. Ask what the total repayment will be."),
]

_PCT = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*(?:%|percent|per\s*cent)")
_CTX = re.compile(r"penal|penalty|default|overdue|late", re.I)


_ABBR = re.compile(r"\b(Rs|No|Nos|Sr|Dr|Mr|Mrs|Sec|Art|approx|etc|i\.e|e\.g)\.\s+", re.I)


def split_clauses(text):
    text = _ABBR.sub(lambda m: m.group(0).rstrip() + "\x00", text)   # protect "Rs. 500", "Sec. 5"
    parts = re.split(r"\n+|(?<=[^\d\s][.;])\s+(?=[A-Z0-9(])", text)
    parts = [p.replace("\x00", " ").strip() for p in parts]
    return [p for p in parts if len(p) > 8]


def analyze(text):
    findings, seen = [], set()
    for clause in split_clauses(text):
        for rid, sev, pat, title, why in RULES:
            if re.search(pat, clause, re.I) and (rid, clause) not in seen:
                seen.add((rid, clause))
                findings.append({"rule": rid, "severity": sev, "title": title,
                                 "clause": clause, "explanation": why})
        for m in _PCT.finditer(clause):                       # very high penal interest
            if float(m.group(1)) >= 24 and _CTX.search(clause) and ("high_rate", clause) not in seen:
                seen.add(("high_rate", clause))
                findings.append({"rule": "high_rate", "severity": "high",
                                 "title": f"Very high rate ({m.group(1)}%)",
                                 "clause": clause,
                                 "explanation": "This penal or default rate is very high. Compare with the rate allowed under your society's bye-laws."})
    score = sum(SEV[f["severity"]] for f in findings)
    level = "high" if (score >= 6 or any(f["severity"] == "high" for f in findings)) else \
            "medium" if score >= 2 else "low"
    findings.sort(key=lambda f: -SEV[f["severity"]])
    return {"risk_level": level if findings else "none", "score": score, "findings": findings}
