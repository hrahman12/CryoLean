"""Z3 campaign scheduler (untrusted) + Lean `validSchedule` (trusted).

    experiments ──► Lean verdict per experiment ──► only ACCEPTED ones ("only feasible experiments")
                                                          │
                     Z3 Optimize: start_i >= cooldown, start_i + d_i <= run length,
                     pairwise disjoint, minimise makespan  (proposed slots)
                                                          │
                     Lean `check-schedule` (validSchedule_sound / _bounds / _disjoint /
                     _only_accepted)  ──►  Schedule OK / rejected

Durations come from each experiment's `run_duration` parameter (supplied by the user,
user_entered); the cooldown is the configuration's documented `cooldown_time.max`.
"""
from __future__ import annotations

import copy
from fractions import Fraction

import z3

from . import lean_runner, serialize, units, verifier
from .catalog import Catalog

SECONDS = {"s": 1}


def hours(x: Fraction) -> str:
    h = x / 3600
    return f"{float(h):g} h" if h.denominator in (1, 2, 4, 5, 10, 20) else f"{float(h):.3f} h"


def _q_seconds(x: Fraction) -> dict:
    return {"num": x.numerator, "den": x.denominator, "dim": {"s": 1}}


def _cooldown_seconds(cfg_doc: dict) -> Fraction | None:
    c = next((c for c in cfg_doc["capabilities"] if c["key"] == "cooldown_time.max"), None)
    if not c or c["install"] != "installed" or c["value"].get("kind") != "min":
        return None
    if c["evidence_status"] not in ("manufacturer_specification", "experimental_observation", "reference_data",
                                    "certified_simulation", "user_entered"):
        return None
    q = c["value"]["q"]
    if units.dims_of(q) != units.dims_of({"dim": SECONDS}):
        return None
    return Fraction(q["num"], q["den"])


def _duration(exp_doc: dict) -> Fraction | None:
    p = next((p for p in exp_doc.get("params", []) if p["name"] == "run_duration"), None)
    if not p or p.get("value") is None:
        return None
    q = p["value"]
    if units.dims_of(q) != units.dims_of({"dim": SECONDS}):
        return None
    return Fraction(q["num"], q["den"])


def propose(cooldown: Fraction, run_length: Fraction, durations: list[tuple[str, Fraction]]) -> dict:
    """Z3 Optimize: earliest-finishing packing of the experiments into one run (exact rationals)."""
    o = z3.Optimize()
    starts = {eid: z3.Real(f"start[{eid}]") for eid, _ in durations}
    makespan = z3.Real("makespan")
    labels = {}
    for eid, d in durations:
        s = starts[eid]
        lab = z3.Bool(f"fits[{eid}]")
        o.add(z3.Implies(lab, z3.And(s >= z3.Q(cooldown.numerator, cooldown.denominator),
                                     s + z3.Q(d.numerator, d.denominator) <= z3.Q(run_length.numerator, run_length.denominator))))
        labels[eid] = lab
        o.add(makespan >= s + z3.Q(d.numerator, d.denominator))
    for i, (a, da) in enumerate(durations):
        for b, db in durations[i + 1:]:
            o.add(z3.Or(starts[a] + z3.Q(da.numerator, da.denominator) <= starts[b],
                        starts[b] + z3.Q(db.numerator, db.denominator) <= starts[a]))
    # check feasibility with every experiment included; if not, find which ones conflict (unsat core)
    s = z3.Solver()
    s.set(unsat_core=True)
    for eid, d in durations:
        s.assert_and_track(z3.And(starts[eid] >= z3.Q(cooldown.numerator, cooldown.denominator),
                                  starts[eid] + z3.Q(d.numerator, d.denominator) <= z3.Q(run_length.numerator, run_length.denominator)),
                           z3.Bool(f"window[{eid}]"))
    for i, (a, da) in enumerate(durations):
        for b, db in durations[i + 1:]:
            s.add(z3.Or(starts[a] + z3.Q(da.numerator, da.denominator) <= starts[b],
                        starts[b] + z3.Q(db.numerator, db.denominator) <= starts[a]))
    if s.check() == z3.unsat:
        core = sorted(str(x)[len("window["):-1] for x in s.unsat_core())
        total = sum((d for _, d in durations), Fraction(0))
        return {"status": "unsat", "conflicting_experiments": core,
                "explanation": (f"the experiments {core} cannot all fit between the end of cooldown ({hours(cooldown)}) "
                                f"and the end of the run ({hours(run_length)}): {hours(run_length - cooldown)} available, "
                                f"{hours(total)} needed")}
    for lab in labels.values():
        o.add(lab)
    o.minimize(makespan)
    if o.check() != z3.sat:
        return {"status": "unknown"}
    m = o.model()

    def val(t) -> Fraction:
        v = m.eval(t, model_completion=True)
        return Fraction(v.numerator_as_long(), v.denominator_as_long())
    slots = sorted(((eid, val(starts[eid])) for eid, _ in durations), key=lambda t: t[1])
    return {"status": "sat", "slots": [{"experiment_id": e, "start": st} for e, st in slots], "makespan": val(makespan)}


def schedule_campaign(catalog: Catalog, configuration_id: str, experiment_ids: list[str], run_length: dict,
                      durations: dict[str, dict], parameters: dict | None = None, confirmed: bool = False) -> dict:
    """Pack experiments into one run of a configuration. Z3 proposes; Lean decides (validSchedule)."""
    run_L = units.to_si(run_length["value"], run_length["unit"])
    if units.unit(run_length["unit"]).dim != units.unit("s").dim:
        raise ValueError("run_length must be a time")
    feasible, excluded, docs = [], [], {}
    cfg_doc = None
    for eid in experiment_ids:
        params = dict((parameters or {}).get(eid, {}))
        if eid in durations:
            params["run_duration"] = durations[eid]
        ex = serialize.working_experiment(catalog, eid, params or None, None, confirmed)
        cd, ed, _, _ = verifier.build_documents(catalog, ex, configuration_id)
        cfg_doc = cd
        r = lean_runner.check(cd, ed)
        if r["verdict"] == "REQUIREMENTS_MET":
            feasible.append(eid)
            docs[eid] = ed
        else:
            excluded.append({"experiment_id": eid, "lean_verdict": r["verdict"], "reason": r["summary"]})
    out = {"configuration_id": configuration_id, "run_length": hours(run_L),
           "feasible_experiments": feasible, "excluded_experiments": excluded,
           "note": "Z3 proposes the slots (a hint); only the Lean validSchedule result decides."}
    if not feasible:
        out.update({"z3": {"status": "nothing_to_schedule"}, "lean": None, "schedule_ok": False})
        return out
    cooldown = _cooldown_seconds(cfg_doc)
    durs = [(e, _duration(docs[e])) for e in feasible]
    missing = [e for e, d in durs if d is None]
    if cooldown is None or missing:
        out.update({"z3": {"status": "missing_information",
                           "missing": (["cooldown_time.max (documented, trusted) for this configuration"] if cooldown is None else [])
                                      + [f"run_duration for {e}" for e in missing]},
                    "lean": None, "schedule_ok": False})
        return out
    prop = propose(cooldown, run_L, durs)
    out["z3"] = {k: v for k, v in prop.items() if k not in ("slots", "makespan")}
    if prop["status"] != "sat":
        out.update({"lean": None, "schedule_ok": False})
        return out
    out["z3"]["makespan"] = hours(prop["makespan"])
    out["cooldown"] = hours(cooldown)
    out["timeline"] = [{"experiment_id": s["experiment_id"], "start": hours(s["start"]),
                        "stop": hours(s["start"] + dict(durs)[s["experiment_id"]])} for s in prop["slots"]]
    order = [s["experiment_id"] for s in prop["slots"]]
    doc = {"configuration": cfg_doc, "experiments": [docs[e] for e in order],
           "slots": [{"experiment_id": s["experiment_id"], "start": _q_seconds(s["start"])} for s in prop["slots"]],
           "run_length": _q_seconds(run_L)}
    lean = lean_runner.check_schedule(doc)
    out.update({"lean": lean, "schedule_ok": bool(lean.get("valid")), "lean_input": doc})
    return out


def check_schedule_document(doc: dict) -> dict:
    """Run Lean validSchedule on an externally proposed schedule (e.g. a hand-edited one)."""
    return lean_runner.check_schedule(copy.deepcopy(doc))
