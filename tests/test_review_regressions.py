"""Regression tests for every finding confirmed by the 2026-10-31 adversarial review."""
import copy
import json

import pytest

from cryolean import lean_runner, serialize, smt, units, verifier
from conftest import check, data, outcome


def Q(v, u):
    return units.lean_quantity(v, u)


# ---------------------------------------------------------------- Lean core / decoder
def test_lean1_absent_requirement_met_by_option_not_installed(lean_available):
    cfg = {"id": "c", "equipment_id": "x", "name": "c", "capabilities": [
        {"key": "magnetic_field.max", "value": {"kind": "max", "q": Q(14, "T")}, "install": "optional_not_installed",
         "evidence_status": "manufacturer_specification"}]}
    exp = {"id": "e", "name": "e", "industry": "x", "params": [], "coupled": [], "confirmed": True,
           "requirements": [{"keys": ["magnetic_field.max"], "constraint": {"kind": "absent"}, "mandatory": True, "origin": "user_entered"}]}
    assert lean_runner.check(cfg, exp)["verdict"] == "REQUIREMENTS_MET"
    exp["requirements"][0]["constraint"] = {"kind": "at_least", "q": Q(10, "T")}
    assert lean_runner.check(cfg, exp)["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"


@pytest.mark.parametrize("mutate,needle", [
    (lambda cfg, exp: cfg["capabilities"].append(copy.deepcopy(cfg["capabilities"][0])), "duplicate capability key"),
    (lambda cfg, exp: exp["params"].extend([{"name": "T", "value": Q(2, "K"), "origin": "user_entered"}] * 2), "duplicate parameter"),
    (lambda cfg, exp: exp["requirements"].append({"keys": ["gas.compatible"], "constraint": {"kind": "set_contains", "needed": []},
                                                   "mandatory": True, "origin": "user_entered"}), "set_contains"),
    (lambda cfg, exp: cfg["capabilities"][0]["value"]["lo"].update(dim={"kelvin": 1}), "unknown dimension"),
])
def test_lean2_3_4_decoder_fails_closed(lean_available, mutate, needle):
    cfg = {"id": "c", "equipment_id": "x", "name": "c", "capabilities": [
        {"key": "temperature.range", "value": {"kind": "range", "lo": Q(1, "K"), "hi": Q(400, "K")}, "install": "installed",
         "evidence_status": "manufacturer_specification"}]}
    exp = {"id": "e", "name": "e", "industry": "x", "params": [], "coupled": [], "confirmed": True,
           "requirements": [{"keys": ["temperature.range"], "constraint": {"kind": "point_within", "q": Q(2, "K")}, "mandatory": True, "origin": "user_entered"}]}
    mutate(cfg, exp)
    with pytest.raises(lean_runner.LeanDecodeError) as e:
        lean_runner.check(cfg, exp)
    assert needle in str(e.value)


# ---------------------------------------------------------------- data provenance
def test_dp_data_corrections(api):
    cat = api._catalog
    tr = next(c for c in cat.get_configuration("oxford_optistatdry_blv")["capabilities"] if c["key"] == "temperature.range")
    assert tr["value"]["lo"] == {"value": 6500, "unit": "mK"} and "ev_ox_0024" in tr["evidence_ids"]          # DP-1
    pa = next(c for c in cat.get_configuration("lakeshore_crx_4k")["capabilities"] if c["key"] == "electrical.probe_arms")
    assert pa["value"] == {"kind": "count", "n": 2}                                                           # DP-2
    for cid in ("leica_cm1950_genA_standard", "leica_cm1950_dualecotec_standard"):
        st = next(c for c in cat.get_configuration(cid)["capabilities"] if c["key"] == "temperature.stability")
        assert st["value"]["kind"] == "unknown"                                                              # DP-3
    assert not any(r.get("key") == "temperature.cooling_rate.max" for r in cat.get_experiment("chem_phase_transition_pom")["requirements"])  # DP-5
    p = next(p for p in cat.get_experiment("bio_cryo_fluorescence_vitrified")["params"] if p["name"] == "operating_temperature")
    assert p["evidence_ids"] == ["ev_exp_0011"]                                                               # DP-7
    v = next(c for c in cat.get_configuration("bluefors_ld400_hdw")["capabilities"] if c["key"] == "magnetic_field.vector")
    assert v["install"] == "unknown" and v["value"]["kind"] == "unknown"                                      # DP-9


# ---------------------------------------------------------------- Z3 consistency
def _docs(api, exp_id, cfg_id, mutate=None):
    cat = api._catalog
    ex = serialize.working_experiment(cat, exp_id, confirmed=True)
    if mutate:
        mutate(ex)
    cd, ed, _, _ = verifier.build_documents(cat, ex, cfg_id)
    return ex, cd, ed


def test_smt1_duplicate_requirement_keys_do_not_crash(api):
    def dup(ex):
        ex["requirements"].append({"key": "temperature.range", "constraint": {"kind": "point_within", "q": {"value": 300, "unit": "K"}},
                                   "mandatory": True, "origin": "user_entered", "rationale": "dup"})
    ex, cd, ed = _docs(api, "chem_low_temperature_raman", "linkam_thms600_lnp96_t96", dup)
    r = verifier.check(api._catalog, ex, "linkam_thms600_lnp96_t96")
    assert r["suggestions"]["conflicts"]["status"] in ("unsat", "sat_on_documented_facts")


def test_smt2_optional_unknown_value_agrees_with_lean(api):
    ex, cd, ed = _docs(api, "mat_magnetometry_vsm", "bluefors_ld400_hdw")
    lean = lean_runner.check(cd, ed)
    ev = smt.evaluate(cd, ed)
    assert lean["verdict"] == "DOES_NOT_MEET_REQUIREMENTS" and ev.status == "conflict"


def test_smt3_any_of_with_unknown_key_is_not_a_conflict(api):
    ex, cd, ed = _docs(api, "chem_low_temperature_raman", "oxford_optistatdry_tlex")
    frost = [c for c in lean_runner.check(cd, ed)["checks"] if c["keys"] == ["vacuum.available", "purge.gas"]][0]
    ev = smt.evaluate(cd, ed)
    labels = ev.failing_items
    if frost["outcome"] != "fail":
        assert not any("vacuum.available|purge.gas" in l for l in labels)


def test_smt5_coupled_core_names_the_machine_fact(api):
    ex, cd, ed = _docs(api, "quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw")
    core = smt.all_conflicts(cd, ed)["conflicts"][0]
    assert any(f.get("key") == "cooling_power.at_20mK" and f.get("evidence_ids") for f in core["facts"])


def test_smt6_inverted_range_is_not_satisfiable_in_z3(api):
    def inv(ex):
        for r in ex["requirements"]:
            if r.get("key") == "temperature.range":
                r["constraint"] = {"kind": "range_within", "lo": {"value": 300, "unit": "K"}, "hi": {"value": 2, "unit": "K"}}
    ex, cd, ed = _docs(api, "mat_magnetometry_vsm", "qd_dynacool_12T_vsm", inv)
    assert lean_runner.check(cd, ed)["verdict"] == "NEED_MORE_INFORMATION"
    assert smt.evaluate(cd, ed).status != "satisfiable"
    # and user edits refuse it up front
    r = api.check_compatibility("mat_magnetometry_vsm", "qd_dynacool_12T_vsm", requirement_edits=[
        {"key": "temperature.range", "constraint": {"kind": "range_within", "lo": {"value": 300, "unit": "K"}, "hi": {"value": 2, "unit": "K"}}}], confirmed=True)
    assert r["ok"] is False and r["error"]["code"] == "edit_refused"


# ---------------------------------------------------------------- Python boundary
def test_f1_alternatives_and_search_respect_modifications(fresh_api):
    data(fresh_api.register_modification("qd_dynacool_12T_vsm", "undocumented", [{"key": "magnetic_field.max"}], "magnet rewound"))
    direct = check(fresh_api, "mat_magnetometry_vsm", "qd_dynacool_12T_vsm", suggestions=False)
    assert direct["verdict"] == "NEED_MORE_INFORMATION"
    found = data(fresh_api.find_compatible_equipment("mat_magnetometry_vsm", confirmed=True))
    assert all(not c["configuration_id"].startswith("qd_dynacool_12T_vsm") for c in found["verified_compatible"])


@pytest.mark.parametrize("flag", [None, "false", "true", 1])
def test_f2_confirmation_is_strict(api, flag):
    r = data(api.check_compatibility("mat_magnetometry_vsm", "qd_dynacool_12T_vsm", None, None, flag, None, False))
    assert r["verdict"] == "NEED_MORE_INFORMATION"


def test_f3_compare_and_find_default_unconfirmed(api):
    r = data(api.compare_equipment("mat_magnetometry_vsm", ["qd_dynacool_12T_vsm"]))
    assert r["results"][0]["verdict"] == "NEED_MORE_INFORMATION"
    f = data(api.find_compatible_equipment("mat_magnetometry_vsm"))
    assert f["verified_compatible"] == []


def test_f4_promotion_cannot_overwrite_trusted_records(fresh_api):
    eq = copy.deepcopy(fresh_api._catalog.get_equipment("oxford_teslatronpt"))
    doc = {k: v for k, v in eq.items() if k in ("id", "manufacturer", "model", "family")}
    doc["configurations"] = [{"id": "oxford_teslatronpt_8T", "name": "x", "capabilities": [
        {"key": "magnetic_field.max", "value": {"kind": "max", "q": {"value": 20000, "unit": "mT"}}, "install": "installed",
         "evidence_status": "manufacturer_specification", "evidence_ids": ["pm_001"]}]}]
    ev = [{"id": "pm_001", "claim": "x", "quote": "x", "source_url": "https://example.com/x", "document_title": "x",
           "evidence_status": "manufacturer_specification", "accessed": "2026-10-31"}]
    cand = data(fresh_api.register_equipment(doc, ev, "attacker"))
    assert cand["validation"]["ok"] is False
    assert fresh_api.approve_candidate(cand["id"], "reviewer")["ok"] is False
    assert fresh_api._catalog.evidence["pm_001"]["source_url"] != "https://example.com/x"


def test_f5_internal_num_den_and_floats_refused_from_users(api):
    bad = {"target_field": {"value": "9", "unit": "T", "num": 1, "den": 10, "dim": {"kg": 1, "s": -2, "A": -1}}}
    r = api.check_compatibility("mat_magnetometry_vsm", "qd_dynacool_12T_vsm", parameters=bad, confirmed=True)
    assert r["ok"] is False and r["error"]["code"] in ("edit_refused", "invalid_input")
    r = api.check_compatibility("mat_magnetometry_vsm", "qd_dynacool_12T_vsm", parameters={"target_field": {"value": 9.9, "unit": "T"}}, confirmed=True)
    assert r["ok"] is False


def test_f6_negative_parameters_never_help(api):
    r = check(api, "quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw", parameters={"design_margin": {"value": "-3", "unit": "count"}})
    assert r["verdict"] != "REQUIREMENTS_MET"
    assert r["coupled_checks"][0]["outcome"] == "unsupported"


def test_f7_material_temperature_is_derived_and_required(fresh_api):
    cat = fresh_api._catalog
    ex = serialize.working_experiment(cat, "mat_electrical_resistance_low_temperature", confirmed=True)
    ex["coupled"] = [{"model": "differential_thermal_contraction", "mandatory": True}]
    base = [p for p in ex["params"] if p["name"] != "operating_temperature"]
    ex["params"] = base + [
        {"name": "operating_temperature", "value": {"value": 5000, "unit": "mK"}, "origin": "user_entered"},
        {"name": "contraction_data_temperature", "value": {"value": 5000, "unit": "mK"}, "origin": "user_entered"},
        {"name": "sample_length", "value": {"value": "10", "unit": "mm"}, "origin": "user_entered"},
        {"name": "eps_sample", "value": "material:ptfe@80000mK"}, {"name": "eps_holder", "value": "material:copper@80000mK"},
        {"name": "allowed_mismatch", "value": {"value": "170", "unit": "um"}, "origin": "user_entered"}]
    r = verifier.check(cat, ex, "qd_dynacool_14T_eto_vsm_hc", suggestions=False)
    assert all(c["outcome"] != "pass" for c in r["coupled_checks"])          # data at 80 K, operating at 5 K: not valid
    ex["params"][-3]["value"] = "material:ptfe"                               # no temperature -> refused
    with pytest.raises(serialize.SerializationError):
        verifier.check(cat, ex, "qd_dynacool_14T_eto_vsm_hc", suggestions=False)


def test_f8_cooling_slot_uses_installed_capabilities_only(api):
    cat = api._catalog
    cfg = cat.get_configuration("bluefors_ld400_hdw")
    ex = serialize.working_experiment(cat, "quantum_mxc_wiring_heat_budget", confirmed=True)
    mod = copy.deepcopy(cfg)
    for c in mod["capabilities"]:
        if c["key"] == "cooling_power.at_20mK":
            c["install"] = "optional_not_installed"
    slots, _ = serialize.resolve_slots(cat, cat.coupled_models["mxc_wiring_heat_budget"], mod, ex["params"])
    assert "cooling" not in slots
