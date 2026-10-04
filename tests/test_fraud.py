import pytest
import fraud

LIKELY = [
    "Congratulations! You have won Rs 25,00,000 in the lucky draw. Pay Rs 5,000 processing fee to claim your prize. Call 9876543210.",
    "Dear member your society account will be blocked today. Update KYC immediately at http://bit.ly/3xYz and share OTP received.",
    "Your loan of Rs 3 lakh is approved. Pay Rs 8,000 insurance fee to UPI id loan.dept@ybl to release the amount within 2 hours.",
    "आपका खाता बंद हो जाएगा। तुरंत अपना OTP बताएं।",
]
SUSPICIOUS_OR_WORSE = [
    "PM-KISAN installment pending. Download PMKISAN.apk and enter your Aadhaar and bank details to receive Rs 2000.",
    "Police case registered against you. Pay Rs 20,000 immediately to avoid arrest.",
    "Install AnyDesk so our officer can fix your subsidy.",
    "Your subsidy is ready. Claim at http://pmkisan-subsidy.in/claim",
]
GENUINE = [
    "Your instalment of Rs 1,200 for loan account ending 4417 is due on 5 November. Please pay at the society office or by cheque.",
    "Gram Sabha meeting on Sunday 10 AM at the panchayat office. All members are requested to attend.",
    "Loan processing fee of Rs 500 will be deducted from the sanctioned amount at disbursal.",
    "Dear member, never share your OTP with anyone. The society will never ask for it.",
    "Please bring your PIN code details and ration card to the office for address update.",
    "Details of the scheme are at https://pmkisan.gov.in",
    "Visit https://www.sunrisepacs.in for the society's loan form timings.",
]


@pytest.mark.parametrize("text", LIKELY)
def test_likely_fraud(text):
    assert fraud.analyze(text)["verdict"] == "likely_fraud", fraud.analyze(text)


@pytest.mark.parametrize("text", SUSPICIOUS_OR_WORSE)
def test_suspicious_or_worse(text):
    assert fraud.analyze(text)["verdict"] in ("suspicious", "likely_fraud"), fraud.analyze(text)


@pytest.mark.parametrize("text", GENUINE)
def test_genuine_messages_not_flagged(text):
    r = fraud.analyze(text)
    assert r["verdict"] in ("no_flags", "low_concern"), r["flags"]


def test_advice_only_when_risky_and_helpline_present():
    assert fraud.analyze(GENUINE[0])["advice"] == []
    assert any("1930" in a for a in fraud.analyze(LIKELY[0])["advice"])


def test_no_flags_note_is_cautious():
    assert "not prove" in fraud.analyze(GENUINE[1])["note"]
