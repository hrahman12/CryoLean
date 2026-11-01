"""The 20 required scenarios. Real, sourced specifications are used wherever they exist; the few synthetic
fixtures are marked SYNTHETIC and only exercise the engine (never a published claim)."""
import copy
import hashlib
import json
import os
from pathlib import Path

import pytest

from cryolean import config, lean_runner, serialize, smt
from conftest import check, data, outcome

ROOT = Path(__file__).resolve().parents[1]


# 1 -------------------------------------------------------------------------------------------
def test_01_temperature_compatibility(api):
    ok = check(api, "chem_phase_transition_pom", "linkam_thms600_lnp96_t96")       # 203-393 K inside 78-873 K
    assert outcome(ok, "temperature.range") == "pass" and ok["verdict"] == "REQUIREMENTS_MET"
    bad = check(api, "chem_temperature_dependent_photoluminescence", "linkam_thms600_lnp96_t96")   # needs 4 K
    assert outcome(bad, "temperature.range") == "fail" and bad["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"


# 2 -------------------------------------------------------------------------------------------
def test_02_sample_size_incompatibility(api):
    edit = [{"key": "sample.diameter.max", "constraint": {"kind": "at_least", "q": {"value": 30000, "unit": "um"}}}]
    r = check(api, "chem_low_temperature_raman", "linkam_thms600_lnp96_t96", requirement_edits=edit)
    assert outcome(r, "sample.diameter.max") == "fail"                              # documented 22 mm sample area
    assert r["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"


# 3 -------------------------------------------------------------------------------------------
def test_03_insufficient_cooling_power(api):
    # Joule heating (user parameters) against the Bluefors LD250 documented 10 µW at 20 mK
    params = {"measurement_current": {"value": "200", "unit": "uA"}, "sample_resistance": {"value": "1000", "unit": "Ohm"},
              "operating_temperature": {"value": "20", "unit": "mK"}}
    edit = [{"key": "temperature.base", "mandatory": True, "constraint": {"kind": "at_most", "q": {"value": 20, "unit": "mK"}}}]
    ex_id = "mat_electrical_resistance_low_temperature"
    r = check(api, ex_id, "bluefors_ld250_manual_v2", parameters=params, requirement_edits=edit)
    c = next(c for c in r["coupled_checks"] if c["model"] == "joule_heating_vs_cooling_power")
    assert c["outcome"] == "fail"                    # 40 µW > 10 µW
    assert c["lhs"]["display"] == "40 µW" and c["rhs"]["display"] == "10 µW"


# 4 -------------------------------------------------------------------------------------------
def test_04_magnetic_field_incompatibility(api):
    r9 = check(api, "mat_magnetoresistance_10T", "qd_dynacool_9T_eto_res")
    r14 = check(api, "mat_magnetoresistance_10T", "qd_dynacool_14T_eto_vsm_hc")
    assert outcome(r9, "magnetic_field.max") == "fail" and r9["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"
    assert outcome(r14, "magnetic_field.max") == "pass"
    assert r14["verdict"] == "NEED_MORE_INFORMATION"            # transport sample size is not documented


# 5 -------------------------------------------------------------------------------------------
def test_05_missing_measurement_accessory(api):
    r = check(api, "mat_magnetometry_vsm", "qd_dynacool_9T_eto_res")
    assert outcome(r, "module.vsm") == "fail" and r["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"
    vsm = next(c for c in r["checks"] if c["keys"] == ["module.vsm"])
    assert vsm["per_key"][0]["capability"]["install"] == "optional_not_installed"
    ok = check(api, "mat_magnetometry_vsm", "qd_dynacool_12T_vsm")
    assert ok["verdict"] == "REQUIREMENTS_MET"


# 6 -------------------------------------------------------------------------------------------
def test_06_electrical_feedthrough_limitation(api):
    edit = [{"key": "electrical.coax_lines", "constraint": {"kind": "count_at_least", "n": 200}}]
    r = check(api, "quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw", requirement_edits=edit)
    assert outcome(r, "electrical.coax_lines") == "fail"          # documented 168


# 7 -------------------------------------------------------------------------------------------
def test_07_thermal_load_exceeds_cooling_capacity(api):
    r = check(api, "quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw")
    c = r["coupled_checks"][0]
    assert c["outcome"] == "fail" and c["lhs"]["display"] == "14.592 µW" and c["rhs"]["display"] == "12 µW"


# 8 -------------------------------------------------------------------------------------------
def test_08_optical_working_distance_incompatibility(fresh_api):
    """THMS600 needs an objective working distance of at least 4.8 mm (eg_052); a 3 mm objective cannot reach the sample."""
    from cryolean import serialize, verifier
    cat = fresh_api._catalog
    ex = serialize.working_experiment(cat, "chem_low_temperature_raman", confirmed=True)
    ex["coupled"] = [{"model": "objective_working_distance_clearance", "mandatory": True, "rationale": "user objective"}]
    ex["params"] += [{"name": "objective_working_distance", "value": {"value": "3", "unit": "mm"}, "origin": "user_entered"},
                     {"name": "extra_spacer", "value": {"value": "0", "unit": "mm"}, "origin": "user_entered"}]
    r = verifier.check(cat, ex, "linkam_thms600_lnp96_t96", suggestions=True)
    c = r["coupled_checks"][0]
    assert c["outcome"] == "fail" and r["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"
    p = next(p for p in r["suggestions"]["parameter_changes"] if p["parameter"] == "objective_working_distance")
    assert p["status"] == "found" and p["suggested"] == "4.8 mm" and p["verified"] is True


# 9 -------------------------------------------------------------------------------------------
def test_09_thermal_contraction_constraint(fresh_api):
    """Real reference data (NBS Monograph 29): 10 mm silicon chip on copper at 4 K mismatches by 30.4 µm."""
    from cryolean import serialize, verifier
    cat = fresh_api._catalog
    ex = serialize.working_experiment(cat, "mat_electrical_resistance_low_temperature", confirmed=True)
    ex["coupled"] = [{"model": "differential_thermal_contraction", "mandatory": True, "rationale": "chip glued to holder"}]
    ex["params"] = [p for p in ex["params"] if p["name"] != "operating_temperature"] + [
        {"name": "operating_temperature", "value": {"value": 4000, "unit": "mK"}, "origin": "user_entered"},
        {"name": "contraction_data_temperature", "value": {"value": 4000, "unit": "mK"}, "origin": "reference_data", "evidence_ids": ["tc_001"]},
        {"name": "sample_length", "value": {"value": "10", "unit": "mm"}, "origin": "user_entered"},
        {"name": "eps_sample", "value": "material:silicon@4000mK"},
        {"name": "eps_holder", "value": "material:copper@4000mK"},
        {"name": "allowed_mismatch", "value": {"value": "20", "unit": "um"}, "origin": "user_entered"}]
    r = verifier.check(cat, ex, "qd_dynacool_14T_eto_vsm_hc")
    rels = [c for c in r["coupled_checks"] if c["model"] == "differential_thermal_contraction"]
    assert {c["outcome"] for c in rels} == {"pass", "fail"}
    failing = next(c for c in rels if c["outcome"] == "fail")
    assert failing["lhs"]["display"] == "30.4 µm"            # 10 mm x (0.00326 - 0.00022)
    assert r["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"


# 10 ------------------------------------------------------------------------------------------
def test_10_vacuum_incompatibility(api):
    r = check(api, "chem_temperature_dependent_photoluminescence", "linkam_thms600_lnp96_t96")
    assert outcome(r, "vacuum.available") == "fail"          # THMS600 standard stage: vacuum only in separate versions


# 11 ------------------------------------------------------------------------------------------
def test_11_missing_mandatory_manufacturer_data(api):
    r = check(api, "chem_low_temperature_raman", "linkam_thms600_heating_only")
    assert outcome(r, "temperature.range") == "unknown" and r["verdict"] == "NEED_MORE_INFORMATION"


# 12 ------------------------------------------------------------------------------------------
def test_12_unsupported_physical_requirements(api, fresh_api):
    # (a) a model that is not validated is reported UNSUPPORTED, never a pass
    from cryolean import serialize, verifier
    cat = fresh_api._catalog
    ex = serialize.working_experiment(cat, "mat_magnetometry_vsm", confirmed=True)
    ex["coupled"] = [{"model": "temperature_stability_during_field_sweep", "mandatory": True}]
    r = verifier.check(cat, ex, "qd_dynacool_12T_vsm", suggestions=False)
    assert r["coupled_checks"][0]["outcome"] == "unsupported" and r["verdict"] == "NEED_MORE_INFORMATION"
    # (b) a dimension mismatch (kelvin required against a tesla capability): refused at the boundary, and if a
    #     document reaches Lean anyway the check is unsupported, never converted and never a pass
    edit = [{"key": "magnetic_field.max", "constraint": {"kind": "at_least", "q": {"value": 10, "unit": "K"}}}]
    refused = api.check_compatibility("mat_magnetoresistance_10T", "qd_dynacool_14T_eto_vsm_hc", requirement_edits=edit, confirmed=True)
    assert refused["ok"] is False and refused["error"]["code"] == "edit_refused"
    cat = api._catalog
    ex = serialize.working_experiment(cat, "mat_magnetoresistance_10T", confirmed=True)
    cfg = cat.get_configuration("qd_dynacool_14T_eto_vsm_hc")
    cd = serialize.configuration_doc(cat, cfg)
    ed, _ = serialize.experiment_doc(cat, ex, cfg)
    for r in ed["requirements"]:
        if r["keys"] == ["magnetic_field.max"]:
            r["constraint"] = {"kind": "at_least", "q": {"num": 10, "den": 1, "dim": {"K": 1}}}
    lr = lean_runner.check(cd, ed)
    assert next(c["outcome"] for c in lr["checks"] if c["keys"] == ["magnetic_field.max"]) == "unsupported"
    assert lr["verdict"] != "REQUIREMENTS_MET"


# 13 & 14 ------------------------------------------------------------------------------------
def test_13_14_z3_proposes_invalid_configuration_lean_rejects(api, monkeypatch):
    """A (buggy or adversarial) solver ranks the 9 T configuration first for a 10 T experiment; Lean rejects it."""
    real = smt.rank_alternatives

    def bad_rank(pairs, *a, **k):
        out = real(pairs, *a, **k)
        nine = next(x for x in out if x["configuration_document"]["id"] == "qd_dynacool_9T_eto_res")
        nine["evaluation"] = {**nine["evaluation"], "status": "satisfiable", "failing_items": []}
        return [nine] + [x for x in out if x is not nine]
    monkeypatch.setattr(smt, "rank_alternatives", bad_rank)
    found = data(api.find_compatible_equipment("mat_magnetoresistance_10T", confirmed=True))
    bad = next(c for c in found["candidates"] if c["configuration_id"] == "qd_dynacool_9T_eto_res")
    assert bad["z3_status"] == "satisfiable" and bad["lean_verdict"] == "DOES_NOT_MEET_REQUIREMENTS" and bad["verified"] is False
    assert all(c["configuration_id"] != "qd_dynacool_9T_eto_res" for c in found["verified_compatible"])


# 15 ------------------------------------------------------------------------------------------
def test_15_lean_accepts_valid_candidate(api):
    found = data(api.find_compatible_equipment("mat_magnetometry_vsm", confirmed=True))
    ids = {c["configuration_id"] for c in found["verified_compatible"]}
    assert {"qd_dynacool_12T_vsm", "qd_dynacool_14T_eto_vsm_hc"} <= ids
    for c in found["verified_compatible"]:
        assert c["lean_verdict"] == "REQUIREMENTS_MET"


# 16 ------------------------------------------------------------------------------------------
def test_16_equipment_switching_invalidates_results(api):
    s = data(api.start_session("mat_magnetoresistance_10T"))
    data(api.update_session(s["id"], confirmed=True))
    data(api.select_equipment(s["id"], "qd_dynacool_9T_eto_res"))
    r1 = data(api.check_session(s["id"]))
    assert r1["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"
    assert data(api.get_session_result(s["id"]))["result_id"] == r1["result_id"]
    data(api.select_equipment(s["id"], "qd_dynacool_14T_eto_vsm_hc"))
    stale = api.get_session_result(s["id"])
    assert stale["ok"] is False and stale["error"]["code"] == "stale_result" and stale["error"]["verdict"] is None
    r2 = data(api.check_session(s["id"]))
    assert r2["experiment"]["id"] == r1["experiment"]["id"] and r2["fingerprint"] != r1["fingerprint"]


def test_16b_stored_result_refused_after_catalog_change(fresh_api):
    r = data(fresh_api.check_compatibility("bio_cryosection_frozen_tissue", "leica_cm1950_genA_vacuum_motor_objcool", confirmed=True))
    assert data(fresh_api.get_verification_details(r["result_id"]))["verdict"] == "REQUIREMENTS_MET"
    data(fresh_api.register_modification("leica_cm1950_genA_vacuum_motor_objcool", "undocumented",
                                         [{"key": "temperature.specimen_head.range"}], "object head re-wired"))
    stale = fresh_api.get_verification_details(r["result_id"])
    assert stale["ok"] is False and stale["error"]["code"] == "stale_result"
    again = data(fresh_api.check_compatibility("bio_cryosection_frozen_tissue", "leica_cm1950_genA_vacuum_motor_objcool", confirmed=True))
    assert again["verdict"] == "NEED_MORE_INFORMATION" and "~mod:" in again["equipment"]["configuration_id"]


# 17 ------------------------------------------------------------------------------------------
def test_17_independent_checks_pass_coupled_fails(api):
    r = check(api, "quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw")
    assert all(c["outcome"] == "pass" for c in r["checks"] if c["mandatory"])
    assert r["coupled_checks"][0]["outcome"] == "fail" and r["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"
    fix = next(p for p in r["suggestions"]["parameter_changes"] if p["parameter"] == "n_flux_lines")
    assert fix["suggested"] == "39" and fix["lean_verdict"] == "REQUIREMENTS_MET" and fix["verified"] is True


# 18 & 19 ------------------------------------------------------------------------------------
def _core_hash():
    h = hashlib.sha256()
    for p in sorted((ROOT / "lean" / "CryoLean").glob("*.lean")) + [ROOT / "lean" / "Main.lean"]:
        h.update(p.read_bytes())
    h.update(config.lean_binary_path().read_bytes())
    return h.hexdigest()


def test_18_register_previously_unknown_industry(fresh_api):
    before = _core_hash()
    ind = data(fresh_api.register_industry("Cryogenic food preservation research", "new label", "food_cryopreservation_research"))
    assert ind["status"] == "registered"
    assert "food_cryopreservation_research" in {i["id"] for i in data(fresh_api.list_industries())["industries"]}
    rr = data(fresh_api.research_new_experiment("Freeze fruit tissue and section it", "food_cryopreservation_research"))
    assert rr["verdict"] == "NEED_MORE_INFORMATION" and len(rr["request"]["steps"]) == 12
    # semiconductors: sourced candidate through the validation gate and reviewer promotion
    nd = ROOT / "research" / "new_industry"
    doc = json.loads((nd / "semiconductor_candidate_experiment.json").read_text(encoding="utf-8"))
    ev = json.loads((nd / "semiconductor_candidate_evidence.json").read_text(encoding="utf-8"))
    cand = data(fresh_api.register_experiment(doc, ev, "research agent"))
    assert cand["validation"]["ok"] and cand["trust"] == "candidate"
    assert fresh_api.check_compatibility(doc["id"], "lakeshore_crx_vf", confirmed=True)["error"]["code"] == "not_found"
    assert fresh_api.approve_candidate(cand["id"], "")["ok"] is False
    data(fresh_api.approve_candidate(cand["id"], "test reviewer"))
    found = data(fresh_api.find_compatible_equipment(doc["id"], confirmed=True))
    assert "lakeshore_crx_vf" in {c["configuration_id"] for c in found["verified_compatible"]}
    # the CRX-4K configuration documents 2 probe arms; the profile needs at least 3 -> Lean rejects it
    r4k = data(fresh_api.check_compatibility(doc["id"], "lakeshore_crx_4k", confirmed=True, suggestions=False))
    assert r4k["verdict"] == "DOES_NOT_MEET_REQUIREMENTS" and outcome(r4k, "electrical.probe_arms") == "fail"
    for c in found["candidates"]:
        if c["z3_unknown_items"]:
            assert c["lean_verdict"] != "REQUIREMENTS_MET"
    assert _core_hash() == before


def test_19_same_lean_core_across_industries(api):
    pairs = {"biology_and_biotechnology": ("bio_cryosection_frozen_tissue", "leica_cm1950_genA_vacuum_motor_objcool"),
             "chemistry_and_pharmaceuticals": ("chem_phase_transition_pom", "linkam_thms600_lnp96_t96"),
             "materials_and_nanotechnology": ("mat_magnetometry_vsm", "qd_dynacool_12T_vsm"),
             "quantum_computing_and_sensing": ("quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw")}
    engines = set()
    for ind, (e, c) in pairs.items():
        r = check(api, e, c, suggestions=False)
        assert r["experiment"]["industry"] == ind
        engines.add((r["verification"]["concrete_evaluation"]["engine"], r["verification"]["concrete_evaluation"]["lean_version"]))
    assert len(engines) == 1


def test_19b_industry_label_cannot_change_verdict(api, lean_available):
    from cryolean import serialize
    cat = api._catalog
    ex = serialize.working_experiment(cat, "mat_magnetoresistance_10T", confirmed=True)
    cfg = cat.get_configuration("qd_dynacool_9T_eto_res")
    cd = serialize.configuration_doc(cat, cfg)
    ed, _ = serialize.experiment_doc(cat, ex, cfg)
    verdicts = {lean_runner.check(cd, {**ed, "industry": lab})["verdict"] for lab in ("materials", "defense_and_security", "brand-new", "")}
    assert verdicts == {"DOES_NOT_MEET_REQUIREMENTS"}


# 20 ------------------------------------------------------------------------------------------
def test_20_offline_verification_from_local_data(api, monkeypatch):
    import socket

    def no_network(*a, **k):
        raise OSError("network disabled for this test")
    monkeypatch.setattr(socket, "socket", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)
    r = check(api, "bio_cryosection_frozen_tissue", "leica_cm1950_genA_vacuum_motor_objcool")
    assert r["verdict"] == "REQUIREMENTS_MET" and r["verification"]["concrete_evaluation"]["verified_by_lean"] is True
    assert any("leicabiosystems" in (e.get("source_url") or "") or "leica" in (e.get("document_title") or "").lower()
               for c in r["checks"] for e in c["capability_evidence"])


# Verified-fix gate -----------------------------------------------------------------------------
def test_suggested_fixes_are_all_lean_verified_and_apply_reproduces_them(api):
    """Every listed fix passed Lean before it is shown; Apply fix re-runs Lean on the identical configuration."""
    r = check(api, "quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw")
    sg = r["suggestions"]
    assert sg["gate"] == "lean_verified_only"
    assert sg["verified_fixes"], "expected at least one verified fix for the wiring demo"
    for f in sg["verified_fixes"]:
        assert f["lean"]["verdict"] == "REQUIREMENTS_MET" and f["lean"]["lean_input_hash"]
        assert f["verified"] is True
    for f in sg["parameter_changes"] + sg["alternatives"]:
        assert f["verified"] is True
    for f in sg["verified_fixes"]:
        out = data(api.apply_fix("quantum_mxc_wiring_heat_budget", f, None, None, True))
        assert out["verdict"] == "REQUIREMENTS_MET"
        assert out["apply_fix"]["same_configuration"] and out["apply_fix"]["confirmed"]


def test_no_verified_solution_is_reported_not_faked(api):
    r = check(api, "quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw")
    sg = r["suggestions"]
    if not sg["verified_fixes"]:
        assert sg["status"] == "no_verified_solution_found" and sg["message"] == "No verified solution found"
    assert sg["requirement_relaxations"] == []
