import schemes
import grievance


def names(res):
    return {s["id"]: s["status"] for s in res["schemes"]}


def test_landowner_farmer():
    n = names(schemes.recommend({"owns_land": True, "occupation": ["farmer"]}))
    assert n == {"pm_kisan": "likely_eligible", "kcc": "likely_eligible", "pmfby": "likely_eligible"}


def test_tenant_not_eligible_for_pm_kisan_but_listed_on_request():
    p = {"owns_land": False, "occupation": ["tenant_farmer"]}
    assert "pm_kisan" not in names(schemes.recommend(p))
    assert names(schemes.recommend(p, include_not_eligible=True))["pm_kisan"] == "not_eligible"
    assert names(schemes.recommend(p))["kcc"] == "likely_eligible"


def test_unknown_profile_asks_to_check_details():
    n = names(schemes.recommend({"owns_land": None, "occupation": []}))
    assert set(n.values()) == {"check_details"}


def test_unverified_data_is_marked_and_note_present():
    r = schemes.recommend({"owns_land": True, "occupation": ["farmer"]})
    assert all(s["verified"] is False for s in r["schemes"]) and "not an official decision" in r["note"]


def test_best_matches_first():
    r = schemes.recommend({"owns_land": None, "occupation": ["farmer"]})
    order = [s["status"] for s in r["schemes"]]
    assert order == sorted(order, key=lambda s: ["likely_eligible", "check_details"].index(s))


def test_every_category_has_steps_and_template():
    for cat in grievance.CATEGORIES:
        g = grievance.guide(cat)
        assert len(g["steps"]) >= 4 and "Complaint regarding" in g["complaint_template"]
    assert len(grievance.guide("fraud_misappropriation")["steps"]) == 5
    assert "1930" in grievance.guide("fraud_misappropriation")["steps"][-1]["detail"]


def test_society_type_changes_registrar_and_template_fills():
    g = grievance.guide("loan_dispute", "multi_state", member_name="Ramesh", society_name="Sunrise PACS",
                        member_no="42", details="Extra Rs. 800 was deducted.")
    assert "Central Registrar" in g["steps"][2]["detail"]
    t = g["complaint_template"]
    assert "Ramesh" in t and "Sunrise PACS" in t and "42" in t and "800" in t


def test_no_invented_deadlines():
    text = " ".join(s["detail"] for s in grievance.guide("loan_dispute")["steps"])
    assert "days" not in text.lower()


def test_evidence_attached_when_engine_available(make_engine):
    g = grievance.guide("loan_dispute", engine=make_engine(min_score=0.1))
    assert g["evidence"] and g["evidence"][0]["file"] == "dummy_act.txt"
