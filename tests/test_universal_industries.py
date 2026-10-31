"""Acceptance test: one Lean engine across industries, and a previously unregistered industry added
through the data/research pipeline without touching the trusted Lean core."""
import hashlib
import json
from pathlib import Path

from backend import lean_runner

ROOT = Path(__file__).resolve().parents[1]
NEW = ROOT / "research" / "new_industry"


def _lean_core_hash():
    h = hashlib.sha256()
    for p in sorted((ROOT / "lean" / "CryoLean").glob("*.lean")) + [ROOT / "lean" / "Main.lean"]:
        h.update(p.read_bytes())
    h.update(lean_runner.config.lean_binary_path().read_bytes())
    return h.hexdigest()


def test_same_engine_checks_fundamentally_different_industries(client):
    pairs = {"biology_and_biotechnology": ("bio_cryosection_frozen_tissue", "leica_cm1950_genA_vacuum_motor_objcool"),
             "chemistry_and_pharmaceuticals": ("chem_low_temperature_raman", "linkam_thms600_lnp96_t96"),
             "materials_and_nanotechnology": ("mat_magnetoresistance_10T", "qd_dynacool_9T_eto_res"),
             "quantum_computing_and_sensing": ("quantum_transmon_characterization", "bluefors_ld400_hdw")}
    checkers = set()
    for industry, (e, c) in pairs.items():
        r = client.post("/verify", json={"experiment_id": e, "configuration_id": c, "confirmed": True}).json()
        assert r["industry"] == industry
        checkers.add((r["checker"], r["lean_version"]))
    assert len(checkers) == 1


def test_industry_label_cannot_change_a_verdict(lean_available, catalog):
    cfg = catalog.lean_configuration(catalog.get_configuration("qd_dynacool_9T_eto_res"))
    base = catalog.lean_experiment(catalog.get_experiment("mat_magnetoresistance_10T"))
    verdicts = set()
    for label in ("materials_and_nanotechnology", "defense_and_security", "totally_new_industry_xyz", ""):
        e = dict(base, industry=label)
        verdicts.add(lean_runner.run_check(cfg, e)["verdict"])
    assert verdicts == {"REJECT"}


def test_all_standard_industries_are_listed_and_searchable(client):
    inds = client.get("/industries").json()["industries"]
    ids = {i["id"] for i in inds}
    for must in ("aerospace_and_space_exploration", "nuclear_engineering_and_fusion", "food_and_agriculture", "metrology_and_calibration"):
        assert must in ids
    assert client.get("/industries", params={"q": "hydrogen"}).json()["industries"][0]["id"] == "energy_and_hydrogen"


def test_coverage_registry_does_not_overclaim(client):
    cov = client.get("/coverage").json()
    researched = set(cov["industries"]["researched_ids"])
    assert researched == {"biology_and_biotechnology", "chemistry_and_pharmaceuticals", "materials_and_nanotechnology", "quantum_computing_and_sensing"}
    assert cov["industries"]["known"] > len(researched)
    assert cov["missing_scientific_data"]["unknown_capabilities"], "unknowns must be reported"
    assert "does not mean every experiment" in cov["disclaimer"]


def test_new_industry_through_research_pipeline(tmp_client):
    client, cat, data = tmp_client
    core_before = _lean_core_hash()
    IND = "semiconductors_and_electronics"

    # 0. before research: a request for this industry yields NEED_MORE_INFORMATION, not a verdict on guesses
    rr = client.post("/research/requests", json={"industry": IND,
                                                 "description": "Measure I-V curves of a MoS2 transistor in a cryogenic probe station from 10 K to room temperature"}).json()
    assert rr["verdict"] == "NEED_MORE_INFORMATION" and len(rr["steps"]) == 10

    # 1. the new industry appears in the API
    client.post("/industries", json={"name": "Semiconductors and electronics", "id": IND, "description": "cryogenic device characterisation"})
    assert IND in {i["id"] for i in client.get("/industries").json()["industries"]}

    # 2. a research candidate (real sources, see research/new_industry/) is validated and stored UNTRUSTED
    exp_doc = json.loads((NEW / "semiconductor_candidate_experiment.json").read_text(encoding="utf-8"))
    ev = json.loads((NEW / "semiconductor_candidate_evidence.json").read_text(encoding="utf-8"))
    cand = client.post("/research/candidates", json={"kind": "experiment", "document": exp_doc, "evidence": ev,
                                                     "submitted_by": "research agent", "request_id": rr["id"]}).json()
    assert cand["trust"] == "candidate" and cand["validation"]["ok"], cand["validation"]
    # an untrusted candidate cannot be verified
    r = client.post("/verify", json={"experiment_id": exp_doc["id"], "configuration_id": "lakeshore_crx_4k", "confirmed": True})
    assert r.status_code == 404

    # 3. promotion requires a reviewer; then the requirements are represented in the catalog
    from backend.research_pipeline import ResearchPipeline
    pipe = ResearchPipeline(cat, data / "research_requests", data / "candidates")
    try:
        pipe.promote(cand["id"], "")
        raise AssertionError("promotion without reviewer must fail")
    except ValueError:
        pass
    pipe.promote(cand["id"], "test reviewer")
    client.post("/catalog/reload")
    ex = client.get(f"/experiments/{exp_doc['id']}").json()
    assert ex["industry"] == IND and ex["requirements"] and ex["review"]["reviewed_by"] == "test reviewer"
    assert exp_doc["id"] in client.get(f"/industries/{IND}").json()["experiment_ids"]

    # 4. relevant equipment can be searched; Z3 proposes; 5. Lean checks every proposal
    s = client.post("/search", json={"experiment_id": exp_doc["id"]}).json()
    proposals = s["verified_compatible"] + s["candidates_not_verified"]
    assert proposals, s["rejected"][:3]
    for p in proposals:
        assert p["lean"]["verified_by_lean"] and p["lean"]["industry"] == IND
        if p["candidate"]["assumed_unknown"]:
            assert p["lean"]["verdict"] != "ACCEPT"

    # 6. missing or unsupported information cannot produce ACCEPT
    for cfg_id in cat.configurations:
        r = client.post("/verify", json={"experiment_id": exp_doc["id"], "configuration_id": cfg_id, "confirmed": True}).json()
        mand = [c["outcome"] for c in r["checks"] if c["mandatory"]]
        if any(o in ("unknown", "unsupported") for o in mand):
            assert r["verdict"] != "ACCEPT"
    # a requirement on a key no equipment documents, and one outside the vocabulary
    client.post("/vocabulary/propose", json={"key": "wafer.diameter.max", "shape": "max", "unit": "um", "description": "max wafer diameter"})
    r = client.post("/verify", json={"experiment_id": exp_doc["id"], "configuration_id": "lakeshore_crx_vf", "confirmed": True,
                                     "requirement_edits": [{"key": "wafer.diameter.max", "mandatory": True,
                                                            "constraint": {"kind": "at_least", "q": {"value": 100000, "unit": "um"}}}]}).json()
    assert r["verdict"] != "ACCEPT" and "wafer.diameter.max" in r["missing_information"]

    # the trusted Lean core was not modified
    assert _lean_core_hash() == core_before


def test_invalid_candidate_is_refused(tmp_client):
    client, cat, data = tmp_client
    bad = {"id": "bad_exp", "name": "bad", "industry": "x", "confirmed": True, "sources": [],
           "requirements": [{"key": "temperature.range", "constraint": {"kind": "at_least", "q": {"value": 1.5, "unit": "K"}},
                             "mandatory": True, "origin": "experimental_observation", "evidence_ids": ["nope"]}]}
    cand = client.post("/research/candidates", json={"kind": "experiment", "document": bad, "evidence": [], "submitted_by": "ai"}).json()
    assert cand["validation"]["ok"] is False
    from backend.research_pipeline import ResearchPipeline
    pipe = ResearchPipeline(cat, data / "research_requests", data / "candidates")
    try:
        pipe.promote(cand["id"], "reviewer")
        raise AssertionError("invalid candidate promoted")
    except ValueError as e:
        assert "validation errors" in str(e)
