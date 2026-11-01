"""Z3 SMT engine: runs AFTER the Lean verdict and produces suggestions.

* ``all_conflicts`` — capability facts and parameter values are *tracked
  assumptions*; requirements and coupled relations are tracked constraints.  The
  unsatisfiable cores name which requirement conflicts with which documented
  fact (with evidence ids).
* ``requirements_self_consistent`` — requirements that contradict each other
  independently of any machine.
* ``rank_alternatives`` — evaluates every registered configuration, optionally
  adding documented optional accessories (minimised with Optimize), and ranks
  them by documented criteria.
* ``suggest_parameters`` — for a failing coupled relation, optimises each
  user-adjustable parameter.

The per-key logic mirrors the Lean checker (`checkCapability`, `combineAny`):
install state first, then provenance, then the value; any-of requirements fail
only when every key fails.  Z3 works on the SAME documents Lean reads, with exact
rationals.  Nothing here is a verdict: every suggestion is re-checked by Lean.
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from fractions import Fraction

import z3

from . import units

TRUSTED = {"manufacturer_specification", "experimental_observation", "reference_data", "user_entered",
           "certified_simulation"}
DIMLESS = (0, 0, 0, 0, 0, 0, 0)


def frac(q: dict) -> Fraction:
    return Fraction(int(q["num"]), int(q["den"]))


def dim(q: dict) -> tuple:
    return units.dims_of(q)


def rv(x: Fraction):
    return z3.Q(x.numerator, x.denominator)


def lookup(cfg_doc: dict, key: str):
    return next((c for c in cfg_doc["capabilities"] if c["key"] == key), None)


def usable(c) -> bool:
    return c is not None and c["install"] == "installed" and c["evidence_status"] in TRUSTED and c["value"]["kind"] != "unknown"


def describe_cap(c) -> str:
    v = c["value"]
    k = v["kind"]
    if k == "range":
        return f"{units.display(frac(v['lo']), dim(v['lo']))} to {units.display(frac(v['hi']), dim(v['hi']))}"
    if k in ("max", "min"):
        return f"{k} {units.display(frac(v['q']), dim(v['q']))}"
    if k == "flag":
        return "present" if v["b"] else "absent"
    if k == "count":
        return f"count {v['n']}"
    if k == "enum":
        return v["s"]
    if k == "set":
        return "{" + ", ".join(v["xs"]) + "}"
    return "UNKNOWN"


class Unknown(Exception):
    pass


class Unsupported(Exception):
    pass


def _param(exp_doc: dict, name: str):
    p = next((p for p in exp_doc.get("params", []) if p["name"] == name), None)
    if p is None or p.get("value") is None or p.get("origin") not in TRUSTED:
        return None
    return p["value"]


def _sel_value(c: dict, sel: str):
    v = c["value"]
    if sel == "lo" and v["kind"] == "range":
        return frac(v["lo"]), dim(v["lo"])
    if sel == "hi" and v["kind"] == "range":
        return frac(v["hi"]), dim(v["hi"])
    if sel in ("max", "min") and v["kind"] == sel:
        return frac(v["q"]), dim(v["q"])
    if sel == "count" and v["kind"] == "count":
        return Fraction(v["n"]), DIMLESS
    raise Unsupported(f"selector {sel} does not match {c['key']}")


def encode_expr(e: dict, cfg_doc: dict, exp_doc: dict, var_for: dict | None = None, cap_vars: dict | None = None):
    """Returns (z3 term, dim). `var_for` maps parameter names, `cap_vars` maps (key, sel) to z3 variables."""
    op = e["op"]
    if op == "lit":
        return rv(frac(e["q"])), dim(e["q"])
    if op == "param":
        if var_for and e["name"] in var_for:
            return var_for[e["name"]]
        q = _param(exp_doc, e["name"])
        if q is None:
            raise Unknown(f"parameter {e['name']} missing")
        return rv(frac(q)), dim(q)
    if op == "cap":
        c = lookup(cfg_doc, e["key"])
        if not usable(c):
            raise Unknown(f"capability {e['key']} not documented/installed/trusted")
        val, d = _sel_value(c, e["sel"])
        if cap_vars is not None and (e["key"], e["sel"]) in cap_vars:
            return cap_vars[(e["key"], e["sel"])][0], d
        return rv(val), d
    if op in ("add", "sub"):
        a, da = encode_expr(e["a"], cfg_doc, exp_doc, var_for, cap_vars)
        b, db = encode_expr(e["b"], cfg_doc, exp_doc, var_for, cap_vars)
        if da != db:
            raise Unsupported("dimension mismatch")
        return (a + b if op == "add" else a - b), da
    if op == "mul":
        a, da = encode_expr(e["a"], cfg_doc, exp_doc, var_for, cap_vars)
        b, db = encode_expr(e["b"], cfg_doc, exp_doc, var_for, cap_vars)
        return a * b, tuple(x + y for x, y in zip(da, db))
    if op == "neg":
        a, da = encode_expr(e["a"], cfg_doc, exp_doc, var_for, cap_vars)
        return -a, da
    raise Unsupported(f"op {op}")


def eval_const(t) -> Fraction:
    s = z3.simplify(t)
    if z3.is_rational_value(s):
        return Fraction(s.numerator_as_long(), s.denominator_as_long())
    raise Unsupported("not a rational constant")


def _walk(x, op):
    out = []
    if isinstance(x, dict):
        if x.get("op") == op:
            out.append(x)
        for v in x.values():
            out += _walk(v, op)
    elif isinstance(x, list):
        for v in x:
            out += _walk(v, op)
    return out


def _param_names(e) -> set:
    return {x["name"] for x in _walk(e, "param")}


# ---------------------------------------------------------------------------- conditions
def _cond_ok(c: dict, cfg_doc: dict, exp_doc: dict) -> str:
    """'holds' | 'fails' | 'unknown' — mirrors Lean's evalCond."""
    if c["kind"] == "cap_flag":
        cap = lookup(cfg_doc, c["key"])
        if cap is None:
            return "unknown"
        if cap["install"] == "optional_not_installed":
            if cap["evidence_status"] not in TRUSTED:
                return "unknown"
            return "holds" if not c["b"] else "fails"
        if usable(cap) and cap["value"]["kind"] == "flag":
            return "holds" if cap["value"]["b"] == c["b"] else "fails"
        return "unknown"
    q = _param(exp_doc, c["name"])
    if q is None or dim(q) != dim(c["q"]):
        return "unknown"
    v, bound = frac(q), frac(c["q"])
    ok = v <= bound if c["kind"] == "param_at_most" else bound <= v
    return "holds" if ok else "fails"


def conds(item: dict, cfg_doc: dict, exp_doc: dict) -> str:
    rs = [_cond_ok(c, cfg_doc, exp_doc) for c in item.get("conditions", [])]
    if "fails" in rs:
        return "fails"
    return "holds" if all(r == "holds" for r in rs) else "unknown"


# ---------------------------------------------------------------------------- per-key semantics (mirrors checkCapability)
def _is_absence(cons: dict) -> bool:
    return cons["kind"] == "absent" or (cons["kind"] == "flag_is" and cons.get("b") is False)


def _value_formula(cons: dict, value: dict, var):
    """Formula over the capability variable `var` for a constraint; None if not comparable (Lean: unsupported)."""
    k = cons["kind"]
    vk = value["kind"]
    if k in ("point_within", "at_least", "at_most", "range_within") and vk in ("range", "max", "min"):
        lo, hi = var if vk == "range" else (var, var)
        qdim = dim(value["lo"]) if vk == "range" else dim(value["q"])
        if k == "point_within" and vk == "range" and dim(cons["q"]) == qdim:
            x = rv(frac(cons["q"]))
            return z3.And(lo <= x, x <= hi)
        if k == "range_within" and vk == "range" and dim(cons["lo"]) == qdim and dim(cons["hi"]) == qdim:
            if frac(cons["lo"]) > frac(cons["hi"]):
                return None                      # inverted interval: Lean reports unsupported
            return z3.And(lo <= rv(frac(cons["lo"])), rv(frac(cons["hi"])) <= hi)
        if k == "at_least" and vk in ("max", "range") and dim(cons["q"]) == qdim:
            return rv(frac(cons["q"])) <= hi
        if k == "at_most" and vk in ("min", "range") and dim(cons["q"]) == qdim:
            return lo <= rv(frac(cons["q"]))
        return None
    if k in ("present", "absent", "flag_is") and vk == "flag":
        want = True if k == "present" else False if k == "absent" else bool(cons["b"])
        return var == z3.BoolVal(want)
    if k in ("count_at_least", "count_equals") and vk == "count":
        return (var >= cons["n"]) if k == "count_at_least" else (var == cons["n"])
    if k == "enum_in" and vk == "enum":
        return z3.BoolVal(value["s"] in cons["allowed"])
    if k == "set_contains" and vk == "set":
        return z3.BoolVal(all(x in value["xs"] for x in cons["needed"]))
    return None


def _cap_var(key: str, value: dict):
    vk = value["kind"]
    if vk == "range":
        return (z3.Real(f"cap[{key}].lo"), z3.Real(f"cap[{key}].hi"))
    if vk in ("max", "min"):
        return z3.Real(f"cap[{key}]")
    if vk == "flag":
        return z3.Bool(f"cap[{key}]")
    if vk == "count":
        return z3.Int(f"cap[{key}]")
    return None


def _cap_fact(var, value: dict):
    vk = value["kind"]
    if vk == "range":
        return z3.And(var[0] == rv(frac(value["lo"])), var[1] == rv(frac(value["hi"])))
    if vk in ("max", "min"):
        return var == rv(frac(value["q"]))
    if vk == "flag":
        return var == z3.BoolVal(value["b"])
    if vk == "count":
        return var == value["n"]
    return z3.BoolVal(True)


def key_status(cfg_doc: dict, key: str, cons: dict) -> dict:
    """One key, exactly as Lean's checkCapability classifies it.
    kinds: 'pass' | 'fail' | 'unknown' | 'unsupported' | 'formula' (documented value, decided by Z3) |
           'option' (documented optional accessory, not installed, whose documented value could satisfy it)."""
    cap = lookup(cfg_doc, key)
    if cap is None:
        return {"kind": "unknown", "why": "not documented"}
    if cap["install"] == "optional_not_installed":
        # mirrors Lean checkCapability: a "not fitted" record needs trusted provenance for pass AND fail
        if cap["evidence_status"] not in TRUSTED:
            return {"kind": "unknown", "why": f"'not installed' claim has evidence {cap['evidence_status']}"}
        if _is_absence(cons):
            return {"kind": "pass", "cap": cap}
        st = {"kind": "fail", "cap": cap, "why": "option not installed"}
        if cap["value"]["kind"] != "unknown":
            var = _cap_var(key, cap["value"])
            f = _value_formula(cons, cap["value"], var)
            if f is not None:
                s = z3.Solver()
                s.add(_cap_fact(var, cap["value"]), f)
                if s.check() == z3.sat:
                    st["option_satisfies"] = (var, f)
        return st
    if cap["install"] == "unknown":
        return {"kind": "unknown", "why": "install status unknown"}
    if cap["evidence_status"] not in TRUSTED:
        return {"kind": "unknown", "why": f"evidence {cap['evidence_status']}"}
    if cap["value"]["kind"] == "unknown":
        return {"kind": "unknown", "why": "value UNKNOWN"}
    var = _cap_var(key, cap["value"])
    f = _value_formula(cons, cap["value"], var)
    if f is None:
        return {"kind": "unsupported", "why": "dimension or shape mismatch"}
    return {"kind": "formula", "cap": cap, "var": var, "formula": f}


def _formula_sat(st) -> bool:
    s = z3.Solver()
    s.add(_cap_fact(st["var"], st["cap"]["value"]), st["formula"])
    return s.check() == z3.sat


def _relevant(items):
    return [(i, it) for i, it in enumerate(items) if it["mandatory"] and it.get("applicable", True)]


def _req_label(i: int, r: dict) -> str:
    return f"req#{i}:" + "|".join(r["keys"])


# ---------------------------------------------------------------------------- conflict explanation
def explain_conflict(cfg_doc: dict, exp_doc: dict) -> dict:
    """One minimal unsat core of (mandatory, applicable requirements + coupled relations) against tracked facts.
    Only requirements whose every key is decidable from documented facts are encoded (mirrors combineAny)."""
    s = z3.Solver()
    s.set(unsat_core=True)
    info, skipped, added = {}, [], set()

    def track(label, formula, meta):
        s.assert_and_track(formula, z3.Bool(label))
        info[label] = meta

    def track_fact(key, cap, var=None, text=None):
        label = f"fact:{key}" if var is not None else f"fact:{key}:not_installed"
        if label in added:
            return
        added.add(label)
        if var is None:
            track(label, z3.Not(z3.Bool(f"installed[{key}]")),
                  {"kind": "fact", "key": key, "text": f"{key} is an option that is not installed", "evidence_ids": cap.get("evidence_ids", [])})
        else:
            track(label, _cap_fact(var, cap["value"]),
                  {"kind": "fact", "key": key, "text": text or f"{key} documented as {describe_cap(cap)} ({cap['evidence_status']})",
                   "evidence_ids": cap.get("evidence_ids", [])})

    for i, r in _relevant(exp_doc["requirements"]):
        label = _req_label(i, r)
        cstate = conds(r, cfg_doc, exp_doc)
        if cstate != "holds":
            if cstate == "unknown":
                skipped.append({"item": label, "reason": "a condition depends on missing information"})
            continue
        sts = [(k, key_status(cfg_doc, k, r["constraint"])) for k in r["keys"]]
        if any(st["kind"] in ("unknown", "unsupported") for _, st in sts):
            skipped.append({"item": label, "reason": "; ".join(f"{k}: {st.get('why', st['kind'])}" for k, st in sts
                                                                if st["kind"] in ("unknown", "unsupported"))})
            continue
        alts = []
        for k, st in sts:
            if st["kind"] == "pass":
                alts.append(z3.BoolVal(True))
            elif st["kind"] == "fail":
                track_fact(k, st["cap"])
                alts.append(z3.Bool(f"installed[{k}]"))
            else:
                track_fact(k, st["cap"], st["var"])
                alts.append(st["formula"])
        track(label, z3.Or(*alts) if len(alts) > 1 else alts[0],
              {"kind": "requirement", "index": i, "keys": r["keys"], "constraint": r["constraint"], "origin": r["origin"],
               "evidence_ids": r.get("evidence_ids", [])})

    for i, c in _relevant(exp_doc.get("coupled", [])):
        label = f"coupled#{i}:{c['id']}"
        if conds(c, cfg_doc, exp_doc) != "holds":
            continue
        try:
            pvars = {}
            for n in sorted(_param_names(c)):
                q = _param(exp_doc, n)
                if q is None:
                    raise Unknown(f"parameter {n} missing")
                v = z3.Real(f"param[{n}]")
                pvars[n] = (v, dim(q))
                plabel = f"param:{n}"
                if plabel not in added:
                    added.add(plabel)
                    p = next(p for p in exp_doc["params"] if p["name"] == n)
                    track(plabel, v == rv(frac(q)), {"kind": "parameter", "name": n,
                                                    "text": f"{n} = {units.display(frac(q), dim(q))} ({p.get('origin')})"})
            cvars = {}
            for ref in _walk(c, "cap"):
                cap = lookup(cfg_doc, ref["key"])
                if not usable(cap):
                    raise Unknown(f"capability {ref['key']} not documented/installed/trusted")
                val, d = _sel_value(cap, ref["sel"])
                v = z3.Real(f"cap[{ref['key']}].{ref['sel']}")
                cvars[(ref["key"], ref["sel"])] = (v, d)
                flabel = f"fact:{ref['key']}.{ref['sel']}"
                if flabel not in added:
                    added.add(flabel)
                    track(flabel, v == rv(val), {"kind": "fact", "key": ref["key"],
                                                 "text": f"{ref['key']} documented as {units.display(val, d)} ({cap['evidence_status']})",
                                                 "evidence_ids": cap.get("evidence_ids", [])})
            for val_pair in c.get("validity", []):
                a, da = encode_expr(val_pair["a"], cfg_doc, exp_doc)
                b, db = encode_expr(val_pair["b"], cfg_doc, exp_doc)
                if da != db or not z3.is_true(z3.simplify(a <= b)):
                    raise Unsupported("outside the model's validity range")
            lhs, dl = encode_expr(c["lhs"], cfg_doc, exp_doc, pvars, cvars)
            rhs, dr = encode_expr(c["rhs"], cfg_doc, exp_doc, pvars, cvars)
            if dl != dr:
                raise Unsupported("dimension mismatch")
        except (Unknown, Unsupported) as e:
            skipped.append({"item": label, "reason": str(e)})
            continue
        track(label, lhs <= rhs, {"kind": "coupled", "index": i, "id": c["id"], "name": c["name"], "model": c["model"],
                                  "evidence_ids": c.get("evidence_ids", [])})

    cores = []
    if s.check() == z3.unsat:
        core = [str(x) for x in s.unsat_core()]
        items = [info[l] | {"label": l} for l in core]
        reqs = [i for i in items if i["kind"] in ("requirement", "coupled")]
        facts = [i for i in items if i["kind"] in ("fact", "parameter")]
        text = " AND ".join(_short(i) for i in reqs) + " cannot hold together with " + "; ".join(i["text"] for i in facts)
        cores.append({"requirements": reqs, "facts": facts, "explanation": text})
    return {"engine": f"z3 {z3.get_version_string()}", "status": "unsat" if cores else "sat_on_documented_facts",
            "conflicts": cores, "not_encoded": skipped}


def _short(i: dict) -> str:
    if i["kind"] == "requirement":
        c = i["constraint"]
        k = c["kind"]
        if "q" in c:
            return f"{'/'.join(i['keys'])} {k.replace('_', ' ')} {units.display(frac(c['q']), dim(c['q']))}"
        if k == "range_within":
            return f"{'/'.join(i['keys'])} covers {units.display(frac(c['lo']), dim(c['lo']))} to {units.display(frac(c['hi']), dim(c['hi']))}"
        return f"{'/'.join(i['keys'])} {k.replace('_', ' ')}"
    return i["name"]


def all_conflicts(cfg_doc: dict, exp_doc: dict, max_cores: int = 8) -> dict:
    """Enumerate independent minimal conflicts by removing each found core's items and re-solving."""
    cores, first = [], None
    work = copy.deepcopy(exp_doc)
    for _ in range(max_cores):
        res = explain_conflict(cfg_doc, work)
        if first is None:
            first = res
        if not res["conflicts"]:
            break
        core = res["conflicts"][0]
        cores.append(core)
        drop_r = {i["index"] for i in core["requirements"] if i["kind"] == "requirement"}
        drop_c = {i["index"] for i in core["requirements"] if i["kind"] == "coupled"}
        if not drop_r and not drop_c:
            break
        work["requirements"] = [r for j, r in enumerate(work["requirements"]) if j not in drop_r]
        work["coupled"] = [c for j, c in enumerate(work.get("coupled", [])) if j not in drop_c]
    return {"engine": f"z3 {z3.get_version_string()}", "status": "unsat" if cores else "sat_on_documented_facts",
            "conflicts": cores, "not_encoded": (first or {}).get("not_encoded", []),
            "note": "Each conflict is a minimal unsat core: the listed requirements cannot all hold given the listed documented facts. "
                    "Items depending on missing information are listed under not_encoded (they are never treated as satisfied)."}


def requirements_self_consistent(exp_doc: dict) -> dict:
    """Are the experiment's own numeric requirements jointly satisfiable by SOME capability values?"""
    s = z3.Solver()
    s.set(unsat_core=True)
    by_key, info = {}, {}
    for i, r in _relevant(exp_doc["requirements"]):
        if r.get("conditions") or len(r["keys"]) != 1:
            continue
        key = r["keys"][0]
        c = r["constraint"]
        k = c["kind"]
        lo, hi = by_key.setdefault(key, (z3.Real(f"x[{key}].lo"), z3.Real(f"x[{key}].hi")))
        if k == "point_within":
            f = z3.And(lo <= rv(frac(c["q"])), rv(frac(c["q"])) <= hi)
        elif k == "range_within" and frac(c["lo"]) <= frac(c["hi"]):
            f = z3.And(lo <= rv(frac(c["lo"])), rv(frac(c["hi"])) <= hi)
        elif k == "at_least":
            f = rv(frac(c["q"])) <= hi
        elif k == "at_most":
            f = lo <= rv(frac(c["q"]))
        else:
            continue
        label = f"req#{i}:{key}"
        s.assert_and_track(z3.And(f, lo <= hi), z3.Bool(label))
        info[label] = r
    st = s.check()
    core = [str(x) for x in s.unsat_core()] if st == z3.unsat else []
    return {"consistent": st != z3.unsat, "conflicting_requirements": [info[l]["keys"] for l in core]}


# ---------------------------------------------------------------------------- per-configuration evaluation
@dataclass
class Evaluation:
    configuration_id: str
    equipment_id: str
    status: str                      # satisfiable | needs_options | pending_information | conflict
    added_options: list = field(default_factory=list)
    unknown_items: list = field(default_factory=list)
    failing_items: list = field(default_factory=list)
    min_relative_margin: str | None = None


def evaluate(cfg_doc: dict, exp_doc: dict, allow_options: bool = True) -> Evaluation:
    """Which mandatory items pass, fail, need a documented option, or are unknown (Lean semantics)."""
    opt = z3.Optimize()
    add_vars, fails, unknowns, margins = {}, [], [], []
    for i, r in _relevant(exp_doc["requirements"]):
        label = _req_label(i, r)
        cstate = conds(r, cfg_doc, exp_doc)
        if cstate == "fails":
            continue
        if cstate == "unknown":
            unknowns.append(label)
            continue
        sts = [(k, key_status(cfg_doc, k, r["constraint"])) for k in r["keys"]]
        passes = [st for _, st in sts if st["kind"] == "pass" or (st["kind"] == "formula" and _formula_sat(st))]
        if passes:
            for st in passes:
                if st["kind"] == "formula":
                    m = _margin(r["constraint"], st["cap"]["value"])
                    if m is not None:
                        margins.append(m)
                    break
            continue
        options = [(k, st) for k, st in sts if st["kind"] == "fail" and "option_satisfies" in st]
        if allow_options and options:
            alts = []
            for k, st in options:
                a = add_vars.setdefault(k, z3.Bool(f"add[{k}]"))
                var, f = st["option_satisfies"]
                alts.append(z3.And(a, _cap_fact(var, st["cap"]["value"]), f))
            opt.add(z3.Or(*alts))
            continue
        if any(st["kind"] in ("unknown", "unsupported") for _, st in sts):
            unknowns.append(label)
        else:
            fails.append(label)
    for i, c in _relevant(exp_doc.get("coupled", [])):
        label = f"coupled#{i}:{c['id']}"
        cstate = conds(c, cfg_doc, exp_doc)
        if cstate == "fails":
            continue
        if cstate == "unknown":
            unknowns.append(label)
            continue
        try:
            for v in c.get("validity", []):
                a, da = encode_expr(v["a"], cfg_doc, exp_doc)
                b, db = encode_expr(v["b"], cfg_doc, exp_doc)
                if da != db or not z3.is_true(z3.simplify(a <= b)):
                    raise Unsupported("outside validity")
            lhs, dl = encode_expr(c["lhs"], cfg_doc, exp_doc)
            rhs, dr = encode_expr(c["rhs"], cfg_doc, exp_doc)
            if dl != dr:
                raise Unsupported("dimension")
            if z3.is_true(z3.simplify(lhs <= rhs)):
                l, rr = eval_const(lhs), eval_const(rhs)
                if rr != 0:
                    margins.append((rr - l) / abs(rr))
            else:
                fails.append(label)
        except (Unknown, Unsupported):
            unknowns.append(label)
    if add_vars:
        opt.minimize(z3.Sum([z3.If(a, 1, 0) for a in add_vars.values()]))
    added = []
    if not fails and add_vars and opt.check() == z3.sat:
        m = opt.model()
        added = sorted(k for k, a in add_vars.items() if z3.is_true(m.eval(a, model_completion=True)))
    status = "conflict" if fails else ("pending_information" if unknowns else ("needs_options" if added else "satisfiable"))
    mm = min(margins) if margins else None
    return Evaluation(cfg_doc["id"], cfg_doc["equipment_id"], status, added, unknowns, fails,
                      None if mm is None else f"{float(mm):.4g}")


def _margin(cons: dict, value: dict) -> Fraction | None:
    """Relative slack of a numeric requirement (documented ranking criterion)."""
    k, vk = cons["kind"], value["kind"]
    try:
        if k == "at_least":
            cap = frac(value["q"]) if vk == "max" else frac(value["hi"])
            req = frac(cons["q"])
            return (cap - req) / abs(req) if req else None
        if k == "at_most":
            cap = frac(value["q"]) if vk == "min" else frac(value["lo"])
            req = frac(cons["q"])
            return (req - cap) / abs(req) if req else None
    except KeyError:
        return None
    return None


def _count_passes(cfg_doc: dict, exp_doc: dict) -> int:
    n = 0
    for _, r in _relevant(exp_doc["requirements"]):
        if conds(r, cfg_doc, exp_doc) != "holds":
            continue
        for k in r["keys"]:
            st = key_status(cfg_doc, k, r["constraint"])
            if st["kind"] == "pass" or (st["kind"] == "formula" and _formula_sat(st)):
                n += 1
                break
    return n


def hypothetical(cfg_doc: dict, added: list[str]) -> dict:
    d = copy.deepcopy(cfg_doc)
    d["id"] = f"{cfg_doc['id']}+{'+'.join(added)}"
    d["name"] = f"{cfg_doc.get('name', cfg_doc['id'])} (hypothetical: with {', '.join(added)} installed)"
    for c in d["capabilities"]:
        if (c["key"] in added or any(c["key"] == a + ".temperature" for a in added)) and c["install"] == "optional_not_installed":
            c["install"] = "installed"
    return d


RANK = {"satisfiable": 0, "needs_options": 1, "pending_information": 2, "conflict": 3}


def rank_alternatives(pairs: list[tuple[dict, dict]], allow_options: bool = True,
                      reported_equipment: list[str] | None = None, models: dict | None = None) -> list[dict]:
    """Ranking criteria (documented, in order):
      1. Z3 status tier (satisfiable < needs documented options < pending information < conflict)
      2. fewest added optional accessories
      3. the equipment model is named in the experiment's own sources (reported_equipment)
      4. fewest unknown items
      5. most mandatory items documented as passing
      6. largest smallest relative margin over numeric requirements"""
    names = [n.lower() for n in (reported_equipment or [])]
    evs = []
    for cfg_doc, exp_doc in pairs:
        ev = evaluate(cfg_doc, exp_doc, allow_options)
        base = cfg_doc["id"].split("+")[0].split("~")[0]
        model = ((models or {}).get(base) or "").lower()
        named = any(n in model for n in names) if names else False
        evs.append((ev, cfg_doc, exp_doc, named, _count_passes(cfg_doc, exp_doc)))
    evs.sort(key=lambda t: (RANK[t[0].status], len(t[0].added_options), 0 if t[3] else 1, len(t[0].unknown_items),
                            -t[4], -(float(t[0].min_relative_margin) if t[0].min_relative_margin else -1e9)))
    return [{"evaluation": {**ev.__dict__, "named_in_sources": named, "documented_passes": passes},
             "configuration_document": hypothetical(c, ev.added_options) if ev.added_options else c,
             "experiment_document": e} for ev, c, e, named, passes in evs]


# ---------------------------------------------------------------------------- parameter suggestions
def suggest_parameters(cfg_doc: dict, exp_doc: dict, coupled_ids: list[str], adjustable: dict[str, dict]) -> list[dict]:
    """For each failing coupled relation, the best value of each adjustable parameter (others fixed) such that
    lhs <= rhs and the model's validity bounds hold. `adjustable`: {param: {"adjustable": "decrease"|"increase", "integer": bool}}."""
    out = []
    for c in exp_doc.get("coupled", []):
        if c["id"] not in coupled_ids:
            continue
        for n in sorted(_param_names(c)):
            meta = adjustable.get(n)
            if not meta or not meta.get("adjustable"):
                continue
            current = _param(exp_doc, n)
            if current is None:
                continue
            d = dim(current)
            is_int = bool(meta.get("integer"))
            v = z3.Int(f"opt[{n}]") if is_int else z3.Real(f"opt[{n}]")
            vr = z3.ToReal(v) if is_int else v
            try:
                lhs, _ = encode_expr(c["lhs"], cfg_doc, exp_doc, {n: (vr, d)})
                rhs, _ = encode_expr(c["rhs"], cfg_doc, exp_doc, {n: (vr, d)})
                cons = [lhs <= rhs, vr >= 0]
                for val in c.get("validity", []):
                    a, _ = encode_expr(val["a"], cfg_doc, exp_doc, {n: (vr, d)})
                    b, _ = encode_expr(val["b"], cfg_doc, exp_doc, {n: (vr, d)})
                    cons.append(a <= b)
            except (Unknown, Unsupported) as e:
                out.append({"coupled_id": c["id"], "parameter": n, "status": "not_computable", "reason": str(e)})
                continue
            best = _optimise(v, vr, cons, meta["adjustable"], is_int)
            entry = {"coupled_id": c["id"], "model": c["model"], "parameter": n, "direction": meta["adjustable"],
                     "current": units.display(frac(current), d), "current_exact": str(frac(current))}
            if best is None:
                entry.update({"status": "no_feasible_value", "reason": "no value of this parameter alone satisfies the relation"})
            else:
                entry.update({"status": "found", "suggested_exact": str(best), "suggested": units.display(best, d),
                              "suggested_quantity": {"num": best.numerator, "den": best.denominator,
                                                     "dim": {k: x for k, x in zip(units.DIM_KEYS, d) if x}}})
            out.append(entry)
    return out


def _optimise(v, vr, cons, direction, is_int) -> Fraction | None:
    """Exact optimum for linear relations (Optimize); for non-linear ones, the boundary root found by nlsat,
    rounded INTO the feasible side to 4 significant digits (then re-checked by Lean)."""
    s = z3.Solver()
    s.add(*cons)
    if s.check() != z3.sat:
        return None
    o = z3.Optimize()
    o.add(*cons)
    # 'decrease' parameters (current, line count): the largest value that still fits;
    # 'increase' parameters (time budget): the smallest value that fits.
    if direction == "decrease":
        o.maximize(v)
    else:
        o.minimize(v)
    try:
        if o.check() == z3.sat:
            val = o.model().eval(v, model_completion=True)
            if z3.is_int_value(val):
                return Fraction(val.as_long())
            if z3.is_rational_value(val):
                return Fraction(val.numerator_as_long(), val.denominator_as_long())
    except z3.Z3Exception:
        pass
    s = z3.Solver()
    s.add(*cons)
    s.add(cons[0].arg(0) == cons[0].arg(1))
    if s.check() == z3.sat:
        val = s.model().eval(vr, model_completion=True)
        txt = (val.approx(12) if z3.is_algebraic_value(val) else val).as_decimal(12).rstrip("?")
        rounded = _round_inward(Fraction(txt), direction)
        chk = z3.Solver()
        chk.add(*[z3.substitute(c_, (vr, rv(rounded))) for c_ in cons])
        if chk.check() == z3.sat:
            return rounded
    return None


def _round_inward(x: Fraction, direction: str) -> Fraction:
    """4 significant digits, rounded toward the feasible side (down for 'decrease', up for 'increase')."""
    if x == 0:
        return x
    e = math.floor(math.log10(abs(float(x)))) - 3
    step = Fraction(10) ** e
    k = x / step
    k = math.floor(k) if direction == "decrease" else math.ceil(k)
    return k * step
