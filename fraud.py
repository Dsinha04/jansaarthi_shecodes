"""Suspicious message / fake-notice checker (rule-based, offline, explainable).
Covers English plus a few common Hindi phrases. Absence of flags is NOT proof a message is genuine."""
import re

SEV = {"high": 3, "medium": 2, "low": 1}
_SHORT = r"(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|cutt\.ly|rb\.gy|is\.gd|shorturl\.at|wa\.me)"
_NEG = re.compile(r"\b(never|do not|don't|dont|will not|won't|not ask|beware|avoid)\b|कभी नहीं|मत ", re.I)
_SECRET = (r"\b(?:otp|cvv|mpin|upi\s*pin|atm\s*pin|password|passcode|pin(?!\s*-?\s*code))\b")

# (id, severity, regex, title, explanation, skip_if_sentence_is_a_warning)
RULES = [
    ("share_otp", "high",
     rf"(?:share|send|tell|give|provide|forward|enter|read out|batao|bataiye)[^.\n]{{0,40}}{_SECRET}"
     rf"|{_SECRET}[^.\n]{{0,30}}(?:share|send|tell|give|provide|forward|batao|बताएं|बताओ|भेजें|शेयर)|ओटीपी",
     "Asks for OTP / PIN / password",
     "No bank, society or government office will ever ask for your OTP, PIN or password.", True),
    ("advance_fee", "high",
     r"(?:pay|deposit|send|transfer|remit)[^.\n]{0,60}(?:processing|registration|release|clearance|insurance|handling|verification)\s+(?:fee|charges?)"
     r"|(?:pay|deposit|send|transfer)[^.\n]{0,40}\b(?:gst|tax|stamp duty|advance)\b[^.\n]{0,60}(?:release|receive|claim|get)[^.\n]{0,40}(?:loan|subsidy|grant|refund|prize|amount)"
     r"|प्रोसेसिंग\s*फीस\s*(?:जमा|भेज)",
     "Asks you to pay first to receive money",
     "Genuine loans, subsidies and refunds are not released after you send a 'fee' to a person or UPI ID.", False),
    ("prize_lottery", "high",
     r"\byou(?:'ve| have)\s+won\b|\blucky\s+draw\b|\blottery\b|\bjackpot\b|लॉटरी|इनाम\s*जीत",
     "Prize / lottery claim",
     "You cannot win a prize in a draw you never entered. This is a common scam.", False),
    ("arrest_threat", "high",
     r"\b(?:arrest|warrant|fir|jail|police case|legal action|court case|cbi)\b[^.\n]{0,80}\b(?:pay|immediately|today|within|avoid)\b"
     r"|\b(?:pay|immediately|within)\b[^.\n]{0,80}\b(?:arrest|warrant|jail|legal action)\b",
     "Threat of arrest or legal action to force payment",
     "Officials do not demand money by SMS or phone to avoid arrest.", False),
    ("apk_install", "high",
     r"\.apk\b|\b(?:install|download)\s+(?:this|the|our)\s+(?:app|apk)\b",
     "Asks you to install an app / APK",
     "Apps sent through messages can steal your bank details. Install only from the official app store.", True),
    ("remote_access", "high",
     r"\b(?:anydesk|teamviewer|quicksupport|rustdesk)\b",
     "Remote-access app mentioned",
     "Remote-access apps let a stranger control your phone and bank apps.", True),
    ("kyc_details", "medium",
     r"(?:share|send|enter|update|verify|submit|batao)[^.\n]{0,40}\b(?:aadhaar|aadhar|pan|account number|card number|bank details)\b",
     "Asks for ID or bank details",
     "Do not send Aadhaar, PAN or bank details through messages or links. Visit the office instead.", False),
    ("account_block", "medium",
     r"(?:account|card|membership|shares?|kyc|sim)[^.\n]{0,50}(?:will be|shall be|is being|has been|stands?)\s+(?:blocked|suspended|closed|frozen|deactivated|cancelled)"
     r"|(?:खाता|अकाउंट)[^.\n]{0,20}(?:बंद|ब्लॉक)",
     "Threat that your account will be blocked",
     "Scammers create fear so you act without thinking. Check with your society office directly.", False),
    ("personal_payment", "medium",
     r"\b[\w.\-]{2,}@(?:ok(?:axis|hdfcbank|icici|sbi)|ybl|ibl|axl|paytm|upi|apl|sbi|hdfcbank|icici|axisbank|pnb)\b"
     r"|(?:pay|send|transfer|gpay|phonepe|paytm)[^.\n]{0,40}\b[6-9]\d{9}\b",
     "Payment to a personal UPI ID or phone number",
     "Official dues are paid to the society's or government's registered account, not to a person's UPI or phone number.", False),
    ("shortened_link", "medium",
     rf"(?:https?://)?(?:www\.)?{_SHORT}/\S*",
     "Shortened link hides the real website",
     "Do not open shortened links in messages claiming to be official.", False),
    ("urgency", "low",
     r"\b(?:within|in)\s+\d+\s*(?:hours?|hrs?|minutes?|mins?)\b|\b(?:immediately|urgent(?:ly)?|last chance|today only|act now|final notice)\b|तुरंत",
     "Pressure to act quickly",
     "Genuine offices give time and written notice. Pressure is a warning sign.", False),
]

_URL = re.compile(r"(?:https?://|www\.)[^\s)>\"']+", re.I)
_OFFICIAL = re.compile(r"government|govt|ministry|nabard|rbi|registrar|pm[- ]?kisan|\bkisan\b|\bkcc\b|"
                       r"cooperative|society|sahakari|scheme|subsidy|yojana", re.I)
_LOOKALIKE = re.compile(r"kisan|subsid|(?<![a-z])gov(?![a-z])|nabard|(?<![a-z])rbi(?![a-z])|yojana|(?<![a-z])kcc(?![a-z])|pmfby|scheme")
_KYC = re.compile(r"\bkyc\b|\be-?kyc\b|re-?verification", re.I)

ADVICE = [
    "Do not share OTP, PIN or password with anyone, even if they say they are from the society or a bank.",
    "Do not click links or pay money. Verify using the phone number on your passbook or at the society office.",
    "If you already paid or shared details, call the cyber crime helpline 1930 and report at cybercrime.gov.in.",
]


def _sentence(text, m):
    start = max(text.rfind(c, 0, m.start()) for c in ".!?\n।") + 1
    ends = [i for i in (text.find(c, m.end()) for c in ".!?\n।") if i != -1]
    return text[start:(min(ends) if ends else len(text))]


def _host(url):
    u = re.sub(r"^https?://", "", url, flags=re.I).split("/")[0].split(":")[0].lower()
    return u[4:] if u.startswith("www.") else u


def analyze(text):
    flags = []
    for rid, sev, pat, title, why, warn_ok in RULES:
        for m in re.finditer(pat, text, re.I):
            if warn_ok and _NEG.search(_sentence(text, m)):
                continue                       # e.g. "Never share your OTP" is a safety warning, not a scam
            flags.append({"rule": rid, "severity": sev, "title": title,
                          "match": m.group(0)[:100], "explanation": why})
            break

    urls = _URL.findall(text)
    if urls and _KYC.search(text):
        flags.append({"rule": "kyc_link", "severity": "high", "title": "KYC update through a link",
                      "match": urls[0][:100],
                      "explanation": "KYC updates are done at the office or in the official app, not through message links."})
    if urls and _OFFICIAL.search(text):
        for u in urls:
            h = _host(u)
            if h.endswith((".gov.in", ".nic.in", ".gov")) or re.fullmatch(_SHORT, h) \
                    or any(f["rule"] == "shortened_link" for f in flags):
                continue
            lookalike = bool(_LOOKALIKE.search(h))        # e.g. pmkisan-subsidy.in, gov-india.in
            flags.append({"rule": "lookalike_link" if lookalike else "unofficial_link",
                          "severity": "high" if lookalike else "medium",
                          "title": "Website name imitates an official site" if lookalike
                                   else "Link claims to be official but is not a .gov.in / .nic.in address",
                          "match": u[:100],
                          "explanation": "Government websites end in .gov.in or .nic.in. Fake sites copy official names. Check the address carefully."})
            break

    score = sum(SEV[f["severity"]] for f in flags)
    highs = sum(f["severity"] == "high" for f in flags)
    if highs >= 2 or score >= 6:
        verdict = "likely_fraud"
    elif highs == 1 or score >= 3:
        verdict = "suspicious"
    elif flags:
        verdict = "low_concern"
    else:
        verdict = "no_flags"
    flags.sort(key=lambda f: -SEV[f["severity"]])
    return {"verdict": verdict, "score": score, "flags": flags,
            "advice": ADVICE if verdict in ("likely_fraud", "suspicious") else [],
            "note": "No flags does not prove a message is genuine. When in doubt, check at the society office."
                    if verdict == "no_flags" else None}
