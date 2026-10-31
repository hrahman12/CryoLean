"""Unknown, estimated, not-installed or unrepresentable capabilities can never be treated as supported —
checked against the real Lean binary on randomly generated documents, and in the Z3 encoding."""
import random

from backend import lean_runner
from solver.z3_search import ConfigurationSearch

KEYS = ["temperature.range", "magnetic_field.max", "optical_access", "electrical.dc_lines", "sample.width.max"]


def _good(key):
    return {"temperature.range": {"kind": "range", "lo": {"value": 1000, "unit": "mK"}, "hi": {"value": 400000, "unit": "mK"}},
            "magnetic_field.max": {"kind": "max", "q": {"value": 20000, "unit": "mT"}},
            "optical_access": {"kind": "flag", "b": True},
            "electrical.dc_lines": {"kind": "count", "n": 48},
            "sample.width.max": {"kind": "max", "q": {"value": 50000, "unit": "um"}}}[key]


REQS = [
    {"key": "temperature.range", "constraint": {"kind": "point_within", "q": {"value": 4000, "unit": "mK"}}},
    {"key": "magnetic_field.max", "constraint": {"kind": "at_least", "q": {"value": 9000, "unit": "mT"}}},
    {"key": "optical_access", "constraint": {"kind": "present"}},
    {"key": "electrical.dc_lines", "constraint": {"kind": "count_at_least", "n": 8}},
    {"key": "sample.width.max", "constraint": {"kind": "at_least", "q": {"value": 3000, "unit": "um"}}},
]


def _cap(key, defect):
    cap = {"key": key, "value": _good(key), "install": "installed", "evidence_status": "manufacturer_specification", "evidence_ids": []}
    if defect == "unknown_value":
        cap["value"] = {"kind": "unknown"}; cap["evidence_status"] = "unknown"
    elif defect == "estimate":
        cap["evidence_status"] = "inferred_estimate"
    elif defect == "no_provenance":
        cap["evidence_status"] = "unknown"
    elif defect == "install_unknown":
        cap["install"] = "unknown"
    elif defect == "optional":
        cap["install"] = "optional_not_installed"
    elif defect == "wrong_unit":
        v = cap["value"]
        for side in ("q", "lo", "hi"):
            if side in v:
                v[side]["unit"] = "K" if v[side]["unit"] == "mK" else "X"
        if v["kind"] in ("flag", "count"):
            cap["value"] = {"kind": "max", "q": {"value": 1, "unit": "X"}}   # wrong shape
    return cap


DEFECTS = ["unknown_value", "estimate", "no_provenance", "install_unknown", "optional", "wrong_unit", "missing"]


def _docs(n=120, seed=7):
    rng = random.Random(seed)
    docs = []
    for i in range(n):
        bad_key = rng.choice(KEYS)
        defect = rng.choice(DEFECTS)
        caps = []
        for k in KEYS:
            if k == bad_key:
                if defect != "missing":
                    caps.append(_cap(k, defect))
            else:
                caps.append(_cap(k, None))
        cfg = {"id": f"rand{i}", "equipment_id": "random", "name": f"random {i}", "capabilities": caps}
        exp = {"id": "e", "name": "e", "industry": rng.choice(["any", "food_and_agriculture", "a brand-new industry"]),
               "requirements": [{**r, "mandatory": True, "origin": "user_entered", "rationale": "", "evidence_ids": []} for r in REQS],
               "confirmed": True}
        docs.append((cfg, exp, bad_key, defect))
    return docs


def test_lean_never_accepts_defective_capability(lean_available):
    docs = _docs()
    results = lean_runner.run_batch([(c, e) for c, e, _, _ in docs])
    for (cfg, _, key, defect), r in zip(docs, results):
        assert r["verdict"] != "ACCEPT", (key, defect)
        o = next(c["outcome"] for c in r["checks"] if c["key"] == key)
        assert o != "pass", (key, defect, o)
        if defect == "optional":
            assert r["verdict"] == "REJECT"
        else:
            assert r["verdict"] == "NEED_MORE_INFORMATION", (key, defect)


def test_control_all_good_accepts(lean_available):
    cfg = {"id": "good", "equipment_id": "x", "name": "good", "capabilities": [_cap(k, None) for k in KEYS]}
    exp = {"id": "e", "name": "e", "industry": "x", "confirmed": True,
           "requirements": [{**r, "mandatory": True, "origin": "user_entered", "rationale": "", "evidence_ids": []} for r in REQS]}
    assert lean_runner.run_check(cfg, exp)["verdict"] == "ACCEPT"


def test_z3_tier1_never_proposes_defective_configuration():
    docs = _docs(60, seed=11)
    cfgs = [c for c, _, _, d in docs if d != "optional"]
    exp = docs[0][1]
    res = ConfigurationSearch(cfgs).search(exp, allow_hypothetical_options=False, allow_pending_information=False)
    assert res.candidates == []
    res2 = ConfigurationSearch(cfgs).search(exp, allow_hypothetical_options=False, allow_pending_information=True)
    assert res2.candidates, "pending-information tier should still propose candidates"
    for cand in res2.candidates:
        assert cand.kind == "pending_information" and cand.assumed_unknown and cand.verified is False


def test_missing_value_does_not_become_zero_or_infinity(client):
    """Requirements of 0 or a huge number on an UNKNOWN capability are still not met."""
    for v in (0, 10**15):
        edit = [{"key": "temperature.range", "constraint": {"kind": "at_most", "q": {"value": v, "unit": "mK"}}}]
        r = client.post("/verify", json={"experiment_id": "chem_low_temperature_raman", "configuration_id": "linkam_thms600_heating_only",
                                         "confirmed": True, "requirement_edits": edit}).json()
        o = next(c["outcome"] for c in r["checks"] if c["key"] == "temperature.range")
        assert o == "unknown" and r["verdict"] != "ACCEPT"
