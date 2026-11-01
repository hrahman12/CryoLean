"""Campaign scheduler (Z3 -> Lean validSchedule), Gatekeeper + Registry, Lanyon import, verdict card,
and the soundness fix found by the for-all-dev/forensics vacuity judge."""
import json
from fractions import Fraction

import pytest

from cryolean import gatekeeper, lanyon, lean_runner, schedule, units
from cryolean.catalog import Catalog
from conftest import check, data

H = {"value": 1, "unit": "h"}
CRX = "lakeshore_crx_vf"
ACCEPTED = ["bio_cryo_fluorescence_vitrified", "chem_low_temperature_raman", "chem_phase_transition_pom"]


def hours(n):
    return {"value": n, "unit": "h"}


# ------------------------------------------------------------------ soundness fix (forensics vacuity judge)
def Q(v, u):
    return units.lean_quantity(v, u)


@pytest.mark.parametrize("status,expected", [("unknown", "NEED_MORE_INFORMATION"),
                                             ("inferred_estimate", "NEED_MORE_INFORMATION"),
                                             ("manufacturer_specification", "DOES_NOT_MEET_REQUIREMENTS")])
def test_untrusted_not_installed_record_never_rejects(lean_available, status, expected):
    """SYNTHETIC fixture. An untrusted 'not installed' record used to cause REJECT; it must give NEED_MORE_INFORMATION."""
    cfg = {"id": "c", "equipment_id": "s", "name": "s", "capabilities": [
        {"key": "magnetic_field.max", "value": {"kind": "max", "q": Q(14, "T")}, "install": "optional_not_installed",
         "evidence_status": status, "evidence_ids": []}]}
    exp = {"id": "e", "name": "e", "industry": "x", "params": [], "coupled": [], "confirmed": True,
           "requirements": [{"keys": ["magnetic_field.max"], "constraint": {"kind": "at_least", "q": Q(9, "T")},
                             "mandatory": True, "origin": "user_entered"}]}
    assert lean_runner.check(cfg, exp)["verdict"] == expected


# ------------------------------------------------------------------ verdict card
def test_verdict_card_on_every_result(api):
    r = check(api, "mat_magnetoresistance_10T", "qd_dynacool_9T_eto_res", suggestions=False)
    c = r["verdict_card"]
    assert c["verdict"] == r["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"
    assert "magnetic_field.max" in c["reason"]
    assert "verdict_reject_sound" in c["theorems"] and "fail_needs_trusted" in c["theorems"]
    assert len(c["source_hash"]) == 64 and c["lean_input_hash"] == r["verification"]["concrete_evaluation"]["lean_input_hash"]
    assert c["z3_role"] == "Z3 output is a hint, never a verdict"
    if c["axiom_audit"] == "current":
        assert c["axioms_standard_only"] is True
        assert set().union(*c["axioms"].values()) <= {"propext", "Classical.choice", "Quot.sound"}


def test_card_theorems_exist_in_lean_sources():
    from cryolean.verifier import CARD_THEOREMS
    names = {t["name"] for t in lean_runner.theorem_inventory()["theorems"]}
    for ts in CARD_THEOREMS.values():
        assert set(ts) <= names, set(ts) - names


# ------------------------------------------------------------------ campaign scheduler
def test_schedule_packs_only_accepted_and_lean_validates(built_db, lean_available):
    cat = Catalog(str(built_db))
    exps = ACCEPTED + ["mat_magnetoresistance_10T"]
    durs = {ACCEPTED[0]: hours(6), ACCEPTED[1]: hours(8), ACCEPTED[2]: hours(4), "mat_magnetoresistance_10T": hours(2)}
    r = schedule.schedule_campaign(cat, CRX, exps, hours(48), durs, confirmed=True)
    assert r["feasible_experiments"] == ACCEPTED
    assert [e["experiment_id"] for e in r["excluded_experiments"]] == ["mat_magnetoresistance_10T"]
    assert r["z3"]["status"] == "sat" and r["z3"]["makespan"] == "23 h"     # 5 h cooldown + 6 + 8 + 4
    assert r["schedule_ok"] is True and r["lean"]["valid"] is True
    assert all(v["verdict"] == "REQUIREMENTS_MET" for v in r["lean"]["experiment_verdicts"])
    assert "validSchedule_disjoint" in r["lean"]["theorems"]


def test_schedule_too_long_gives_unsat_core(built_db, lean_available):
    cat = Catalog(str(built_db))
    durs = {ACCEPTED[0]: hours(6), ACCEPTED[1]: hours(8), ACCEPTED[2]: hours(4)}
    r = schedule.schedule_campaign(cat, CRX, ACCEPTED, hours(20), durs, confirmed=True)
    assert r["z3"]["status"] == "unsat" and r["schedule_ok"] is False and r["lean"] is None
    assert set(r["z3"]["conflicting_experiments"]) <= set(ACCEPTED)


def _valid_doc(cat):
    durs = {ACCEPTED[0]: hours(6), ACCEPTED[1]: hours(8)}
    r = schedule.schedule_campaign(cat, CRX, ACCEPTED[:2], hours(48), durs, confirmed=True)
    assert r["schedule_ok"]
    return r["lean_input"]


@pytest.mark.parametrize("tamper", ["overlap", "before_cooldown", "past_end", "wrong_id"])
def test_lean_rejects_tampered_schedules(built_db, lean_available, tamper):
    """Z3 output is a hint: a wrong slot list (as if Z3 were buggy) is refused by Lean validSchedule."""
    doc = _valid_doc(Catalog(str(built_db)))
    s0, s1 = doc["slots"]
    if tamper == "overlap":
        s1["start"] = dict(s0["start"])
    elif tamper == "before_cooldown":
        s0["start"] = {"num": 0, "den": 1, "dim": {"s": 1}}
    elif tamper == "past_end":
        s1["start"] = {"num": 47 * 3600, "den": 1, "dim": {"s": 1}}
    elif tamper == "wrong_id":
        s0["experiment_id"] = "somebody_else"
    r = schedule.check_schedule_document(doc)
    assert r["valid"] is False


def test_schedule_refuses_rejected_experiment_in_lean(built_db, lean_available):
    """validSchedule_only_accepted: even if a caller injects a rejected experiment, Lean refuses the schedule."""
    cat = Catalog(str(built_db))
    doc = _valid_doc(cat)
    from cryolean import serialize, verifier
    ex = serialize.working_experiment(cat, "mat_magnetoresistance_10T", {"run_duration": hours(1)}, None, True)
    _, bad, _, _ = verifier.build_documents(cat, ex, CRX)
    doc["experiments"].append(bad)
    doc["slots"].append({"experiment_id": bad["id"], "start": {"num": 40 * 3600, "den": 1, "dim": {"s": 1}}})
    assert schedule.check_schedule_document(doc)["valid"] is False


def test_schedule_missing_cooldown_is_reported(built_db, lean_available):
    cat = Catalog(str(built_db))
    r = schedule.schedule_campaign(cat, "linkam_thms600_lnp96_t96", ["chem_phase_transition_pom"], hours(10),
                                   {"chem_phase_transition_pom": hours(2)}, confirmed=True)
    assert r["schedule_ok"] is False and r["z3"]["status"] == "missing_information"


def test_bridge_schedule_campaign(api):
    r = data(api.schedule_campaign(CRX, json.dumps(ACCEPTED[:2]), hours(48),
                                   {ACCEPTED[0]: hours(6), ACCEPTED[1]: hours(8)}, None, True))
    assert r["schedule_ok"] is True and r["timeline"][0]["start"] == "5 h"


# ------------------------------------------------------------------ Gatekeeper
GOOD = "import CryoLean\nopen CryoLean\ntheorem gate_test_le_refl (a : Q) : Q.le a a := Q.le_refl a\n"


@pytest.mark.slow
def test_gatekeeper_admits_clean_proof_and_refuses_escape_hatches(fresh_api):
    r = data(fresh_api.submit_lean_rule("le_refl", GOOD, "test"))
    assert r["admitted"] and set(r["report"]["theorems"]["gate_test_le_refl"]) <= gatekeeper.STANDARD
    assert [x["name"] for x in data(fresh_api.list_registry())] == ["le_refl"]
    for src, hatch in [("theorem gate_t1 : 1 = 2 := by sorry\n", "sorry"),
                       ("theorem gate_t2 : 2 + 2 = 4 := by native_decide\n", "native_decide"),
                       ("axiom cheat : False\ntheorem gate_t3 : 1 = 2 := cheat.elim\n", "axiom declaration")]:
        r = data(fresh_api.submit_lean_rule("bad", src, "test"))
        assert r["admitted"] is False and hatch in r["report"]["escape_hatches"]
    r = data(fresh_api.submit_lean_rule("broken", "theorem gate_t4 : (1 : Nat) = 2 := rfl\n", "test"))
    assert r["admitted"] is False and not r["report"]["compiled"]
    assert len(data(fresh_api.list_registry())) == 1


def test_gatekeeper_catches_hidden_axiom_even_without_keyword():
    """A comment does not hide an escape hatch, and theorem names are found inside namespaces."""
    src = "/- sorry in a comment is fine -/\nnamespace Foo\ntheorem bar : True := trivial\nend Foo\n"
    assert gatekeeper._theorem_names(src) == ["Foo.bar"]
    assert "sorry" not in gatekeeper._strip_comments(src)


# ------------------------------------------------------------------ Lanyon
def _fake_run(tmp_path, certified=True, discrepancy=False, proof=GOOD):
    run = tmp_path / "run"
    (run / "save").mkdir(parents=True)
    sid = "00000000-0000-0000-0000-000000000001"
    (run / "save" / "ids.json").write_text(json.dumps({"session_id": sid}), encoding="utf-8")
    ev = []
    if certified:
        ev.append({"type": "proof.certified", "payload": {"certificate_id": "cert-1", "status": "certified",
                                                          "evidence_kind": "lanyon_symbolic", "subject_sha256": "0" * 64}})
    if discrepancy:
        ev.append({"type": "proof.discrepancy_detected", "payload": {}})
    (run / "save" / "events.json").write_text(json.dumps({"events": ev}), encoding="utf-8")
    sd = run / "sessions" / sid
    sd.mkdir(parents=True)
    if proof is not None:
        (sd / "proof-abc.lean").write_text(proof, encoding="utf-8")
    return run


def test_lanyon_client_is_pinned():
    st = lanyon.client_status()
    if not st["available"] and "not installed" in (st["reason"] or ""):
        pytest.skip("Lanyon client not installed")
    assert st["sha256"] == lanyon.CLIENT_SHA256


@pytest.mark.slow
def test_lanyon_certified_only_with_admitted_proof(built_db, tmp_path, lean_available):
    import shutil
    db = tmp_path / "c.db"
    shutil.copy(built_db, db)
    cat = Catalog(str(db))
    ok = lanyon.import_session(cat, _fake_run(tmp_path / "a"))
    assert ok["certified"] and ok["evidence_status"] == "certified_simulation"
    rec = lanyon.capability_record(ok, "temperature.gradient.max", {"kind": "max", "q": Q(1, "K")}, "demo")
    assert rec["certificate"]["registry_rule"] and rec["evidence_status"] == "certified_simulation"
    for i, kw in enumerate([{"certified": False}, {"discrepancy": True}, {"proof": None},
                            {"proof": "theorem gate_t5 : 1 = 2 := by sorry\n"}]):
        r = lanyon.import_session(cat, _fake_run(tmp_path / f"case{i}", **kw))
        assert r["certified"] is False and r["evidence_status"] == "inferred_estimate", kw
        assert lanyon.capability_record(r, "k", {"kind": "unknown"}, "x")["evidence_status"] == "inferred_estimate"


def test_certified_simulation_needs_certificate_fields(built_db):
    """Only a Lanyon run whose proof passed the Gatekeeper may carry certified_simulation in the catalog."""
    import copy
    from cryolean.validation import Report, validate_configuration
    cat = Catalog(str(built_db))
    cfg = copy.deepcopy(cat.get_configuration(CRX))
    cap = next(c for c in cfg["capabilities"] if c.get("evidence_status") == "manufacturer_specification")
    cap["evidence_status"] = "certified_simulation"
    rep = Report()
    validate_configuration(cat, cfg, "cfg", rep)
    assert any("certified_simulation needs certificate" in str(i) for i in rep.errors)
    cap["certificate"] = {"lanyon_session": "s", "proof_sha256": "0" * 64, "registry_rule": "rule_x"}
    rep = Report()
    validate_configuration(cat, cfg, "cfg", rep)
    assert not any("certified_simulation needs certificate" in str(i) for i in rep.errors)


def test_certified_simulation_is_trusted_in_lean(lean_available):
    """A Gatekeeper-backed certified simulation is trusted evidence in the Lean checker (trustedB)."""
    cfg = {"id": "c", "equipment_id": "s", "name": "s", "capabilities": [
        {"key": "temperature.gradient.max", "value": {"kind": "max", "q": Q(1, "K")}, "install": "installed",
         "evidence_status": "certified_simulation", "evidence_ids": ["lanyon:x"]}]}
    exp = {"id": "e", "name": "e", "industry": "x", "params": [], "coupled": [], "confirmed": True,
           "requirements": [{"keys": ["temperature.gradient.max"], "constraint": {"kind": "at_least", "q": Q(1, "K")},
                             "mandatory": True, "origin": "user_entered"}]}
    assert lean_runner.check(cfg, exp)["verdict"] == "REQUIREMENTS_MET"


# ------------------------------------------------------------------ documented absence (install "not_available")
@pytest.mark.parametrize("status,expected", [("manufacturer_specification", "DOES_NOT_MEET_REQUIREMENTS"),
                                             ("inferred_estimate", "NEED_MORE_INFORMATION"),
                                             ("unknown", "NEED_MORE_INFORMATION")])
def test_not_available_is_a_documented_absence(lean_available, status, expected):
    """SYNTHETIC fixture. 'not_available' (the instrument does not offer the capability) decodes to Lean's absent
    case: with trusted evidence it fails a requirement for the capability; untrusted, it only gives NEED INFO."""
    cfg = {"id": "c", "equipment_id": "s", "name": "s", "capabilities": [
        {"key": "magnetic_field.max", "value": {"kind": "unknown"}, "install": "not_available",
         "evidence_status": status, "evidence_ids": ["ev_x"]}]}
    exp = {"id": "e", "name": "e", "industry": "x", "params": [], "coupled": [], "confirmed": True,
           "requirements": [{"keys": ["magnetic_field.max"], "constraint": {"kind": "at_least", "q": Q(9, "T")},
                             "mandatory": True, "origin": "user_entered"}]}
    r = lean_runner.check(cfg, exp)
    assert r["verdict"] == expected
    if expected.startswith("DOES"):
        assert "not available" in r["checks"][0]["explanation"]


def test_not_available_requires_trusted_evidence(built_db):
    import copy
    from cryolean.validation import Report, validate_configuration
    cat = Catalog(str(built_db))
    cfg = copy.deepcopy(cat.get_configuration(CRX))
    cfg["capabilities"].append({"key": "section_thickness.range", "value": {"kind": "unknown"}, "install": "not_available",
                                "evidence_status": "inferred_estimate", "evidence_ids": []})
    rep = Report()
    validate_configuration(cat, cfg, "cfg", rep)
    assert any("not_available" in str(i) for i in rep.errors)


def test_not_available_is_never_offered_as_an_option():
    from cryolean import smt
    cfg = {"id": "c", "capabilities": [{"key": "magnetic_field.max", "value": {"kind": "max", "q": Q(14, "T")},
                                        "install": "not_available", "evidence_status": "manufacturer_specification",
                                        "evidence_ids": ["ev_x"]}]}
    st = smt.key_status(cfg, "magnetic_field.max", {"kind": "at_least", "q": Q(9, "T")})
    assert st["kind"] == "fail" and "option_satisfies" not in st
    hyp = smt.hypothetical(cfg, ["magnetic_field.max"])
    assert hyp["capabilities"][0]["install"] == "not_available"


# ------------------------------------------------------------------ information monotonicity (empirical companion of
# the Lean theorem verdict_refines in lean/CryoLean/Monotone.lean)
def test_refinement_never_changes_a_decided_verdict(lean_available):
    """SYNTHETIC fixtures. Start from configurations with gaps (missing keys, unknown values, estimates), refine them
    by documenting the gaps with trusted values, and check that every decided verdict is unchanged."""
    import random
    rng = random.Random(5)
    keys = ["temperature.range", "magnetic_field.max", "optical_access", "electrical.dc_lines", "sample.width.max"]
    good = {"temperature.range": {"kind": "range", "lo": Q(1, "K"), "hi": Q(400, "K")},
            "magnetic_field.max": {"kind": "max", "q": Q(20, "T")}, "optical_access": {"kind": "flag", "b": True},
            "electrical.dc_lines": {"kind": "count", "n": 48}, "sample.width.max": {"kind": "max", "q": Q(50, "mm")}}
    bad = {"temperature.range": {"kind": "range", "lo": Q(10, "K"), "hi": Q(400, "K")},
           "magnetic_field.max": {"kind": "max", "q": Q(5, "T")}, "optical_access": {"kind": "flag", "b": False},
           "electrical.dc_lines": {"kind": "count", "n": 4}, "sample.width.max": {"kind": "max", "q": Q(2, "mm")}}
    reqs = [{"keys": ["temperature.range"], "constraint": {"kind": "point_within", "q": Q(4, "K")}},
            {"keys": ["magnetic_field.max"], "constraint": {"kind": "at_least", "q": Q(9, "T")}},
            {"keys": ["optical_access"], "constraint": {"kind": "flag_is", "b": True}},
            {"keys": ["electrical.dc_lines"], "constraint": {"kind": "count_at_least", "n": 8}},
            {"keys": ["sample.width.max"], "constraint": {"kind": "at_least", "q": Q(3, "mm")}}]
    exp = {"id": "e", "name": "e", "industry": "x", "params": [], "coupled": [], "confirmed": True,
           "requirements": [{**r, "mandatory": True, "origin": "user_entered"} for r in reqs]}
    pairs = []
    for i in range(400):
        caps_before, caps_after = [], []
        for k in keys:
            truth = rng.choice([good[k], bad[k]])
            state = rng.choice(["known", "known", "missing", "unknown_value", "estimate"])
            rec = {"key": k, "value": truth, "install": "installed", "evidence_status": "manufacturer_specification", "evidence_ids": ["e"]}
            if state == "known":
                caps_before.append(rec)
            elif state == "unknown_value":
                caps_before.append({**rec, "value": {"kind": "unknown"}, "evidence_status": "unknown"})
            elif state == "estimate":
                caps_before.append({**rec, "evidence_status": "inferred_estimate"})
            caps_after.append(rec)                    # refinement: the gap is documented with a trusted value
        pairs.append(({"id": f"b{i}", "equipment_id": "s", "name": "s", "capabilities": caps_before}, exp))
        pairs.append(({"id": f"a{i}", "equipment_id": "s", "name": "s", "capabilities": caps_after}, exp))
    res = lean_runner.check_batch(pairs)
    decided = 0
    for before, after in zip(res[0::2], res[1::2]):
        if before["verdict"] != "NEED_MORE_INFORMATION":
            decided += 1
            assert after["verdict"] == before["verdict"]
    assert decided > 50


# ------------------------------------------------------------------ data completeness per cryostat
def test_completeness_counts_only_configuration_side_gaps(lean_available):
    from cryolean import completeness
    cfg = {"id": "c", "equipment_id": "s", "name": "s", "capabilities": [
        {"key": "temperature.range", "value": {"kind": "range", "lo": Q(1, "K"), "hi": Q(400, "K")}, "install": "installed",
         "evidence_status": "manufacturer_specification", "evidence_ids": ["e"]},
        {"key": "magnetic_field.max", "value": {"kind": "unknown"}, "install": "installed", "evidence_status": "unknown",
         "evidence_ids": []}]}
    exp = {"id": "e", "name": "e", "industry": "x", "params": [], "coupled": [], "confirmed": True,
           "requirements": [{"keys": ["temperature.range"], "constraint": {"kind": "point_within", "q": Q(4, "K")},
                             "mandatory": True, "origin": "user_entered"},
                            {"keys": ["magnetic_field.max"], "constraint": {"kind": "at_least", "q": Q(9, "T")},
                             "mandatory": True, "origin": "user_entered"}]}
    r = lean_runner.check(cfg, exp)
    g = completeness.classify(cfg, exp, r)
    assert r["verdict"] == "NEED_MORE_INFORMATION" and g["configuration"] == ["magnetic_field.max"] and g["experiment"] == []
    assert completeness.informative(cfg["capabilities"][0]) and not completeness.informative(cfg["capabilities"][1])
    assert completeness.informative({"install": "not_available", "evidence_status": "manufacturer_specification",
                                     "value": {"kind": "unknown"}})


def test_bridge_data_completeness(api):
    r = data(api.get_data_completeness())
    assert len(r["configurations"]) == sum(len(e["configurations"]) for e in data(api.list_equipment())["equipment"])
    for rec in r["configurations"].values():
        assert 0 <= rec["score"] <= 1 and rec["fully_documented"] == (len(rec["complete_for"]) == rec["experiments"])
        # a decided verdict always counts as complete (no data can change it: verdict_refines)
        for eid, v in rec["verdicts"].items():
            if v != "NEED_MORE_INFORMATION":
                assert eid in rec["complete_for"]
