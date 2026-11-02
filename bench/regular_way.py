"""The regular way: how "can this cryostat run my experiment?" is decided today, without CryoLean.

These checkers are deliberately ordinary Python. They are NOT verified. They read the SAME input documents the
Lean checker reads (`serialize.configuration_doc` / `serialize.experiment_doc`), so every difference between their
answers and CryoLean's is a difference in *method*, never in data.

Three versions, each a step closer to CryoLean (an ablation):

R1  spec-sheet checklist   One datasheet line per requirement, compared on its own. A number on the sheet counts
                           whatever its source (manufacturer, estimate, unsourced). A line the sheet is silent on does
                           not block: answer NO only if some line visibly fails, otherwise YES. This is the vendor
                           buying-guide procedure ("check temperature, field, sample space, wiring ...").
R2  careful spreadsheet    Same lines, but a blank is "TBD": YES only if every line is a documented pass; any blank
                           gives NEED INFO. Still one line at a time; still trusts any number on the sheet.
R3  physics-aware script   R2 plus the coupled physics (heat budget, Joule heating, ramp time, cooldown + run time,
                           contraction, optics) computed in floating point from whatever numbers are listed,
                           with no validity range (the cooling power quoted at some temperature is used as is).
                           This is what a strong engineer would vibe-code in an afternoon.

All three respect what the sheet states about install status ("optional, not fitted" / "not available" means absent),
so none of them is a strawman that confuses a brochure option with the installed machine.

CryoLean (the Lean checker) adds what none of these has: only sourced numbers can decide, the coupled physics is
exact and refuses to extrapolate outside its validity range, and every verdict is backed by theorems.
"""
from __future__ import annotations

from fractions import Fraction

MET, NOT, NI = "REQUIREMENTS_MET", "DOES_NOT_MEET_REQUIREMENTS", "NEED_MORE_INFORMATION"
SHORT = {MET: "YES", NOT: "NO", NI: "NEED INFO"}
ABSENT = ("optional_not_installed", "not_available")
DIMS = ("K", "m", "kg", "s", "A", "mol", "cd")


# ------------------------------------------------------------------------------------------- numbers
def frac(q) -> Fraction:
    return Fraction(int(q["num"]), int(q["den"]))


def flt(q) -> float:
    return int(q["num"]) / int(q["den"])


def dim(q) -> tuple:
    d = q.get("dim") or {}
    return tuple(int(d.get(k, 0)) for k in DIMS)


# ------------------------------------------------------------------------------------------- one datasheet line
def value_outcome(con: dict, val: dict) -> str:
    """Compare one requirement with one documented value: pass / fail / unknown / unsupported.
    The regular way compares like units (a person would not compare tesla with kelvin either)."""
    k, vk = con["kind"], val.get("kind")
    if vk in (None, "unknown"):
        return "unknown"
    if k in ("present", "absent", "flag_is"):
        want = True if k == "present" else False if k == "absent" else bool(con["b"])
        return ("pass" if bool(val["b"]) == want else "fail") if vk == "flag" else "unsupported"
    if k == "count_at_least":
        return ("pass" if con["n"] <= val["n"] else "fail") if vk == "count" else "unsupported"
    if k == "count_equals":
        return ("pass" if con["n"] == val["n"] else "fail") if vk == "count" else "unsupported"
    if k == "enum_in":
        return ("pass" if val["s"] in con["allowed"] else "fail") if vk == "enum" else "unsupported"
    if k == "set_contains":
        return ("pass" if set(con["needed"]) <= set(val["xs"]) else "fail") if vk == "set" else "unsupported"
    if k == "point_within" and vk == "range":
        if not dim(con["q"]) == dim(val["lo"]) == dim(val["hi"]):
            return "unsupported"
        return "pass" if frac(val["lo"]) <= frac(con["q"]) <= frac(val["hi"]) else "fail"
    if k == "range_within" and vk == "range":
        if not dim(con["lo"]) == dim(con["hi"]) == dim(val["lo"]) == dim(val["hi"]):
            return "unsupported"
        return "pass" if frac(val["lo"]) <= frac(con["lo"]) and frac(con["hi"]) <= frac(val["hi"]) else "fail"
    if k == "at_least" and vk in ("max", "range"):
        m = val["q"] if vk == "max" else val["hi"]
        return ("pass" if frac(con["q"]) <= frac(m) else "fail") if dim(m) == dim(con["q"]) else "unsupported"
    if k == "at_most" and vk in ("min", "range"):
        m = val["q"] if vk == "min" else val["lo"]
        return ("pass" if frac(m) <= frac(con["q"]) else "fail") if dim(m) == dim(con["q"]) else "unsupported"
    return "unsupported"


def lookup(cfg: dict, key: str):
    return next((c for c in cfg["capabilities"] if c["key"] == key), None)


def key_outcome(cfg: dict, con: dict, key: str) -> str:
    """What the sheet says about one key. Provenance is not looked at: a number on the sheet is a number."""
    c = lookup(cfg, key)
    if c is None or c["install"] == "unknown":
        return "unknown"
    if c["install"] in ABSENT:
        return "pass" if con["kind"] == "absent" or (con["kind"] == "flag_is" and not con["b"]) else "fail"
    return value_outcome(con, c["value"])


def cond(cfg: dict, exp: dict, c: dict) -> str:
    """holds / fails / unknown, from whatever the sheet and the experiment say (provenance not looked at)."""
    if c["kind"] == "cap_flag":
        cap = lookup(cfg, c["key"])
        if cap is None or cap["install"] == "unknown":
            return "unknown"
        if cap["install"] in ABSENT:
            return "holds" if c["b"] is False else "fails"
        v = cap["value"]
        return ("holds" if v["b"] == c["b"] else "fails") if v.get("kind") == "flag" else "unknown"
    p = next((p for p in exp["params"] if p["name"] == c["name"]), None)
    if p is None or p.get("value") is None or dim(p["value"]) != dim(c["q"]):
        return "unknown"
    v, q = frac(p["value"]), frac(c["q"])
    ok = v <= q if c["kind"] == "param_at_most" else q <= v
    return "holds" if ok else "fails"


def line_outcomes(cfg: dict, exp: dict) -> list[tuple[str, str]]:
    """(requirement label, outcome) for every mandatory, applicable requirement: the datasheet lines."""
    out = []
    for r in exp["requirements"]:
        if not (r.get("mandatory", True) and r.get("applicable", True)):
            continue
        label = " | ".join(r["keys"])
        cs = [cond(cfg, exp, c) for c in r.get("conditions", [])]
        if "fails" in cs:
            out.append((label, "not_applicable"))
            continue
        if "unknown" in cs:
            out.append((label, "unknown"))
            continue
        os_ = [key_outcome(cfg, r["constraint"], k) for k in r["keys"]]
        if "pass" in os_:
            o = "pass"
        elif os_ and all(o == "fail" for o in os_):
            o = "fail"
        elif "unknown" in os_:
            o = "unknown"
        else:
            o = "unsupported"
        out.append((label, o))
    return out


# ------------------------------------------------------------------------------------------- coupled physics in floats
class Missing(Exception):
    pass


def _sel(v: dict, sel: str) -> float:
    kind = v.get("kind")
    if kind == "range" and sel in ("lo", "hi"):
        return flt(v[sel])
    if kind in ("max", "min") and sel == kind:
        return flt(v["q"])
    if kind == "count" and sel == "count":
        return float(v["n"])
    raise Missing(f"no {sel} value")


def eval_float(x: dict, cfg: dict, exp: dict) -> float:
    """Evaluate a coupled-constraint expression in floats from whatever numbers are listed (any provenance)."""
    op = x["op"]
    if op == "lit":
        return flt(x["q"])
    if op == "cap":
        c = lookup(cfg, x["key"])
        if c is None or c["install"] in ABSENT or c["install"] == "unknown":
            raise Missing(x["key"])
        return _sel(c["value"], x["sel"])
    if op == "param":
        p = next((p for p in exp["params"] if p["name"] == x["name"]), None)
        if p is None or p.get("value") is None:
            raise Missing(x["name"])
        return flt(p["value"])
    if op == "neg":
        return -eval_float(x["a"], cfg, exp)
    a, b = eval_float(x["a"], cfg, exp), eval_float(x["b"], cfg, exp)
    return a + b if op == "add" else a - b if op == "sub" else a * b


def coupled_outcomes_float(cfg: dict, exp: dict) -> list[tuple[str, str]]:
    out = []
    for c in exp.get("coupled", []):
        if not (c.get("mandatory", True) and c.get("applicable", True)):
            continue
        cs = [cond(cfg, exp, d) for d in c.get("conditions", [])]
        if "fails" in cs:
            out.append(("model:" + c["model"], "not_applicable"))
            continue
        if "unknown" in cs:
            out.append(("model:" + c["model"], "unknown"))
            continue
        try:
            lhs, rhs = eval_float(c["lhs"], cfg, exp), eval_float(c["rhs"], cfg, exp)
        except Missing:
            out.append(("model:" + c["model"], "unknown"))
            continue
        out.append(("model:" + c["model"], "pass" if lhs <= rhs else "fail"))
    return out


# ------------------------------------------------------------------------------------------- verdicts
def r1(cfg: dict, exp: dict) -> str:
    """Spec-sheet checklist: NO only if a line visibly fails; silence never blocks."""
    return NOT if any(o == "fail" for _, o in line_outcomes(cfg, exp)) else MET


def _three_valued(outs: list[tuple[str, str]]) -> str:
    os_ = [o for _, o in outs]
    if "fail" in os_:
        return NOT
    if os_ and all(o in ("pass", "not_applicable") for o in os_) and "pass" in os_:
        return MET
    return NI


def r2(cfg: dict, exp: dict) -> str:
    """Careful spreadsheet: blanks are TBD, but lines are still checked one at a time."""
    return _three_valued(line_outcomes(cfg, exp))


def r3(cfg: dict, exp: dict) -> str:
    """Physics-aware script: R2 plus the coupled physics in floats, no validity ranges, any listed number."""
    return _three_valued(line_outcomes(cfg, exp) + coupled_outcomes_float(cfg, exp))


METHODS = {"R1": r1, "R2": r2, "R3": r3}
NAMES = {"R1": "Spec-sheet checklist", "R2": "Careful spreadsheet", "R3": "Physics-aware script",
         "CryoLean": "CryoLean (Lean 4)"}


def all_verdicts(cfg: dict, exp: dict) -> dict[str, str]:
    return {k: f(cfg, exp) for k, f in METHODS.items()}
