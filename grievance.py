"""Step-by-step complaint guidance. The steps are a general template (no invented deadlines or fees).
If the knowledge base is available, matching official passages are attached as evidence."""

CATEGORIES = {
    "loan_dispute": ("a loan dispute", ["Loan sanction letter", "Loan account statement or passbook", "Receipts of every payment made"]),
    "wrong_charges": ("wrong or unexplained charges", ["Loan sanction letter showing agreed charges", "Statement showing the deduction", "Receipts"]),
    "membership_shares": ("membership or share capital", ["Membership certificate or share certificate", "Receipts for share money", "Resignation letter, if any"]),
    "management_election": ("management or election matters", ["Bye-laws", "Notice of the meeting or election", "Minutes, if available"]),
    "fraud_misappropriation": ("suspected fraud or misuse of funds", ["Statements and receipts", "Any messages or notices received", "Names and dates of the people involved"]),
    "other": ("a problem with my society", ["Any paper that relates to the problem"]),
}

REGISTRAR = {
    "state": "the Registrar of Cooperative Societies of your state",
    "multi_state": "the Central Registrar of Cooperative Societies (for multi-state cooperative societies)",
    "unknown": "the Registrar of Cooperative Societies. Your society's registration certificate or bye-laws show whether it is registered with the state Registrar or the Central Registrar",
}

TEMPLATE = """To,
The Secretary / Chairperson,
{society}

Subject: Complaint regarding {label}

Respected Sir / Madam,

I, {name}, a member of {society} (Member No. {member_no}), wish to bring the following matter to your notice:

{details}

I request you to examine this matter and reply to me in writing. Please give me an acknowledgment of this letter.

Date: ____________
Signature: ____________"""


def _evidence(engine, query):
    if engine is None:
        return []
    hits = [h for h in engine.retrieve(query, 3) if h["score"] >= engine.min_score]
    return [{"file": h["source"], "page": h.get("page"), "section": h.get("section"),
             "excerpt": h["text"][:300]} for h in hits]


def guide(category, society_type="unknown", member_name=None, society_name=None,
          member_no=None, details=None, engine=None):
    label, docs = CATEGORIES[category]
    steps = [
        {"n": 1, "title": "Collect your papers", "detail": "Keep copies of: " + "; ".join(docs) + "."},
        {"n": 2, "title": "Complain to the society in writing",
         "detail": "Give a written complaint to the Secretary or the managing committee. Ask for a stamped acknowledgment and keep your copy."},
        {"n": 3, "title": "Escalate to the Registrar",
         "detail": "If you get no reply or no fair answer, write to " + REGISTRAR[society_type] +
                   ". Attach your complaint, the acknowledgment and your papers."},
        {"n": 4, "title": "Ask about other forums",
         "detail": "Ask the Registrar's office whether an ombudsman, tribunal or arbitration route applies to your case."},
    ]
    if category == "fraud_misappropriation":
        steps.append({"n": 5, "title": "Report the crime",
                      "detail": "For fraud or cheating, report to the police. For online or UPI fraud call 1930 or use cybercrime.gov.in."})
    return {
        "category": category, "label": label, "steps": steps,
        "evidence": _evidence(engine, f"complaint procedure {label} cooperative society Registrar"),
        "complaint_template": TEMPLATE.format(
            society=society_name or "[Name of society]", label=label,
            name=member_name or "[Your name]", member_no=member_no or "______",
            details=details or "[Describe what happened, with dates and amounts]"),
        "note": "Time limits and fees depend on your state and Act. Confirm them with the Registrar's office.",
    }
