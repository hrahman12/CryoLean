"""Engine guarantees exercised end to end (Lean binary + bridge)."""
import random

import pytest

from cryolean import lean_runner, units
from conftest import check, data, outcome


def Q(v, u):
    return units.lean_quantity(v, u)


KEYS = ["temperature.range", "magnetic_field.max", "optical_access", "electrical.dc_lines", "sample.width.max"]


def _good(k):
    return {"temperature.range": {"kind": "range", "lo": Q(1, "K"), "hi": Q(400, "K")},
            "magnetic_field.max": {"kind": "max", "q": Q(20, "T")}, "optical_access": {"kind": "flag", "b": True},
            "electrical.dc_lines": {"kind": "count", "n": 48}, "sample.width.max": {"kind": "max", "q": Q(50, "mm")}}[k]


REQS = [{"keys": ["temperature.range"], "constraint": {"kind": "point_within", "q": Q(4, "K")}},
        {"keys": ["magnetic_field.max"], "constraint": {"kind": "at_least", "q": Q(9, "T")}},
        {"keys": ["optical_access"], "constraint": {"kind": "present"}},
        {"keys": ["electrical.dc_lines"], "constraint": {"kind": "count_at_least", "n": 8}},
        {"keys": ["sample.width.max"], "constraint": {"kind": "at_least", "q": Q(3, "mm")}}]


def _cap(k, defect):
    c = {"key": k, "value": _good(k), "install": "installed", "evidence_status": "manufacturer_specification", "evidence_ids": []}
    if defect == "unknown_value":
        c.update(value={"kind": "unknown"}, evidence_status="unknown")
    elif defect == "estimate":
        c["evidence_status"] = "inferred_estimate"
    elif defect == "no_provenance":
        c["evidence_status"] = "unknown"
    elif defect == "install_unknown":
        c["install"] = "unknown"
    elif defect == "optional":
        c["install"] = "optional_not_installed"
    elif defect == "wrong_dimension":
        v = c["value"]
        if v["kind"] in ("flag", "count"):
            c["value"] = {"kind": "max", "q": Q(1, "K")}
        else:
            for side in ("q", "lo", "hi"):
                if side in v:
                    v[side] = {**v[side], "dim": {"kg": 1, "A": 3}}    # a dimension none of these keys has
    return c


DEFECTS = ["unknown_value", "estimate", "no_provenance", "install_unknown", "optional", "wrong_dimension", "missing"]


def test_unknown_capabilities_never_supported(lean_available):
    """SYNTHETIC fixtures: random single defects; Lean must never ACCEPT and the defective check never passes."""
    rng = random.Random(3)
    pairs, meta = [], []
    for i in range(140):
        bad, defect = rng.choice(KEYS), rng.choice(DEFECTS)
        caps = [_cap(k, defect if k == bad else None) for k in KEYS if not (k == bad and defect == "missing")]
        cfg = {"id": f"syn{i}", "equipment_id": "synthetic", "name": "synthetic", "capabilities": caps}
        exp = {"id": "e", "name": "e", "industry": rng.choice(["x", "any", "new industry"]), "params": [], "coupled": [],
               "requirements": [{**r, "mandatory": True, "origin": "user_entered"} for r in REQS], "confirmed": True}
        pairs.append((cfg, exp))
        meta.append((bad, defect))
    for (bad, defect), r in zip(meta, lean_runner.check_batch(pairs)):
        assert r["verdict"] != "REQUIREMENTS_MET", (bad, defect)
        o = next(c["outcome"] for c in r["checks"] if bad in c["keys"])
        assert o != "pass", (bad, defect, o)
        assert r["verdict"] == ("DOES_NOT_MEET_REQUIREMENTS" if defect == "optional" else "NEED_MORE_INFORMATION"), (bad, defect)


def test_control_all_documented_accepts(lean_available):
    cfg = {"id": "good", "equipment_id": "synthetic", "name": "good", "capabilities": [_cap(k, None) for k in KEYS]}
    exp = {"id": "e", "name": "e", "industry": "x", "params": [], "coupled": [], "confirmed": True,
           "requirements": [{**r, "mandatory": True, "origin": "user_entered"} for r in REQS]}
    assert lean_runner.check(cfg, exp)["verdict"] == "REQUIREMENTS_MET"


def test_unconfirmed_profile_never_accepted(api):
    r = check(api, "bio_cryosection_frozen_tissue", "leica_cm1950_genA_vacuum_motor_objcool", confirmed=False)
    assert r["verdict"] == "NEED_MORE_INFORMATION"


def test_optional_requirement_does_not_block(api):
    r = check(api, "mat_magnetometry_vsm", "qd_dynacool_12T_vsm")
    opt = next(c for c in r["checks"] if c["keys"] == ["temperature.sweep_rate.max"])
    assert opt["mandatory"] is False and opt["outcome"] == "unknown"
    assert r["verdict"] == "REQUIREMENTS_MET"


def test_conditional_requirement_not_applicable_is_not_a_failure(api):
    """Frost requirement applies only at or below 0 °C; at +25 °C it is not applicable."""
    params = {"operating_temperature": {"value": 298150, "unit": "mK"}}
    edit = [{"key": "temperature.range", "constraint": {"kind": "range_within", "lo": {"value": 298150, "unit": "mK"}, "hi": {"value": 393000, "unit": "mK"}}}]
    r = check(api, "chem_phase_transition_pom", "qd_dynacool_12T_vsm", parameters=params, requirement_edits=edit, suggestions=False)
    frost = next(c for c in r["checks"] if c["keys"] == ["vacuum.available", "purge.gas"])
    assert frost["outcome"] == "not_applicable"


def test_ai_cannot_weaken_or_invent(api, fresh_api):
    refused = fresh_api.start_session("mat_magnetoresistance_10T")["data"]
    r = fresh_api.update_session(refused["id"], requirement_edits=[{"key": "magnetic_field.max", "mandatory": False}])
    assert r["ok"] is False and r["error"]["code"] == "edit_refused"
    r = fresh_api.update_session(refused["id"], requirement_edits=[{"key": "magnetic_field.max", "remove": True}])
    assert r["ok"] is False and r["error"]["code"] == "edit_refused"
    # closed-set matching: an invented id from the model is discarded
    from cryolean import ai

    class Fake(ai.ClaudeMatcher):
        def __init__(self, cat):
            self.catalog = cat

        def _ask(self, prompt):
            return '{"matches": [{"experiment_id": "invented_profile", "confidence": 0.99}, {"experiment_id": "mat_magnetometry_vsm", "confidence": 0.6}]}'
    m = ai.match(api._catalog, "magnetization", matcher=Fake(api._catalog))
    assert [x["experiment_id"] for x in m["matches"]] == ["mat_magnetometry_vsm"] and m["needs_confirmation"]


def test_injected_verdict_in_document_is_ignored(api, lean_available):
    from cryolean import serialize
    cat = api._catalog
    cfg = cat.get_configuration("qd_dynacool_9T_eto_res")
    ex = serialize.working_experiment(cat, "mat_magnetoresistance_10T", confirmed=True)
    cd = serialize.configuration_doc(cat, cfg)
    ed, _ = serialize.experiment_doc(cat, ex, cfg)
    r = lean_runner.check({**cd, "verdict": "REQUIREMENTS_MET"}, {**ed, "verdict": "REQUIREMENTS_MET", "lean_verified": True})
    assert r["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"


def test_lean_unavailable_gives_no_verdict(built_db, monkeypatch, tmp_path):
    from cryolean.bridge import CryoLeanAPI
    monkeypatch.setenv("CRYOLEAN_LEAN_BIN", str(tmp_path / "missing.exe"))
    a = CryoLeanAPI(str(built_db))
    r = a.check_compatibility("mat_magnetoresistance_10T", "qd_dynacool_14T_eto_vsm_hc", confirmed=True)
    assert r["ok"] is False and r["error"]["code"] == "lean_unavailable" and r["error"]["verdict"] is None


def test_installed_documented_vs_proposed_modifications(fresh_api):
    ch = [{"key": k, "value": {"kind": "max", "q": {"value": 5000, "unit": "um"}}} for k in ("sample.width.max", "sample.length.max", "sample.height.max")]
    data(fresh_api.register_modification("qd_dynacool_14T_eto_vsm_hc", "proposed", ch, "bigger puck we might buy"))
    r = check(fresh_api, "mat_magnetoresistance_10T", "qd_dynacool_14T_eto_vsm_hc", suggestions=False)
    assert r["verdict"] == "NEED_MORE_INFORMATION"                        # proposed upgrade is NOT installed
    data(fresh_api.register_modification("qd_dynacool_14T_eto_vsm_hc", "installed_documented", ch, "lab-measured puck area"))
    r2 = check(fresh_api, "mat_magnetoresistance_10T", "qd_dynacool_14T_eto_vsm_hc", suggestions=False)
    assert r2["verdict"] == "REQUIREMENTS_MET" and "~mod:" in r2["equipment"]["configuration_id"]
    w = next(c for c in r2["checks"] if c["keys"] == ["sample.width.max"])
    assert w["per_key"][0]["capability"]["evidence_status"] == "user_entered"


def test_exact_units_no_floats():
    with pytest.raises(units.UnitError):
        units.to_si(1.8, "K")
    assert units.lean_quantity("-195", "K") == {"num": -195, "den": 1, "dim": {"K": 1}}
    from fractions import Fraction
    t = units.lean_quantity(1, "Torr")
    assert Fraction(t["num"], t["den"]) == Fraction(101325, 760)          # exact, no rounding
    assert units.celsius_to_mK("-195") == 78150


def test_ai_matching_examples(api):
    for text, expected in [("I want to test how electricity moves through a material when it's cold", "mat_electrical_resistance_low_temperature"),
                           ("cut thin slices of frozen mouse brain", "bio_cryosection_frozen_tissue"),
                           ("watch a wax crystallize and melt under a polarized microscope", "chem_phase_transition_pom"),
                           ("measure the magnetization hysteresis loop of a powder up to 9 tesla", "mat_magnetometry_vsm")]:
        m = data(api.match_experiment(text))
        # 204 profiles now include several close procedures (e.g. two sectioning methods); the user picks from the ranked list
        assert expected in [x["experiment_id"] for x in m["matches"][:3]], (text, m["matches"][:3])
    assert data(api.match_experiment("bake a cake"))["no_good_match"] is True
