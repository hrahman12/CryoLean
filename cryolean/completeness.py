"""Data completeness of each cryostat configuration.

A configuration is *complete* for an experiment when its own records suffice to decide the pair: either Lean already
returns a decided verdict (REQUIREMENTS_MET or DOES_NOT_MEET_REQUIREMENTS; by the theorem `verdict_refines` no further
data can change it), or every check that stays undecided is undecided because of something the EXPERIMENT has not
specified (e.g. a measurement current the user has not entered yet), never because the configuration lacks a documented
value. A configuration is *fully documented* when it is complete for every experiment.

Configuration-side gaps (count against the cryostat):
  * a required key with no record, an UNKNOWN value, untrusted evidence (estimate/unknown) or unknown install status;
  * a condition flag (capFlag) on such a record;
  * a coupled-model input that is a capability key and is missing;
  * a model outside its validity region or a shape/dimension mismatch (the documentation does not cover the case).
Experiment-side gaps (do not count): missing or untrusted experiment parameters.

The verdicts themselves always come from Lean; this module only classifies the undecided checks Lean reports.
"""
from __future__ import annotations

from . import lean_runner, serialize, smt, verifier
from .catalog import Catalog

ABSENT = {"optional_not_installed", "not_available"}


def informative(cap: dict | None) -> bool:
    """Mirror of Lean's `Informative`: trusted, and documented absent or installed with a known value."""
    if not cap or cap.get("evidence_status") not in smt.TRUSTED:
        return False
    if cap.get("install") in ABSENT:
        return True
    return cap.get("install") == "installed" and (cap.get("value") or {}).get("kind") != "unknown"


def _caps(cfg_doc: dict) -> dict:
    out = {}
    for c in cfg_doc["capabilities"]:
        out.setdefault(c["key"], c)            # first match, like Lean's lookup
    return out


def classify(cfg_doc: dict, exp_doc: dict, result: dict) -> dict:
    """Split the undecided mandatory checks of one Lean result into configuration-side and experiment-side gaps."""
    caps = _caps(cfg_doc)
    params = {p["name"] for p in exp_doc.get("params", [])}
    reqs = {i: r for i, r in enumerate(exp_doc.get("requirements", []))}
    cfg_gaps, exp_gaps = [], []
    for c in result.get("checks", []):
        if not (c.get("mandatory") and c.get("applicable")) or c.get("outcome") not in ("unknown", "unsupported"):
            continue
        keys = c.get("keys") or []
        bad = [k for k in keys if not informative(caps.get(k))]
        if bad:
            cfg_gaps.append("/".join(keys))
            continue
        if c["outcome"] == "unsupported":
            cfg_gaps.append("/".join(keys) + " (shape/units)")
            continue
        # all keys informative: the condition list decided 'unknown'
        req = next((r for r in reqs.values() if r.get("keys") == keys), None)
        conds = (req or {}).get("conditions", [])
        flag_gaps = [d.get("key") for d in conds if d.get("kind") == "cap_flag" and not informative(caps.get(d.get("key")))]
        if flag_gaps:
            cfg_gaps.append("/".join(keys) + " (condition: " + ", ".join(flag_gaps) + ")")
        else:
            exp_gaps.append("/".join(keys) + " (condition on experiment parameters)")
    for c in result.get("coupled_checks", []):
        if not (c.get("mandatory") and c.get("applicable")) or c.get("outcome") not in ("unknown", "unsupported"):
            continue
        whats = []
        for side in ("lhs", "rhs"):
            s = c.get(side) or {}
            if s.get("status") == "missing":
                whats.append(s.get("what"))
        for v in c.get("validity", []):
            for side in ("a", "b"):
                s = v.get(side) or {}
                if s.get("status") == "missing":
                    whats.append(s.get("what"))
        whats = [w for w in dict.fromkeys(whats) if w]
        cfg_side = [w for w in whats if w not in params]
        exp_side = [w for w in whats if w in params]
        if cfg_side:
            cfg_gaps.append(f"{c['model']} (needs {', '.join(cfg_side)})")
        elif exp_side:
            exp_gaps.append(f"{c['model']} (needs {', '.join(exp_side)})")
        else:
            cfg_gaps.append(f"{c['model']} (outside the documented validity range)")
    return {"configuration": cfg_gaps, "experiment": exp_gaps}


def completeness(catalog: Catalog, configuration_ids: list[str] | None = None, experiment_ids: list[str] | None = None,
                 parameters: dict | None = None) -> dict:
    """Run Lean on every (experiment, configuration) pair and report each configuration's data completeness."""
    cfg_ids = configuration_ids or sorted(catalog.configurations)
    exp_ids = experiment_ids or sorted(catalog.experiments)
    pairs, meta = [], []
    for eid in exp_ids:
        ex = serialize.working_experiment(catalog, eid, (parameters or {}).get(eid), None, True)
        for cid in cfg_ids:
            cd, ed, _, _ = verifier.build_documents(catalog, ex, cid)
            pairs.append((cd, ed))
            meta.append((eid, cid))
    results = lean_runner.check_batch(pairs)
    per_cfg = {cid: {"configuration_id": cid, "experiments": len(exp_ids), "complete_for": [], "gaps": {},
                     "experiment_side": {}, "verdicts": {}} for cid in cfg_ids}
    for (eid, cid), (cd, ed), r in zip(meta, pairs, results):
        g = classify(cd, ed, r)
        rec = per_cfg[cid]
        rec["verdicts"][eid] = r["verdict"]
        if r["verdict"] != "NEED_MORE_INFORMATION" or not g["configuration"]:
            rec["complete_for"].append(eid)          # decided, or held up only by the experiment's own parameters
        else:
            rec["gaps"][eid] = g["configuration"]
        if g["experiment"]:
            rec["experiment_side"][eid] = g["experiment"]
    for rec in per_cfg.values():
        rec["score"] = round(len(rec["complete_for"]) / max(1, rec["experiments"]), 3)
        rec["fully_documented"] = len(rec["complete_for"]) == rec["experiments"]
        rec["missing_keys"] = sorted({k for v in rec["gaps"].values() for k in v})
    return {"configurations": per_cfg,
            "fully_documented": sorted(c for c, r in per_cfg.items() if r["fully_documented"]),
            "experiments": exp_ids,
            "rule": "complete for an experiment = Lean's verdict is decided, or the only undecided checks are caused by "
                    "experiment parameters the user has not entered; fully documented = complete for every experiment"}
