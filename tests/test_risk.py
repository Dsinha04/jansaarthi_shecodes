import pathlib
import pytest
import risk

SAMPLES = pathlib.Path(__file__).parent / "sample_contracts"

EXPECT = {
    "loan_bad.txt": {"blank_signature", "variable_rate", "unilateral_change", "high_rate", "hidden_charges",
                     "prepayment_penalty", "blanket_lien", "immediate_recall", "waiver_rights"},
    "membership_bad.txt": {"unilateral_change", "forfeiture", "waiver_rights", "auto_deduction",
                           "auto_renew", "urgency_pressure"},
    "guarantor_bad.txt": {"unlimited_guarantee", "irrevocable_poa", "blank_cheques",
                          "retained_title_deeds", "compound_interest"},
    "dairy_bad.txt": {"tied_purchase", "auto_deduction", "penalty", "one_sided_arbitration",
                      "auto_renew", "unilateral_change"},
}


@pytest.mark.parametrize("name,expected", EXPECT.items())
def test_bad_contracts_are_caught(name, expected):
    r = risk.analyze((SAMPLES / name).read_text())
    found = {f["rule"] for f in r["findings"]}
    assert expected <= found, f"missed: {expected - found}"
    assert r["risk_level"] == "high"


def test_fair_contract_is_not_flagged_high():
    r = risk.analyze((SAMPLES / "loan_ok.txt").read_text())
    assert r["risk_level"] in ("none", "low"), [f["rule"] for f in r["findings"]]


def test_blank_field_and_numbered_clauses():
    r = risk.analyze("7. Amount: ______\n8. Rate: ______")
    assert "blank_fields" in {f["rule"] for f in r["findings"]}


def test_rs_abbreviation_does_not_split_clause():
    clauses = risk.split_clauses("Penal interest of Rs. 500 per month is charged. The member agrees.")
    assert clauses[0] == "Penal interest of Rs. 500 per month is charged."


def test_reasonable_rate_not_flagged():
    assert risk.analyze("Interest on the loan shall be 9% per annum, fixed for the term.")["risk_level"] == "none"


def test_findings_sorted_high_first():
    f = risk.analyze((SAMPLES / "loan_bad.txt").read_text())["findings"]
    order = [x["severity"] for x in f]
    assert order == sorted(order, key=lambda s: {"high": 0, "medium": 1, "low": 2}[s])
