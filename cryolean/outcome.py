"""The two-line outcome shown under the verdict, built from what the user chose:
step 1 (their experiment, with the values they entered) and step 2 (the cryostat they picked).

  1. compatibility: the experiment is / might be / is not compatible with the chosen cryostat (the Lean verdict).
  2. run time:      runs / might run / does not run on that cryostat, and how long:
                    cooldown + run_duration, where run_duration is the duration the USER entered in step 1 and the
                    cooldown is the one the user entered (parameter 'cooldown_time') or else the cooldown documented
                    for the step-2 cryostat. CryoLean never supplies the experiment's duration itself.

The sum is exact (rationals) and is an estimate from those two numbers, never a verdict; the state follows Lean."""
from __future__ import annotations

from fractions import Fraction

from . import schedule, units

COMPATIBILITY = {
    "REQUIREMENTS_MET": ("compatible", "is compatible with"),
    "NEED_MORE_INFORMATION": ("might_be_compatible", "might be compatible with"),
    "DOES_NOT_MEET_REQUIREMENTS": ("not_compatible", "is not compatible with"),
}


def _hm(x: Fraction) -> str:
    """'1 h 30 min', '45 min', '2 d 3 h' (rounded up to whole minutes)."""
    m = -(-x.numerator // (x.denominator * 60))
    d, rem = divmod(m, 1440)
    h, mins = divmod(rem, 60)
    return " ".join(([f"{d} d"] if d else []) + ([f"{h} h"] if h else []) + ([f"{mins} min"] if mins or not (d or h) else []))


def _user_seconds(experiment: dict, name: str) -> Fraction | None:
    """A duration the user entered (origin user_entered), in seconds; None if not entered or not a time."""
    p = next((p for p in experiment.get("params", []) if p.get("name") == name), None)
    v = p.get("value") if p else None
    if not p or p.get("origin") != "user_entered" or not isinstance(v, dict):
        return None
    try:
        if units.unit(v["unit"]).dim != units.unit("s").dim:
            return None
        return Fraction(units.to_si(v["value"], v["unit"]))
    except Exception:
        return None


def _list(items: list, n: int = 3) -> str:
    return ", ".join(items[:n]) + (f" and {len(items) - n} more" if len(items) > n else "")


def card(verdict: str, experiment: dict, cfg_doc: dict, exp_doc: dict, failed: list, missing: list) -> dict:
    exp_name = experiment.get("plain_name") or experiment.get("name") or experiment.get("id")
    machine = cfg_doc.get("name") or cfg_doc.get("id")
    state, phrase = COMPATIBILITY[verdict]
    if verdict == "REQUIREMENTS_MET":
        detail = "Every requirement you set in step 1 is met by the documented values of this cryostat (decided by Lean)."
    elif verdict == "DOES_NOT_MEET_REQUIREMENTS":
        detail = f"Not met: {_list(failed)}."
    elif not exp_doc.get("confirmed"):
        detail = "Confirm the requirements in step 1 to get a decided answer."
    else:
        detail = f"Not documented yet for this cryostat: {_list(missing)}."

    run = _user_seconds(experiment, "run_duration")
    user_cool = _user_seconds(experiment, "cooldown_time")
    cool = user_cool if user_cool is not None else schedule._cooldown_seconds(cfg_doc)
    cool_src = "you entered" if user_cool is not None else "documented for this cryostat" if cool is not None else None
    total = cool + run if cool is not None and run is not None else None
    need = ([] if run is not None else ["how long your experiment runs (step 1: run_duration)"]) + \
           ([] if cool is not None else ["the cryostat's cooldown time (not documented; you can enter cooldown_time)"])
    breakdown = (f"cooldown {_hm(cool)} ({cool_src}) + your experiment {_hm(run)}" if total is not None else None)

    if verdict == "DOES_NOT_MEET_REQUIREMENTS":
        t_state, t_label, t_detail = "does_not_run", f"Does not run on {machine}", "The experiment cannot be run on this cryostat."
        total = None   # no run time for an experiment that cannot run here
    elif verdict == "REQUIREMENTS_MET":
        t_state = "runs"
        t_label = f"Runs on {machine} in about {_hm(total)}" if total is not None else f"Runs on {machine}"
        t_detail = breakdown + "." if total is not None else "For the time, enter " + "; ".join(need) + "."
    else:
        t_state = "might_run"
        t_label = f"Might run on {machine} in about {_hm(total)}" if total is not None else f"Might run on {machine}"
        t_detail = (f"If the open requirements are met: {breakdown}." if total is not None
                    else "For the time, enter " + "; ".join(need) + ".")
    return {
        "compatibility": {"state": state, "label": f"Your experiment “{exp_name}” {phrase} {machine}",
                          "detail": detail, "experiment": exp_name, "machine": machine, "decided_by": "Lean 4 checker"},
        "run_time": {"state": t_state, "label": t_label, "detail": t_detail,
                     "total_seconds": None if total is None else str(total), "total_display": None if total is None else _hm(total),
                     "run_seconds": None if run is None else str(run), "cooldown_seconds": None if cool is None else str(cool),
                     "cooldown_source": cool_src, "needs": need,
                     "basis": "cooldown + the run_duration you entered (exact sum; an estimate, not a verdict)"},
    }
