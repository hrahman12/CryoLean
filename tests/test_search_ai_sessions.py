"""Z3 search, AI matching, sessions, stale results, Lean unavailability."""
import pytest

from backend import config
from backend.ai_matching import ClaudeMatcher, match_request
from conftest import verify
from solver import z3_search

MR = "mat_magnetoresistance_10T"


# ------------------------------------------------------------------ Z3 search
def test_z3_finds_14T_and_lean_checks_each_candidate(client):
    s = client.post("/search", json={"experiment_id": MR}).json()
    ids = [e["candidate"]["configuration_id"] for e in s["verified_compatible"] + s["candidates_not_verified"]]
    assert "qd_dynacool_14T_eto_vsm_hc" in ids
    assert "qd_dynacool_9T_eto_res" not in ids                     # documented 9 T conflicts
    for e in s["verified_compatible"] + s["candidates_not_verified"]:
        assert e["lean"]["verified_by_lean"] is True
        assert e["candidate"]["verified"] == (e["lean"]["verdict"] == "ACCEPT")
        assert e["lean"]["configuration_id"] == (e["candidate"]["configuration_document"] or {}).get("id", e["candidate"]["configuration_id"])


def test_z3_hypothetical_option_is_lean_checked_as_its_own_document(client):
    # resistance experiment: the 12 T VSM-only DynaCool lacks ETO, an option the family offers
    s = client.post("/search", json={"experiment_id": "mat_electrical_resistance_low_temperature"}).json()
    hyp = [e for e in s["verified_compatible"] + s["candidates_not_verified"] if e["candidate"]["added_options"]]
    for e in hyp:
        assert "+" in e["lean"]["configuration_id"] and e["lean"]["hypothetical"] is True


def test_smt_proposing_an_invalid_setup_is_caught_by_lean(client, monkeypatch):
    """A (buggy or adversarial) solver proposes the 9 T configuration for a 10 T experiment."""
    real = z3_search.ConfigurationSearch.search

    def bad_search(self, experiment, **kw):
        res = real(self, experiment, **kw)
        res.candidates.insert(0, z3_search.Candidate(configuration_id="qd_dynacool_9T_eto_res",
                                                     equipment_id="qd_ppms_dynacool", kind="catalog"))
        return res
    monkeypatch.setattr(z3_search.ConfigurationSearch, "search", bad_search)
    s = client.post("/search", json={"experiment_id": MR}).json()
    bad = next(e for e in s["candidates_not_verified"] if e["candidate"]["configuration_id"] == "qd_dynacool_9T_eto_res")
    assert bad["lean"]["verdict"] == "REJECT" and bad["candidate"]["verified"] is False
    assert all(e["candidate"]["configuration_id"] != "qd_dynacool_9T_eto_res" for e in s["verified_compatible"])


def test_search_across_manufacturers_for_vector_field(client):
    s = client.post("/search", json={"experiment_id": "quantum_mk_vector_field_transport"}).json()
    assert s["smt_stats"]["configurations"] >= 20
    assert "note" in s and "not verified" in s["note"]


# ------------------------------------------------------------------ AI
@pytest.mark.parametrize("text,expected", [
    ("I want to test how electricity moves through a material when it's cold", "mat_electrical_resistance_low_temperature"),
    ("cut thin slices of frozen mouse brain", "bio_cryosection_frozen_tissue"),
    ("raman spectrum of a crystal at low temperature", "chem_low_temperature_raman"),
    ("measure magnetoresistance up to 10 tesla", MR),
])
def test_ai_matching(client, text, expected):
    r = client.post("/ai/match", json={"text": text}).json()
    assert r["matches"][0]["experiment_id"] == expected
    assert r["needs_confirmation"] is True and r["no_good_match"] is False


def test_ai_no_match_returns_no_profile(client):
    r = client.post("/ai/match", json={"text": "bake a cake"}).json()
    assert r["no_good_match"] is True


def test_ai_suggesting_invalid_setup(client, catalog):
    # 1. a model that invents an experiment id: discarded (closed set)
    class FakeResp:
        stop_reason = "end_turn"
        content = [type("B", (), {"type": "text", "text": '{"matches": [{"experiment_id": "invented_experiment", "confidence": 0.99, "reason": "x"},'
                                                          ' {"experiment_id": "chem_low_temperature_raman", "confidence": 0.7, "reason": "y"}]}'})()]

    class FakeClient:
        class beta:
            class messages:
                @staticmethod
                def create(**kw):
                    return FakeResp()
    m = ClaudeMatcher.__new__(ClaudeMatcher)
    m.catalog = catalog
    m.client = FakeClient()
    out = match_request(catalog, "raman", matcher=m)
    assert [x["experiment_id"] for x in out["matches"]] == ["chem_low_temperature_raman"]
    # 2. an AI-suggested configuration that does not exist: no verdict
    r = client.post("/verify", json={"experiment_id": MR, "configuration_id": "ppms_dynacool_20T_invented", "confirmed": True})
    assert r.status_code == 404 and "verdict" not in r.json()
    # 3. an AI-suggested real but incompatible setup: Lean rejects it
    assert verify(client, MR, "qd_dynacool_9T_eto_res")["verdict"] == "REJECT"


def test_requirements_cannot_be_weakened(client):
    sid = client.post("/sessions", json={"experiment_id": MR}).json()["id"]
    r = client.patch(f"/sessions/{sid}/requirements", json=[{"key": "magnetic_field.max", "mandatory": False}])
    assert r.status_code == 400
    r = client.patch(f"/sessions/{sid}/requirements", json=[{"key": "magnetic_field.max", "remove": True}])
    assert r.status_code == 400
    # editing a value is allowed but resets confirmation and marks the requirement user_entered
    r = client.patch(f"/sessions/{sid}/requirements", json=[{"key": "magnetic_field.max",
                                                             "constraint": {"kind": "at_least", "q": {"value": 12000, "unit": "mT"}}}])
    body = r.json()
    assert body["confirmed"] is False
    req = next(x for x in body["experiment"]["requirements"] if x["key"] == "magnetic_field.max")
    assert req["origin"] == "user_entered" and req["mandatory"] is True


# ------------------------------------------------------------------ sessions / stale results
def test_switching_machines_keeps_experiment_and_invalidates_result(client):
    sid = client.post("/sessions", json={"experiment_id": MR}).json()["id"]
    client.post(f"/sessions/{sid}/confirm")
    client.post(f"/sessions/{sid}/select-configuration", json={"configuration_id": "qd_dynacool_9T_eto_res"})
    r1 = client.post(f"/sessions/{sid}/verify").json()
    assert r1["verdict"] == "REJECT"
    assert client.get(f"/sessions/{sid}/result").json()["verdict"] == "REJECT"
    exp_before = client.get(f"/sessions/{sid}").json()["experiment"]
    client.post(f"/sessions/{sid}/select-configuration", json={"configuration_id": "qd_dynacool_14T_eto_vsm_hc"})
    stale = client.get(f"/sessions/{sid}/result")
    assert stale.status_code == 409 and stale.json()["verdict"] is None
    summary = client.get(f"/sessions/{sid}").json()
    assert summary["experiment"] == exp_before and summary["has_valid_result"] is False
    r2 = client.post(f"/sessions/{sid}/verify").json()
    assert r2["configuration_id"] == "qd_dynacool_14T_eto_vsm_hc" and r2["state_token"] != r1["state_token"]


def test_stale_result_rejected_after_requirement_edit_and_catalog_change(client):
    from backend.api import app
    sid = client.post("/sessions", json={"experiment_id": "bio_cryosection_frozen_tissue"}).json()["id"]
    client.post(f"/sessions/{sid}/confirm")
    client.post(f"/sessions/{sid}/select-configuration", json={"configuration_id": "leica_cm1950_genA_vacuum_motor_objcool"})
    assert client.post(f"/sessions/{sid}/verify").json()["verdict"] == "ACCEPT"
    # catalog version change => stored result no longer matches
    cat = app.state.catalog
    old = cat.version
    try:
        cat.version = old + "-changed"
        assert client.get(f"/sessions/{sid}/result").status_code == 409
    finally:
        cat.version = old
    # explain endpoint refuses stale results too
    assert client.post("/ai/explain", json={"session_id": sid}).status_code == 409
    client.post(f"/sessions/{sid}/verify")
    client.patch(f"/sessions/{sid}/requirements", json=[{"key": "section_thickness.range",
                                                         "constraint": {"kind": "point_within", "q": {"value": 20, "unit": "um"}}}])
    assert client.get(f"/sessions/{sid}/result").status_code == 409


def test_lean_unavailable_gives_no_verdict(client, monkeypatch, tmp_path):
    monkeypatch.setenv("CRYOLEAN_LEAN_BIN", str(tmp_path / "no_such_cryolean.exe"))
    r = client.post("/verify", json={"experiment_id": MR, "configuration_id": "qd_dynacool_14T_eto_vsm_hc", "confirmed": True})
    assert r.status_code == 503
    body = r.json()
    assert body["verdict"] is None and body["verified_by_lean"] is False
    assert client.post("/search", json={"experiment_id": MR}).status_code == 503
    assert client.get("/health").json()["lean_checker_available"] is False
