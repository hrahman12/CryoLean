#!/usr/bin/env python
"""Performance benchmarks for the CryoLean paper. Every number is a wall-clock measurement on this machine
(claim class MEASURED); every verdict shown next to a timing comes from the compiled Lean checker.

    python paper/scripts/fig_benchmarks.py                    measure what is missing, then plot (~60 min the first time)
    python paper/scripts/fig_benchmarks.py --recompute        re-measure everything
    python paper/scripts/fig_benchmarks.py --recompute lean_scaling,z3_schedule
    python paper/scripts/fig_benchmarks.py --plot-only        plot from the cached measurements

Measurements (raw timings cached in paper/data/bench_*.json; plotted summaries in paper/data/fig_*.json):

B1 bench_lean_scaling    Lean wall time vs the number N of mandatory requirements (synthetic documents: N requirements
                         over a configuration with the N matching capabilities, all documented, installed, trusted) and
                         vs the number k of coupled constraints (the real mxc_wiring_heat_budget relation of Demo B
                         repeated k times on the Bluefors LD400 + HDW documents). Modes: one Lean process per check
                         (lean_runner.check), the Lean process alone (input pre-written, output not parsed), and
                         lean_runner.check_batch of 100 identical pairs (per pair). 7 interleaved repeats + warm-up.
B2 bench_z3_candidates   Z3 smt.rank_alternatives, smt.all_conflicts on every candidate, the find_compatible_equipment
                         search path (rank + Lean check of <= 10 shown candidates) and Lean check_batch of every candidate,
                         vs the number of candidate configurations (the 26 real configurations replicated x1..x16 with
                         perturbed ids), for each of the 11 catalogued experiments. 5 interleaved repeats + warm-up.
B3 bench_z3_schedule     schedule.propose (Z3) vs the number n of experiments (synthetic durations; a run length with
                         25 % slack = satisfiable, and one 30 min too short = unsatisfiable), its first (feasibility)
                         query alone, and Lean check-schedule of the schedule it finds. 5 repeats.
B4 bench_runtime_dist    >= 40 repeated timings: Lean process start, Lean single check (3 representative pairs, one per
                         verdict), Lean batch per pair (the whole 286-pair grid), Z3 all_conflicts (Demo A pair),
                         verifier.check with suggestions (the 3 pairs), with a per-component breakdown.
B5 bench_runtime_family  the 286 real experiment x configuration single checks, 3 interleaved repeats each, grouped by
                         configuration family.
"""
from __future__ import annotations

import argparse
import copy
import gc
import json
import platform
import random
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter, NullLocator
from scipy import stats

from style import *  # noqa: F401,F403  (also puts the repo root on sys.path)

import z3  # noqa: E402

from cryolean import lean_runner, schedule, serialize, smt, units, verifier  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402

SCRIPT = Path(__file__).resolve()

# ---------------------------------------------------------------- benchmark design
NS = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000]     # mandatory requirements (= capabilities)
KS = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]           # coupled constraints
K_BATCH_MAX = 200                                         # check_batch of 100 pairs only up to k = 200 (cost)
SCALING_REPEATS, BATCH_SIZE = 7, 100
FACTORS = [1, 2, 4, 8, 16]                                # 26 x factor candidate configurations
Z3_REPEATS = 5
N_PROPOSE = list(range(2, 10))                            # schedule.propose measured for n = 2..9
N_CENSOR, CENSOR_SECONDS = 10, 300                        # one attempt at n = 10 with a 300 s wall-clock cap
N_FEAS = list(range(2, 17))                               # feasibility query + Lean check-schedule for n = 2..16
DIST_REPEATS = 40
FAMILY_REPEATS = 3

HEAT_EXP, HEAT_CFG, HEAT_MODEL = "quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw", "mxc_wiring_heat_budget"
SCHED_CFG, SCHED_TEMPLATE = "lakeshore_crx_vf", "chem_low_temperature_raman"   # Demo D configuration; accepted profile
REP_PAIRS = {  # the paper's PPMS DynaCool demonstrations: one pair per verdict
    "REQUIREMENTS_MET": ("mat_magnetometry_vsm", "qd_dynacool_14T_eto_vsm_hc"),
    "DOES_NOT_MEET_REQUIREMENTS": ("mat_magnetoresistance_10T", "qd_dynacool_9T_eto_res"),      # Demo A
    "NEED_MORE_INFORMATION": ("mat_magnetoresistance_10T", "qd_dynacool_14T_eto_vsm_hc"),       # honest 14 T demo
}
PAIR_TEXT = {"REQUIREMENTS_MET": "VSM magnetometry on PPMS DynaCool 14 T",
             "DOES_NOT_MEET_REQUIREMENTS": "10 T magnetoresistance on PPMS DynaCool 9 T (Demo A)",
             "NEED_MORE_INFORMATION": "10 T magnetoresistance on PPMS DynaCool 14 T"}
FAMILY_SHORT = {
    "cryogen-free dilution refrigerator measurement system": "Dilution refrigerator (Bluefors LD)",
    "closed-cycle-refrigerator (CCR) cryogenic probe station": "CCR probe station (Lake Shore CRX)",
    "cryogen-free closed-cycle-refrigerator optical cryostat, sample in vacuum, bottom-loading":
        "CCR optical cryostat (Lake Shore CCS)",
    "clinical cryostat for frozen sectioning (encapsulated rotary microtome in a refrigerated cryochamber)":
        "Cryostat microtome (Leica CM1950)",
    "temperature-controlled microscope heating/freezing stage (liquid-nitrogen cooled)": "LN2 microscope stage (Linkam THMS600)",
    "cryogen-free (Cryofree) optical cryostat for spectroscopy": "Optical cryostat (Oxford OptistatDry)",
    "cryogen-free (Cryofree) superconducting magnet system with variable temperature insert":
        "Magnet + VTI (Oxford TeslatronPT)",
    "liquid-helium physical property measurement platform": "LHe PPMS (Quantum Design PPMS)",
    "cryogen-free physical property measurement platform": "Cryogen-free PPMS (QD DynaCool)",
}


# ---------------------------------------------------------------- helpers
def clock(fn, *a, **k):
    """Wall time of one call. The previous result is released and garbage collected BEFORE the clock starts."""
    gc.collect()
    t0 = time.perf_counter()
    out = fn(*a, **k)
    return time.perf_counter() - t0, out


def system_load(seconds: float = 2.0) -> float:
    import psutil
    return psutil.cpu_percent(interval=seconds)


class LoadMonitor:
    """Samples the whole-system CPU utilisation (% of all logical CPUs, includes this benchmark's own process) every
    `period` seconds in a daemon thread while a benchmark runs."""

    def __init__(self, period: float = 2.0):
        import threading
        self.period, self.samples, self._stop = period, [], threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        import psutil
        while not self._stop.wait(self.period):
            self.samples.append(psutil.cpu_percent(interval=None))

    def __enter__(self):
        import psutil
        psutil.cpu_percent(interval=None)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join()

    def summary(self) -> dict:
        return {"period_s": self.period, **(med_iqr(self.samples) if self.samples else {}), "samples": self.samples}


def cpu_name() -> str:
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
        return winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
    except Exception:  # noqa: BLE001
        return platform.processor()


def _sha256(path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def environment() -> dict:
    import psutil
    b = lean_runner.lean_binary()
    return {"env_json": load("env") if (DATA_DIR / "env.json").exists() else None,
            "cpu": cpu_name(), "cpu_id": platform.processor(),
            "physical_cores": psutil.cpu_count(logical=False), "logical_cpus": psutil.cpu_count(logical=True),
            "ram_gib": round(psutil.virtual_memory().total / 2**30, 1), "os": platform.platform(),
            "python": platform.python_version(), "lean": lean_runner.version(), "z3": z3.get_version_string(),
            "lean_binary_bytes": b.stat().st_size if b else None,
            "lean_binary_mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(b.stat().st_mtime)) if b else None,
            "lean_binary_sha256": _sha256(b) if b else None,
            "catalog_db_mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime((ROOT / "data" / "cryolean.db").stat().st_mtime)),
            "timer": "time.perf_counter (wall clock)",
            "gc": "gc.collect() before every timed call; GC enabled during the call",
            "measured_at": time.strftime("%Y-%m-%d %H:%M:%S")}


def med_iqr(v) -> dict:
    a = np.asarray(v, float)
    return {"median": float(np.median(a)), "q1": float(np.percentile(a, 25)), "q3": float(np.percentile(a, 75)),
            "min": float(a.min()), "max": float(a.max()), "n": int(a.size)}


def loglog_fit(x, y) -> dict:
    """OLS of log10(y) on log10(x) over every repeat; slope with a t-based 95 % confidence interval."""
    lx, ly = np.log10(np.asarray(x, float)), np.log10(np.asarray(y, float))
    r = stats.linregress(lx, ly)
    tc = stats.t.ppf(0.975, len(lx) - 2)
    return {"slope": float(r.slope), "ci95": [float(r.slope - tc * r.stderr), float(r.slope + tc * r.stderr)],
            "intercept": float(r.intercept), "r2": float(r.rvalue ** 2), "points": int(len(lx)),
            "x_range": [float(min(x)), float(max(x))]}


def semilog_fit(x, y) -> dict:
    """OLS of log10(y) on x: growth factor 10^slope per unit of x, with a 95 % confidence interval."""
    x, ly = np.asarray(x, float), np.log10(np.asarray(y, float))
    r = stats.linregress(x, ly)
    tc = stats.t.ppf(0.975, len(x) - 2)
    return {"factor_per_step": float(10 ** r.slope),
            "factor_ci95": [float(10 ** (r.slope - tc * r.stderr)), float(10 ** (r.slope + tc * r.stderr))],
            "slope_log10": float(r.slope), "intercept": float(r.intercept), "r2": float(r.rvalue ** 2),
            "points": int(len(x)), "x_range": [float(min(x)), float(max(x))]}


def Q(v, u):
    return units.lean_quantity(v, u)


# ---------------------------------------------------------------- B1 Lean scaling
SHAPES = [  # (shape, documented capability value, constraint it satisfies)
    ("max", lambda: {"kind": "max", "q": Q(20, "T")}, lambda: {"kind": "at_least", "q": Q(9, "T")}),
    ("range", lambda: {"kind": "range", "lo": Q(1, "K"), "hi": Q(400, "K")}, lambda: {"kind": "point_within", "q": Q(4, "K")}),
    ("flag", lambda: {"kind": "flag", "b": True}, lambda: {"kind": "present"}),
    ("count", lambda: {"kind": "count", "n": 48}, lambda: {"kind": "count_at_least", "n": 8}),
    ("min", lambda: {"kind": "min", "q": Q(2, "K")}, lambda: {"kind": "at_most", "q": Q(4, "K")}),
]


def synthetic_pair(n: int):
    """SYNTHETIC: n mandatory requirements, each on its own key, over a configuration documenting exactly those n keys
    (installed, manufacturer_specification); the five constraint shapes cycle; every requirement passes."""
    caps, reqs = [], []
    for i in range(n):
        shape, val, cons = SHAPES[i % len(SHAPES)]
        key = f"synthetic.k{i:05d}.{shape}"
        caps.append({"key": key, "value": val(), "install": "installed", "evidence_status": "manufacturer_specification",
                     "evidence_ids": []})
        reqs.append({"keys": [key], "constraint": cons(), "mandatory": True, "origin": "user_entered"})
    cfg = {"id": f"synthetic_cfg_{n}", "equipment_id": "synthetic", "name": f"synthetic ({n} capabilities)", "capabilities": caps}
    exp = {"id": f"synthetic_exp_{n}", "name": f"synthetic ({n} requirements)", "industry": "synthetic", "params": [],
           "coupled": [], "requirements": reqs, "confirmed": True}
    return cfg, exp


def coupled_pair(cat: Catalog, k: int):
    """REAL documents of Demo B with the real mxc_wiring_heat_budget coupled constraint repeated k times (unique ids,
    parameters and capabilities unchanged)."""
    ex = serialize.working_experiment(cat, HEAT_EXP, None, None, True)
    cd, ed, _, _ = verifier.build_documents(cat, ex, HEAT_CFG)
    base = next(c for c in ed["coupled"] if c["model"] == HEAT_MODEL)
    e2 = copy.deepcopy(ed)
    e2["coupled"] = [dict(copy.deepcopy(base), id=f"{base['id']}~copy{j}") for j in range(k)]
    return cd, e2


def raw_lean(path: str):
    """The Lean process alone: input file already written, stdout captured but not parsed."""
    b = str(lean_runner.lean_binary())
    gc.collect()
    t0 = time.perf_counter()
    p = subprocess.run([b, "check", path], capture_output=True, text=True, encoding="utf-8")
    dt = time.perf_counter() - t0
    if p.returncode != 0:
        raise RuntimeError(p.stdout[:300] + p.stderr[:300])
    return dt, len(p.stdout.encode("utf-8"))


def bench_lean_scaling(cat: Catalog, ns=NS, ks=KS, k_batch_max=K_BATCH_MAX, repeats=SCALING_REPEATS, batch=BATCH_SIZE,
                       seed=1, log=print) -> dict:
    rng = random.Random(seed)
    tmp = Path(tempfile.mkdtemp(prefix="cryolean_bench_"))
    plan = [("requirements", n, True) for n in ns] + [("coupled", k, k <= k_batch_max) for k in ks]
    docs, files, meta = {}, {}, {}
    for kind, n, do_batch in plan:
        cfg, exp = synthetic_pair(n) if kind == "requirements" else coupled_pair(cat, n)
        s = json.dumps({"configuration": cfg, "experiment": exp}, ensure_ascii=False)
        p = tmp / f"{kind}_{n}.json"
        p.write_text(s, encoding="utf-8")
        docs[(kind, n)], files[(kind, n)] = (cfg, exp), str(p)
        meta[(kind, n)] = {"input_bytes": len(s.encode("utf-8")), "batch": do_batch}
    load0 = system_load()
    log("  warm-up")
    for _ in range(5):
        lean_runner.version()
    for (kind, n), (cfg, exp) in docs.items():
        lean_runner.check(cfg, exp)
        raw_lean(files[(kind, n)])
        if meta[(kind, n)]["batch"]:
            dt, res = clock(lean_runner.check_batch, [(cfg, exp)] * batch)
            del res
            log(f"    warm-up batch {kind} {n}: {dt:.2f} s")
    rec = defaultdict(lambda: defaultdict(list))
    floor = []
    for r in range(repeats):
        order = plan[:]
        rng.shuffle(order)
        t_round = time.perf_counter()
        for kind, n, do_batch in order:
            cfg, exp = docs[(kind, n)]
            dt, res = clock(lean_runner.check, cfg, exp)
            rec[(kind, n)]["single"].append(dt)
            m = meta[(kind, n)]
            m["verdict"] = res["verdict"]
            m["checks_returned"] = len(res["checks"]) + len(res["coupled_checks"])
            m.setdefault("verdicts_seen", Counter())[res["verdict"]] += 1
            del res
            dt, out_bytes = raw_lean(files[(kind, n)])
            rec[(kind, n)]["raw"].append(dt)
            m["output_bytes"] = out_bytes
            if do_batch:
                dt, res = clock(lean_runner.check_batch, [(cfg, exp)] * batch)
                if len(res) != batch:
                    raise RuntimeError("batch size mismatch")
                for x in res:
                    m["verdicts_seen"][x["verdict"]] += 1
                del res
                rec[(kind, n)]["batch_per_pair"].append(dt / batch)
            floor.append(clock(lean_runner.version)[0])
        log(f"  round {r + 1}/{repeats}: {time.perf_counter() - t_round:.1f} s")
    rows = []
    for kind, n, do_batch in plan:
        m = meta[(kind, n)]
        rows.append({"kind": kind, "n": n, "verdict": m["verdict"], "checks_returned": m["checks_returned"],
                     "verdicts_seen": dict(m["verdicts_seen"]), "input_bytes_per_pair": m["input_bytes"],
                     "lean_output_bytes_per_pair": m["output_bytes"],
                     "batch_input_bytes": m["input_bytes"] * batch if do_batch else None,
                     "single_s": rec[(kind, n)]["single"], "raw_s": rec[(kind, n)]["raw"],
                     "batch_per_pair_s": rec[(kind, n)]["batch_per_pair"] or None})
    return {"design": {"requirements_N": list(ns), "coupled_k": list(ks), "batch_size": batch, "repeats": repeats,
                       "coupled_batch_k_max": k_batch_max, "order": "interleaved, shuffled per round (seed %d)" % seed,
                       "warm_up": "5 x version, then one run of every (kind, n, mode) before timing",
                       "synthetic": "requirements: synthetic documents (SYNTHETIC); coupled: real Demo B documents with "
                                    "the real mxc_wiring_heat_budget relation repeated k times"},
            "rows": rows, "process_start_s": floor, "system_cpu_percent_before": load0,
            "system_cpu_percent_after": system_load()}


# ---------------------------------------------------------------- B2 Z3 vs number of candidates
def _models(cat):
    return {cid: f"{c.get('manufacturer', '')} {c.get('model', '')} {c.get('name', '')}" for cid, c in cat.configurations.items()}


def search_path(ex: dict, pairs, models):
    """CryoLeanAPI.find_compatible_equipment after document building (same calls, same filter, same Lean entry point)."""
    t0 = time.perf_counter()
    ranked = smt.rank_alternatives(pairs, True, ex.get("reported_equipment", []), models)
    t_rank = time.perf_counter() - t0
    shown = [r for r in ranked if r["evaluation"]["status"] != "conflict"
             and (r["evaluation"]["status"] != "pending_information" or r["evaluation"]["documented_passes"] > 0)][:10]
    t1 = time.perf_counter()
    lean = [lean_runner.check_candidates(r["experiment_document"], [r["configuration_document"]])[0]["verdict"] for r in shown]
    t_lean = time.perf_counter() - t1
    return {"rank_s": t_rank, "lean_shown_s": t_lean, "shown": len(shown),
            "z3_status": dict(Counter(r["evaluation"]["status"] for r in ranked)), "lean_shown": dict(Counter(lean))}


def bench_z3_candidates(cat: Catalog, factors=FACTORS, repeats=Z3_REPEATS, experiments=None, seed=2, log=print) -> dict:
    rng = random.Random(seed)
    exps = experiments or sorted(cat.experiments)
    cfgs = sorted(cat.configurations)
    models = _models(cat)
    base, build_s = {}, {}
    for eid in exps:
        ex = serialize.working_experiment(cat, eid, None, None, True)
        t0 = time.perf_counter()
        base[eid] = (ex, [verifier.build_documents(cat, ex, cid)[:2] for cid in cfgs])
        build_s[eid] = time.perf_counter() - t0

    def pairs_for(eid, f):     # perturbed ids: "<id>~v<j>" (the base id still names the catalogued model)
        return [({**cd, "id": f"{cd['id']}~v{j}"}, ed) for j in range(f) for cd, ed in base[eid][1]]
    load0 = system_load()
    log("  warm-up")
    for eid in exps:
        p = pairs_for(eid, 1)
        search_path(base[eid][0], p, models)
        for cd, ed in p:
            smt.all_conflicts(cd, ed)
        lean_runner.check_batch(p)
    runs = []
    plan = [(eid, f) for eid in exps for f in factors]
    for r in range(repeats):
        order = plan[:]
        rng.shuffle(order)
        t_round = time.perf_counter()
        for eid, f in order:
            ex, pairs = base[eid][0], pairs_for(eid, f)
            dt, sp = clock(search_path, ex, pairs, models)
            gc.collect()
            t0 = time.perf_counter()
            n_cores = 0
            for cd, ed in pairs:
                n_cores += len(smt.all_conflicts(cd, ed)["conflicts"])
            t_conf = time.perf_counter() - t0
            t_batch, res = clock(lean_runner.check_batch, pairs)
            vs = [x["verdict"] for x in res]
            m = len(base[eid][1])
            replicas_agree = all(vs[j * m:(j + 1) * m] == vs[:m] for j in range(f))
            del res
            runs.append({"repeat": r, "experiment": eid, "factor": f, "candidates": len(pairs), "search_path_s": dt,
                         "rank_s": sp["rank_s"], "lean_shown_s": sp["lean_shown_s"], "shown": sp["shown"],
                         "z3_status": sp["z3_status"], "lean_shown": sp["lean_shown"], "conflicts_all_s": t_conf,
                         "unsat_cores_found": n_cores, "lean_batch_s": t_batch, "lean_verdicts": dict(Counter(vs)),
                         "lean_replicas_agree": replicas_agree})
        log(f"  round {r + 1}/{repeats}: {time.perf_counter() - t_round:.1f} s")
    return {"design": {"experiments": exps, "configurations": cfgs, "factors": list(factors),
                       "candidates": [26 * f for f in factors], "repeats": repeats,
                       "perturbed_ids": "<configuration id>~v<j>, j = 0..factor-1 (documents otherwise identical)",
                       "order": "interleaved, shuffled per round (seed %d)" % seed,
                       "document_build_s_26_configurations": build_s},
            "runs": runs, "system_cpu_percent_before": load0, "system_cpu_percent_after": system_load()}


# ---------------------------------------------------------------- B3 Z3 schedule.propose
def synthetic_durations(nmax=16, seed=5):
    """SYNTHETIC run durations: uniform over 1.0, 1.5, ..., 8.0 h (seeded)."""
    rng = random.Random(seed)
    return [Fraction(rng.randint(2, 16), 2) * 3600 for _ in range(nmax)]


def run_lengths(cool: Fraction, durs):
    tot = sum((d for _, d in durs), Fraction(0))
    return {"sat": cool + tot * Fraction(5, 4), "unsat": cool + tot - 1800}


def feasibility_query(cool: Fraction, L: Fraction, durations):
    """The first query schedule.propose issues (identical constraints): is there ANY placement? Returns (status, slots)."""
    starts = {eid: z3.Real(f"start[{eid}]") for eid, _ in durations}
    s = z3.Solver()
    s.set(unsat_core=True)
    for eid, d in durations:
        s.assert_and_track(z3.And(starts[eid] >= z3.Q(cool.numerator, cool.denominator),
                                  starts[eid] + z3.Q(d.numerator, d.denominator) <= z3.Q(L.numerator, L.denominator)),
                           z3.Bool(f"window[{eid}]"))
    for i, (a, da) in enumerate(durations):
        for b, db in durations[i + 1:]:
            s.add(z3.Or(starts[a] + z3.Q(da.numerator, da.denominator) <= starts[b],
                        starts[b] + z3.Q(db.numerator, db.denominator) <= starts[a]))
    st = s.check()
    if st != z3.sat:
        return str(st), None
    m = s.model()
    slots = []
    for eid, _ in durations:
        v = m.eval(starts[eid], model_completion=True)
        slots.append({"experiment_id": eid, "start": Fraction(v.numerator_as_long(), v.denominator_as_long())})
    return "sat", sorted(slots, key=lambda x: x["start"])


def schedule_document(cfg_doc, template, durations, slots, L):
    """Lean check-schedule input: synthetic copies of an accepted real profile, each with its run_duration."""
    exps = {}
    for eid, d in durations:
        e = copy.deepcopy(template)
        e["id"], e["name"] = eid, f"synthetic campaign item {eid}"
        e["params"] = [p for p in e["params"] if p["name"] != "run_duration"] + [
            {"name": "run_duration", "value": {"num": d.numerator, "den": d.denominator, "dim": {"s": 1}}, "origin": "user_entered"}]
        exps[eid] = e
    q = lambda x: {"num": x.numerator, "den": x.denominator, "dim": {"s": 1}}  # noqa: E731
    return {"configuration": cfg_doc, "experiments": [exps[s["experiment_id"]] for s in slots],
            "slots": [{"experiment_id": s["experiment_id"], "start": q(s["start"])} for s in slots], "run_length": q(L)}


def propose_worker(n: int, case: str):
    """Subprocess entry (censored attempt): time one schedule.propose call and print JSON."""
    cool = Fraction(int(sys.argv[sys.argv.index("--cooldown") + 1]))
    durs = [(f"exp{i:02d}", d) for i, d in enumerate(synthetic_durations()[:n])]
    L = run_lengths(cool, durs)[case]
    t0 = time.perf_counter()
    r = schedule.propose(cool, L, durs)
    print(json.dumps({"n": n, "case": case, "status": r["status"], "seconds": time.perf_counter() - t0}), flush=True)


def bench_z3_schedule(cat: Catalog, n_propose=N_PROPOSE, n_feas=N_FEAS, repeats=Z3_REPEATS, n_censor=N_CENSOR,
                      censor_seconds=CENSOR_SECONDS, seed=3, log=print) -> dict:
    rng = random.Random(seed)
    ex = serialize.working_experiment(cat, SCHED_TEMPLATE, {"run_duration": {"value": "6", "unit": "h"}}, None, True)
    cfg_doc, template, _, _ = verifier.build_documents(cat, ex, SCHED_CFG)
    template_verdict = lean_runner.check(cfg_doc, template)["verdict"]
    cool = schedule._cooldown_seconds(cfg_doc)
    if cool is None:
        raise RuntimeError("no documented cooldown")
    all_durs = synthetic_durations()
    inst = {n: [(f"exp{i:02d}", d) for i, d in enumerate(all_durs[:n])] for n in sorted(set(n_propose) | set(n_feas))}
    load0 = system_load()
    for n in (2, 3, 4):                                       # warm-up
        schedule.propose(cool, run_lengths(cool, inst[n])["sat"], inst[n])
    prop, feas, lean_rows = [], [], []
    plan = [(n, c) for n in n_propose for c in ("sat", "unsat")]
    for r in range(repeats):
        order = plan[:]
        rng.shuffle(order)
        t_round = time.perf_counter()
        for n, case in order:
            L = run_lengths(cool, inst[n])[case]
            dt, out = clock(schedule.propose, cool, L, inst[n])
            row = {"repeat": r, "n": n, "case": case, "seconds": dt, "status": out["status"]}
            if out["status"] == "sat":
                row["makespan_s"] = str(out["makespan"])
                row["back_to_back_makespan_s"] = str(cool + sum((d for _, d in inst[n]), Fraction(0)))
                if r == 0:      # the proposed (optimal) schedule, judged by Lean once
                    doc = schedule_document(cfg_doc, template, inst[n], out["slots"], L)
                    row["lean_valid_of_proposed"] = bool(lean_runner.check_schedule(doc).get("valid"))
            prop.append(row)
        log(f"  propose round {r + 1}/{repeats}: {time.perf_counter() - t_round:.1f} s")
        for n in n_feas:
            L = run_lengths(cool, inst[n])["sat"]
            dt, (st, slots) = clock(feasibility_query, cool, L, inst[n])
            Lu = run_lengths(cool, inst[n])["unsat"]
            feas.append({"repeat": r, "n": n, "case": "sat", "seconds": dt, "status": st})
            doc = schedule_document(cfg_doc, template, inst[n], slots, L)
            dt2, res = clock(lean_runner.check_schedule, doc)
            lean_rows.append({"repeat": r, "n": n, "seconds": dt2, "valid": bool(res.get("valid"))})
            if n <= max(n_propose):
                dtu, (stu, _) = clock(feasibility_query, cool, Lu, inst[n])
                feas.append({"repeat": r, "n": n, "case": "unsat", "seconds": dtu, "status": stu})
    censored = []
    if n_censor:
        log(f"  censored attempt n = {n_censor} (cap {censor_seconds} s, sat and unsat in parallel)")
        procs = {case: subprocess.Popen([sys.executable, str(SCRIPT), "--propose-worker", str(n_censor), case,
                                         "--cooldown", str(int(cool))], stdout=subprocess.PIPE, text=True)
                 for case in ("sat", "unsat")}
        t0 = time.perf_counter()
        for case, p in procs.items():
            try:
                out, _ = p.communicate(timeout=max(1.0, censor_seconds - (time.perf_counter() - t0)))
                censored.append({"n": n_censor, "case": case, "finished": True, **json.loads(out.strip().splitlines()[-1])})
            except subprocess.TimeoutExpired:
                p.kill()
                p.communicate()
                censored.append({"n": n_censor, "case": case, "finished": False,
                                 "seconds_lower_bound": censor_seconds, "note": "killed at the wall-clock cap"})
    return {"design": {"configuration": SCHED_CFG, "cooldown_s": str(cool), "cooldown_source": "documented cooldown_time.max",
                       "template_profile": SCHED_TEMPLATE, "template_lean_verdict": template_verdict,
                       "durations_h": [float(d / 3600) for d in all_durs],
                       "durations_rule": "uniform over 1.0..8.0 h in 0.5 h steps, random.Random(5) (SYNTHETIC)",
                       "run_length_rule": {"sat": "cooldown + 1.25 x sum of durations",
                                           "unsat": "cooldown + sum of durations - 30 min"},
                       "n_propose": list(n_propose), "n_feasibility": list(n_feas), "repeats": repeats,
                       "censor": {"n": n_censor, "cap_s": censor_seconds}},
            "propose": prop, "feasibility": feas, "lean_check_schedule": lean_rows, "censored": censored,
            "system_cpu_percent_before": load0, "system_cpu_percent_after": system_load()}


# ---------------------------------------------------------------- B4 runtime distributions
class Breakdown:
    """Timing wrappers (instrumentation only; behaviour unchanged) around the calls verifier.check makes."""
    TARGETS = [(lean_runner, "check", "lean"), (lean_runner, "axiom_audit", "card_audit"),
               (smt, "all_conflicts", "z3"), (smt, "requirements_self_consistent", "z3"),
               (smt, "suggest_parameters", "z3"), (smt, "rank_alternatives", "z3")]

    def __init__(self):
        self.calls = []
        self.orig = {}

    def __enter__(self):
        for mod, name, tag in self.TARGETS:
            fn = getattr(mod, name)
            self.orig[(mod, name)] = fn

            def wrap(*a, _fn=fn, _tag=tag, _name=name, **k):
                t0 = time.perf_counter()
                try:
                    return _fn(*a, **k)
                finally:
                    self.calls.append((_tag, _name, time.perf_counter() - t0))
            setattr(mod, name, wrap)
        return self

    def __exit__(self, *exc):
        for (mod, name), fn in self.orig.items():
            setattr(mod, name, fn)

    def take(self, total: float) -> dict:
        lean = [dt for tag, _, dt in self.calls if tag == "lean"]
        out = {"lean_verdict_s": lean[0] if lean else 0.0, "lean_rechecks_s": sum(lean[1:]), "lean_rechecks": len(lean) - 1,
               "z3_s": sum(dt for tag, _, dt in self.calls if tag == "z3"),
               "card_audit_s": sum(dt for tag, _, dt in self.calls if tag == "card_audit")}
        out["other_python_s"] = total - out["lean_verdict_s"] - out["lean_rechecks_s"] - out["z3_s"] - out["card_audit_s"]
        self.calls = []
        return out


def bench_runtime_dist(cat: Catalog, repeats=DIST_REPEATS, seed=4, log=print) -> dict:
    rng = random.Random(seed)
    docs = {}
    for v, (eid, cid) in REP_PAIRS.items():
        ex = serialize.working_experiment(cat, eid, None, None, True)
        docs[v] = verifier.build_documents(cat, ex, cid)[:2]
    grid = []
    for eid in sorted(cat.experiments):
        ex = serialize.working_experiment(cat, eid, None, None, True)
        for cid in sorted(cat.configurations):
            grid.append(verifier.build_documents(cat, ex, cid)[:2])
    rej = docs["DOES_NOT_MEET_REQUIREMENTS"]
    cats = ["process_start"] + [f"lean_single:{v}" for v in REP_PAIRS] + ["lean_batch_grid", "z3_conflicts:DOES_NOT_MEET_REQUIREMENTS"] \
        + [f"pipeline:{v}" for v in REP_PAIRS]
    t, verdicts, breakdown, info = defaultdict(list), defaultdict(Counter), defaultdict(list), {}

    def once(c):
        if c == "process_start":
            return clock(lean_runner.version)[0]
        if c.startswith("lean_single:"):
            dt, r = clock(lean_runner.check, *docs[c.split(":")[1]])
            verdicts[c][r["verdict"]] += 1
            return dt
        if c == "lean_batch_grid":
            dt, r = clock(lean_runner.check_batch, grid)
            verdicts[c].update(x["verdict"] for x in r)
            return dt / len(grid)
        if c.startswith("z3_conflicts:"):
            dt, r = clock(smt.all_conflicts, *rej)
            info["z3_conflicts_status"] = r["status"]
            info["z3_unsat_cores"] = len(r["conflicts"])
            info["z3_core_text"] = r["conflicts"][0]["explanation"] if r["conflicts"] else None
            return dt
        v = c.split(":")[1]
        eid, cid = REP_PAIRS[v]
        ex = serialize.working_experiment(cat, eid, None, None, True)
        with Breakdown() as bd:
            dt, r = clock(verifier.check, cat, ex, cid, suggestions=True)
            breakdown[c].append(bd.take(dt))
        verdicts[c][r["verdict"]] += 1
        s = r["suggestions"] or {}
        info[c] = {"alternatives": len(s.get("alternatives") or []), "unsat_cores": len((s.get("conflicts") or {}).get("conflicts", [])),
                   "parameter_changes": len(s.get("parameter_changes") or [])}
        return dt
    load0 = system_load()
    log("  warm-up")
    for c in cats:
        once(c)
        once(c)
    t.clear()
    verdicts.clear()
    breakdown.clear()
    for r in range(repeats):
        order = cats[:]
        rng.shuffle(order)
        for c in order:
            t[c].append(once(c))
        if (r + 1) % 10 == 0:
            log(f"  round {r + 1}/{repeats}")
    return {"design": {"repeats": repeats, "pairs": {v: list(p) for v, p in REP_PAIRS.items()}, "grid_pairs": len(grid),
                       "order": "interleaved, shuffled per round (seed %d); 2 warm-up rounds discarded" % seed},
            "seconds": dict(t), "verdicts": {k: dict(v) for k, v in verdicts.items()}, "pipeline_breakdown": dict(breakdown),
            "info": info, "system_cpu_percent_before": load0, "system_cpu_percent_after": system_load()}


# ---------------------------------------------------------------- B5 runtime per family
def bench_runtime_family(cat: Catalog, repeats=FAMILY_REPEATS, seed=6, log=print) -> dict:
    rng = random.Random(seed)
    pairs = []
    for eid in sorted(cat.experiments):
        ex = serialize.working_experiment(cat, eid, None, None, True)
        for cid in sorted(cat.configurations):
            cd, ed, _, _ = verifier.build_documents(cat, ex, cid)
            pairs.append({"experiment": eid, "configuration": cid, "family": cat.configurations[cid].get("family"),
                          "docs": (cd, ed), "input_bytes": len(json.dumps({"configuration": cd, "experiment": ed},
                                                                         ensure_ascii=False).encode("utf-8")),
                          "capabilities": len(cd["capabilities"]), "requirements": len(ed["requirements"]),
                          "coupled": len(ed["coupled"]), "seconds": [], "verdicts": Counter()})
    load0 = system_load()
    for p in pairs[:10]:                                       # warm-up
        lean_runner.check(*p["docs"])
    floor = []
    for r in range(repeats):
        order = list(range(len(pairs)))
        rng.shuffle(order)
        for j, i in enumerate(order):
            p = pairs[i]
            dt, res = clock(lean_runner.check, *p["docs"])
            p["seconds"].append(dt)
            p["verdicts"][res["verdict"]] += 1
            p["checks"] = len(res["checks"]) + len(res["coupled_checks"])
            if j % 10 == 0:
                floor.append(clock(lean_runner.version)[0])
        log(f"  round {r + 1}/{repeats}")
    g = load("e1_grid") if (DATA_DIR / "e1_grid.json").exists() else None
    ref = {(x["experiment"], x["configuration"]): x["verdict"] for x in g["rows"]} if g else {}
    rows = []
    for p in pairs:
        v = p["verdicts"].most_common(1)[0][0]
        rows.append({k: p[k] for k in ("experiment", "configuration", "family", "input_bytes", "capabilities",
                                        "requirements", "coupled", "checks", "seconds")}
                    | {"verdict": v, "verdict_stable": len(p["verdicts"]) == 1, "e1_grid_verdict": ref.get((p["experiment"], p["configuration"]))})
    return {"design": {"repeats": repeats, "pairs": len(pairs), "order": "every pair once per round, shuffled (seed %d)" % seed,
                       "process_start_sampling": "cryolean version after every 10th check"},
            "rows": rows, "process_start_s": floor, "system_cpu_percent_before": load0,
            "system_cpu_percent_after": system_load()}


# ================================================================ plotting
def log_axis_ms(ax, axis="y"):
    """Seconds on a log axis, labelled in ms / s."""
    def fmt(v, _):
        if v <= 0:
            return ""
        if v >= 1:
            return f"{v:g} s"
        return f"{v * 1000:g} ms"
    a = ax.yaxis if axis == "y" else ax.xaxis
    a.set_major_formatter(FuncFormatter(fmt))
    a.set_minor_formatter(NullFormatter())


def ci_text(f, digits=2):
    return f"{f['slope']:.{digits}f} [{f['ci95'][0]:.{digits}f}, {f['ci95'][1]:.{digits}f}]"


# ---------------------------------------------------------------- fig_lean_scaling
def plot_lean_scaling(d: dict, env: dict):
    rows = d["rows"]
    floor = med_iqr(d["process_start_s"])
    fits, summary = {}, {"process_start": floor, "series": []}
    fig, axes = plt.subplots(1, 2, figsize=(COL2, 3.0), sharey=True)
    modes = [("single", "One Lean process per check (lean_runner.check)", NAVY, "o", "-"),
             ("batch_per_pair", "check_batch of 100 pairs, time per pair", ORANGE, "s", "-")]
    fit_from = {"requirements": {"single": 200, "raw": 200, "batch_per_pair": 200},
                "coupled": {"single": 100, "raw": 100, "batch_per_pair": 20}}
    for ax, kind, xlabel, title in [(axes[0], "requirements", "mandatory requirements N (= capabilities)",
                                     "(a) Requirements (synthetic documents)"),
                                    (axes[1], "coupled", "coupled constraints k (Demo B relation repeated)",
                                     "(b) Coupled constraints (real Demo B documents)")]:
        rs = [r for r in rows if r["kind"] == kind]
        ax.axhspan(floor["q1"], floor["q3"], color=GRID, lw=0, zorder=0)
        ax.axhline(floor["median"], color=MUTED, lw=0.8, ls="--", zorder=1)
        for mode, label, col, mk, ls in modes:
            pts = [(r["n"], v) for r in rs for v in (r[mode + "_s"] if mode != "batch_per_pair" else (r["batch_per_pair_s"] or []))]
            if not pts:
                continue
            xs_all, ys_all = zip(*pts)
            jit = np.exp(np.random.default_rng(0).uniform(-0.06, 0.06, len(xs_all)))
            ax.scatter(np.array(xs_all) * jit, ys_all, s=4, color=col, alpha=0.30, lw=0, zorder=2)
            ns = sorted({x for x in xs_all})
            st = [med_iqr([y for x, y in pts if x == n]) for n in ns]
            med = [s["median"] for s in st]
            ax.errorbar(ns, med, yerr=[[s["median"] - s["q1"] for s in st], [s["q3"] - s["median"] for s in st]],
                        color=col, lw=0.9 if mode != "raw" else 0.8, ls=ls, marker=mk, ms=3.2 if mode != "raw" else 2.6,
                        mfc=col if mode != "raw" else "white", mec=col, mew=0.8, capsize=1.5, elinewidth=0.7, zorder=3)
            lo = fit_from[kind][mode]
            fx = [x for x, _ in pts if x >= lo]
            fy = [y for x, y in pts if x >= lo]
            f = loglog_fit(fx, fy) if len(set(fx)) >= 2 else None
            fa = loglog_fit(xs_all, ys_all) if len(set(xs_all)) >= 2 else None
            if f:
                fits[(kind, mode)] = f
            summary["series"].append({"kind": kind, "mode": mode, "n": ns, "stats": st, "fit_upper": f, "fit_all": fa,
                                      "verdicts": [r["verdict"] for r in rs if r["n"] in ns]})
            if mode != "raw" and f:
                xx = np.array([lo, max(fx)], float)
                ax.plot(xx * np.array([0.8, 1.25]), 10 ** (f["intercept"] + f["slope"] * np.log10(xx * np.array([0.8, 1.25]))),
                        color=INK, lw=0.6, ls=(0, (4, 2)), zorder=4)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel(xlabel)
        ax.set_title(title, loc="left", fontsize=8.5)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.grid(True, which="major")
        ax.grid(False, which="minor")
    axes[0].set_ylabel("wall time per check")
    log_axis_ms(axes[0])
    log_axis_ms(axes[1])
    ylo = min(min(min(r["single_s"]) for r in rows), min(min(r["batch_per_pair_s"]) for r in rows if r["batch_per_pair_s"]))
    yhi = max(max(r["single_s"] + (r["batch_per_pair_s"] or [])) for r in rows)
    axes[0].set_ylim(ylo / 1.6, yhi * 2.2)
    # slope annotations (text in ink, next to the fit line's upper end)
    for ax, kind in [(axes[0], "requirements"), (axes[1], "coupled")]:
        lines = []
        for mode, lab in [("single", "one process"), ("batch_per_pair", "batch, per pair")]:
            f = fits.get((kind, mode))
            if f:
                lines.append(f"{lab}: slope {ci_text(f)} (x ≥ {fit_from[kind][mode]})")
        ax.text(0.98, 0.03, "log-log fits, 95% CI\n" + "\n".join(lines), transform=ax.transAxes, ha="right", va="bottom",
                fontsize=6.0, color=INK, linespacing=1.3,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=GRID, lw=0.5))
    handles = [Line2D([], [], color=c, marker=m, ls=ls, lw=0.9, ms=3.2, mfc=(c if mode != "raw" else "white"), label=l)
               for mode, l, c, m, ls in modes]
    handles.append(Line2D([], [], color=INK, ls=(0, (4, 2)), lw=0.6, label="power-law fit (upper decade)"))
    handles.append(Patch(facecolor=GRID, edgecolor=MUTED, ls="--", lw=0.6,
                         label=f"Lean process start (cryolean version): median {floor['median'] * 1000:.0f} ms, IQR"))
    fig.legend(handles=handles, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.0), fontsize=6.5, handlelength=2.4,
               columnspacing=1.2)
    fig.tight_layout(rect=(0, 0, 1, 0.87))
    # the Lean-process-alone timings (input pre-written) stay in the data, not in the plot (too noisy at small N)
    for kind in ("requirements", "coupled"):
        rs = [r for r in rows if r["kind"] == kind]
        summary["series"].append({"kind": kind, "mode": "raw", "n": [r["n"] for r in rs],
                                  "stats": [med_iqr(r["raw_s"]) for r in rs], "verdicts": [r["verdict"] for r in rs],
                                  "fit_upper": None, "fit_all": None})
    summary["fits"] = {f"{k}:{m}": v for (k, m), v in fits.items()}
    return fig, summary


# ---------------------------------------------------------------- fig_z3_scaling
def plot_z3_scaling(dc: dict, ds: dict):
    runs = dc["runs"]
    exps = dc["design"]["experiments"]
    M = sorted({r["candidates"] for r in runs})
    reps = sorted({r["repeat"] for r in runs})
    # per repeat and M: mean over the experiments of the time per call
    def per_rep(key):
        out = {}
        for m in M:
            out[m] = [float(np.mean([r[key] for r in runs if r["candidates"] == m and r["repeat"] == k])) for k in reps]
        return out
    series = [("rank_s", "Z3 rank_alternatives (all candidates)", NAVY, "o", "-"),
              ("conflicts_all_s", "Z3 all_conflicts on every candidate", LAVENDER, "D", "-"),
              ("lean_batch_s", "Lean check_batch of every candidate", ORANGE, "s", "-"),
              ("search_path_s", "search path: Z3 rank + Lean on ≤ 10 shown", ICY, "^", "--")]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(COL2, 3.7))
    summ = {"candidates": M, "series": {}}
    for key, label, col, mk, ls in series:
        pr = per_rep(key)
        st = [med_iqr(pr[m]) for m in M]
        a1.errorbar(M, [s["median"] for s in st], yerr=[[s["median"] - s["q1"] for s in st], [s["q3"] - s["median"] for s in st]],
                    color=col, marker=mk, ms=3.2, lw=0.9, ls=ls, capsize=1.5, elinewidth=0.7, mec=col, zorder=3)
        f = loglog_fit([m for m in M for _ in pr[m]], [v for m in M for v in pr[m]])
        # per-experiment medians (repeat-to-repeat) for the range across experiments
        per_exp = {e: {m: float(np.median([r[key] for r in runs if r["experiment"] == e and r["candidates"] == m])) for m in M}
                   for e in exps}
        summ["series"][key] = {"label": label, "stats": st, "fit": f, "per_experiment_median": per_exp}
    a1.set_xscale("log", base=2)
    a1.set_yscale("log")
    a1.xaxis.set_major_locator(FixedLocator(M))
    a1.xaxis.set_minor_locator(NullLocator())
    a1.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    log_axis_ms(a1)
    a1.set_xlabel("candidate configurations M (26 real, replicated)")
    a1.set_ylabel("wall time per experiment")
    a1.set_title("(a) Equipment search vs candidates", loc="left", fontsize=8.5)
    # direct labels at the right end (ink text, small marker swatch carries the colour)
    ends = sorted(((summ["series"][k]["stats"][-1]["median"], k) for k, *_ in series))
    ypos = []
    for y, k in ends:
        y_lab = y
        if ypos and y_lab < ypos[-1] * 1.45:
            y_lab = ypos[-1] * 1.45
        ypos.append(y_lab)
        f = summ["series"][k]["fit"]
        a1.annotate(f"slope {f['slope']:.2f}", xy=(M[-1], y), xytext=(M[-1] * 1.12, y_lab), fontsize=6.2, color=INK,
                    va="center", ha="left", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.4))
    a1.set_xlim(M[0] / 1.25, M[-1] * 2.6)
    a1.legend(handles=[Line2D([], [], color=c, marker=m, ls=ls, lw=0.9, ms=3.2, label=l) for _, l, c, m, ls in series],
              loc="upper center", bbox_to_anchor=(0.45, -0.2), fontsize=6.0, handlelength=2.2, ncol=1)
    a1.set_ylim(None, max(s["stats"][-1]["q3"] for s in summ["series"].values()) * 2.0)
    # ---- (b) schedule
    prop, feas, leanr, cens = ds["propose"], ds["feasibility"], ds["lean_check_schedule"], ds["censored"]
    ssum = {}
    for case, label, col, mk in [("sat", "Z3 propose, satisfiable (feasibility + makespan optimisation)", NAVY, "o"),
                                 ("unsat", "Z3 propose, unsatisfiable (proof of infeasibility)", ORANGE, "s")]:
        ns = sorted({r["n"] for r in prop if r["case"] == case})
        st = [med_iqr([r["seconds"] for r in prop if r["case"] == case and r["n"] == n]) for n in ns]
        a2.errorbar(ns, [s["median"] for s in st], yerr=[[s["median"] - s["q1"] for s in st], [s["q3"] - s["median"] for s in st]],
                    color=col, marker=mk, ms=3.2, lw=0.9, capsize=1.5, elinewidth=0.7, zorder=3, label=label)
        tail = [(r["n"], r["seconds"]) for r in prop if r["case"] == case and r["n"] >= 6]
        ssum[f"propose_{case}"] = {"n": ns, "stats": st,
                                   "growth_fit_n_ge_6": semilog_fit(*zip(*tail)) if len({n for n, _ in tail}) >= 2 else None,
                                   "statuses": dict(Counter(r["status"] for r in prop if r["case"] == case))}
        for c in cens:
            if c["case"] == case:
                yv = c.get("seconds") if c.get("finished") else c["seconds_lower_bound"]
                xc = c["n"] + (-0.18 if case == "sat" else 0.18)
                a2.plot([xc], [yv], marker=mk, mfc="white", mec=col, ms=4.2, mew=0.9, ls="none", zorder=4)
                if not c.get("finished"):
                    a2.annotate("", xy=(xc, yv * 4.0), xytext=(xc, yv * 1.2),
                                arrowprops=dict(arrowstyle="-|>", color=col, lw=0.8, mutation_scale=6))
    ns = sorted({r["n"] for r in feas if r["case"] == "sat"})
    st = [med_iqr([r["seconds"] for r in feas if r["case"] == "sat" and r["n"] == n]) for n in ns]
    a2.errorbar(ns, [s["median"] for s in st], yerr=[[s["median"] - s["q1"] for s in st], [s["q3"] - s["median"] for s in st]],
                color=LAVENDER, marker="D", ms=2.8, lw=0.9, ls="--", capsize=1.5, elinewidth=0.7, zorder=3,
                label="Z3 feasibility query alone (first step of propose)")
    ssum["feasibility_sat"] = {"n": ns, "stats": st}
    nsu = sorted({r["n"] for r in feas if r["case"] == "unsat"})
    ssum["feasibility_unsat"] = {"n": nsu, "stats": [med_iqr([r["seconds"] for r in feas if r["case"] == "unsat" and r["n"] == n]) for n in nsu]}
    nl = sorted({r["n"] for r in leanr})
    stl = [med_iqr([r["seconds"] for r in leanr if r["n"] == n]) for n in nl]
    a2.errorbar(nl, [s["median"] for s in stl], yerr=[[s["median"] - s["q1"] for s in stl], [s["q3"] - s["median"] for s in stl]],
                color=ICY, marker="^", ms=3.0, lw=0.9, capsize=1.5, elinewidth=0.7, zorder=3,
                label="Lean check-schedule of that schedule")
    ssum["lean_check_schedule"] = {"n": nl, "stats": stl, "all_valid": all(r["valid"] for r in leanr)}
    ssum["censored"] = cens
    a2.set_yscale("log")
    log_axis_ms(a2)
    a2.set_xlabel("experiments in the campaign n")
    a2.set_ylabel("wall time per call")
    a2.set_title("(b) Campaign scheduling vs experiments", loc="left", fontsize=8.5)
    a2.set_xticks(range(2, max(nl) + 1, 2))
    unfinished = [c for c in cens if not c.get("finished")]
    if unfinished:
        c = unfinished[0]
        a2.text(c["n"] + 0.5, c["seconds_lower_bound"],
                f"n = {c['n']}: not finished\nwithin the {c['seconds_lower_bound']} s cap\n(open markers)",
                fontsize=6.0, color=INK2, va="center")
    a2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), fontsize=6.0, handlelength=2.0)
    ymax = max([c.get("seconds") or c.get("seconds_lower_bound") for c in cens] + [max(s["max"] for s in ssum["propose_sat"]["stats"])])
    a2.set_ylim(None, ymax * 6)
    fig.tight_layout(w_pad=1.6)
    return fig, {"candidates": summ, "schedule": ssum}


# ---------------------------------------------------------------- fig_runtime_dist
DIST_ROWS = [("process_start", "Process start only (cryolean version)", "Lean"),
             ("lean_single:REQUIREMENTS_MET", "Single check, one process: MET pair", "Lean"),
             ("lean_single:DOES_NOT_MEET_REQUIREMENTS", "Single check, one process: NOT MET pair", "Lean"),
             ("lean_single:NEED_MORE_INFORMATION", "Single check, one process: NEED INFO pair", "Lean"),
             ("lean_batch_grid", "Batch of all 286 grid pairs, per pair", "Lean"),
             ("z3_conflicts:DOES_NOT_MEET_REQUIREMENTS", "all_conflicts (unsat cores): NOT MET pair", "Z3"),
             ("pipeline:REQUIREMENTS_MET", "verifier.check + suggestions: MET pair", "Pipeline"),
             ("pipeline:DOES_NOT_MEET_REQUIREMENTS", "verifier.check + suggestions: NOT MET pair", "Pipeline"),
             ("pipeline:NEED_MORE_INFORMATION", "verifier.check + suggestions: NEED INFO pair", "Pipeline")]
GROUP_COLOR = {"Lean": NAVY, "Z3": LAVENDER, "Pipeline": ORANGE}
GROUP_TITLE = {"Lean": "Lean checker (compiled; the only source of verdicts)", "Z3": "Z3 (untrusted proposer)",
               "Pipeline": "Full check: Lean verdict, Z3 suggestions, Lean re-checks"}


def hviolin(ax, y, data, color, half=0.36):
    lx = np.log10(np.asarray(data, float))
    if np.ptp(lx) > 0:
        kde = stats.gaussian_kde(lx)
        g = np.linspace(lx.min() - 0.03, lx.max() + 0.03, 240)
        dens = kde(g)
        dens = dens / dens.max() * half
        xs = 10 ** g
        ax.fill_between(xs, y - dens, y + dens, color=color, alpha=0.22, lw=0, zorder=2)
        ax.plot(xs, y - dens, color=color, lw=0.6, zorder=3)
        ax.plot(xs, y + dens, color=color, lw=0.6, zorder=3)
    q1, med, q3 = np.percentile(data, [25, 50, 75])
    ax.add_patch(Rectangle((q1, y - 0.09), q3 - q1, 0.18, fc="white", ec=INK, lw=0.7, zorder=5))
    ax.plot([med, med], [y - 0.09, y + 0.09], color=INK, lw=1.3, zorder=6, solid_capstyle="butt")
    jit = np.random.default_rng(int(y * 7) + 1).uniform(-0.22, 0.22, len(data))
    ax.scatter(data, y + jit, s=2.5, color=color, alpha=0.55, lw=0, zorder=4)


def fmt_time(s: float) -> str:
    return f"{s:.2f} s" if s >= 1 else (f"{s * 1000:.0f} ms" if s >= 0.01 else f"{s * 1000:.1f} ms")


def plot_runtime_dist(d: dict):
    sec = d["seconds"]
    fig = plt.figure(figsize=(COL2, 5.0))
    gs = fig.add_gridspec(2, 1, height_ratios=[3.3, 1.25], hspace=0.55)
    ax = fig.add_subplot(gs[0])
    rows = [r for r in DIST_ROWS if r[0] in sec]
    ys = {}
    y = 0.0
    prev_group = None
    group_y = {}
    for key, label, grp in rows:
        if prev_group is not None and grp != prev_group:
            y += 0.55
        ys[key] = y
        group_y.setdefault(grp, []).append(y)
        prev_group = grp
        y += 1.0
    summary = {}
    for key, label, grp in rows:
        hviolin(ax, ys[key], sec[key], GROUP_COLOR[grp])
        s = med_iqr(sec[key])
        summary[key] = s
        ax.text(1.015, ys[key], f"{fmt_time(s['median'])}  [{fmt_time(s['q1'])}, {fmt_time(s['q3'])}]",
                transform=ax.get_yaxis_transform(), va="center", ha="left", fontsize=6.3, color=INK)
    ax.set_xscale("log")
    log_axis_ms(ax, "x")
    ax.set_yticks([ys[k] for k, _, _ in rows])
    ax.set_yticklabels([lab for _, lab, _ in rows], fontsize=6.6)
    ax.invert_yaxis()
    ax.set_ylim(y - 0.35, -0.75)
    ax.tick_params(axis="y", length=0)
    ax.grid(True, axis="x", which="major")
    ax.grid(False, axis="y")
    for grp, yy in group_y.items():
        ax.text(-0.012, min(yy) - 0.62, GROUP_TITLE[grp], transform=ax.get_yaxis_transform(), ha="right", va="center",
                fontsize=6.6, fontweight="bold", color=INK)
    ax.set_xlabel("wall time per call (log scale)")
    ax.text(1.015, -0.75, "median  [IQR]", transform=ax.get_yaxis_transform(), va="center", ha="left", fontsize=6.3,
            color=INK2, fontweight="bold")
    ax.set_title(f"(a) Distributions of {d['design']['repeats']} interleaved repeats", loc="left", fontsize=8.5, x=-0.0)
    # ---- (b) breakdown
    bx = fig.add_subplot(gs[1])
    comps = [("lean_verdict_s", "Lean verdict (one process)", NAVY, ""),
             ("z3_s", "Z3 suggestions", LAVENDER, ""),
             ("lean_rechecks_s", "Lean re-checks of Z3 suggestions", ICY, ""),
             ("card_audit_s", "verdict card: axiom-audit freshness (SHA-256 of sources + 107 MB binary)", ORANGE, "////"),
             ("other_python_s", "other Python (documents, views, evidence)", MUTED, "")]
    bsum = {}
    order = ["pipeline:REQUIREMENTS_MET", "pipeline:DOES_NOT_MEET_REQUIREMENTS", "pipeline:NEED_MORE_INFORMATION"]
    labels = {"pipeline:REQUIREMENTS_MET": "MET pair", "pipeline:DOES_NOT_MEET_REQUIREMENTS": "NOT MET pair",
              "pipeline:NEED_MORE_INFORMATION": "NEED INFO pair"}
    for i, key in enumerate(order):
        b = d["pipeline_breakdown"].get(key)
        if not b:
            continue
        left = 0.0
        bsum[key] = {}
        for ck, lab, col, h in comps:
            v = float(np.median([x[ck] for x in b]))
            bsum[key][ck] = v
            bx.barh(i, v, left=left, height=0.62, color=col, edgecolor="white", hatch=h, lw=0.5)
            if v > 0.09:
                if h:   # hatched segment: dark text on a white chip so the value stays legible
                    bx.text(left + v / 2, i, f"{v:.2f}", ha="center", va="center", fontsize=6.0, color=INK,
                            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none"))
                else:
                    bx.text(left + v / 2, i, f"{v:.2f}", ha="center", va="center", fontsize=6.0,
                            color="white" if col in (NAVY, ORANGE, MUTED) else INK)
            left += v
        bsum[key]["sum_of_medians"] = left
        bsum[key]["median_total"] = float(np.median(sec[key]))
        bsum[key]["lean_rechecks_count_median"] = float(np.median([x["lean_rechecks"] for x in b]))
        bx.text(left + 0.03, i, f"{left:.2f} s", va="center", fontsize=6.3, color=INK)
    bx.set_yticks(range(len(order)))
    bx.set_yticklabels([f"verifier.check: {labels[k]}" for k in order], fontsize=6.6)
    bx.invert_yaxis()
    bx.tick_params(axis="y", length=0)
    bx.grid(True, axis="x")
    bx.grid(False, axis="y")
    bx.set_xlabel("median time per component (s; medians stacked)")
    bx.set_title("(b) Where the full check spends its time", loc="left", fontsize=8.5)
    bx.set_xlim(0, max(v["sum_of_medians"] for v in bsum.values()) * 1.12)
    bx.legend(handles=[Patch(facecolor=c, edgecolor="white", hatch=h, label=l) for _, l, c, h in comps],
              loc="upper center", bbox_to_anchor=(0.42, -0.42), ncol=2, fontsize=6.0, handlelength=1.6, columnspacing=1.0)
    fig.subplots_adjust(left=0.36, right=0.80, top=0.95, bottom=0.17)
    return fig, {"distributions": summary, "breakdown_medians": bsum}


# ---------------------------------------------------------------- fig_runtime_family
VERDICT_MARK = {"REQUIREMENTS_MET": "o", "NEED_MORE_INFORMATION": "s", "DOES_NOT_MEET_REQUIREMENTS": "^"}


def plot_runtime_family(d: dict):
    rows = d["rows"]
    floor = med_iqr(d["process_start_s"])
    fams = defaultdict(list)
    for r in rows:
        fams[r["family"]].append(r)
    order = sorted(fams, key=lambda f: np.median([np.median(r["seconds"]) for r in fams[f]]))
    fig, ax = plt.subplots(figsize=(COL2, 3.3))
    ax.axvspan(floor["q1"] * 1000, floor["q3"] * 1000, color=GRID, lw=0, zorder=0)
    ax.axvline(floor["median"] * 1000, color=MUTED, ls="--", lw=0.8, zorder=1)
    summ = {}
    rng = np.random.default_rng(3)
    for i, f in enumerate(order):
        meds = np.array([np.median(r["seconds"]) for r in fams[f]]) * 1000
        q1, md, q3 = np.percentile(meds, [25, 50, 75])
        ax.add_patch(Rectangle((q1, i - 0.28), q3 - q1, 0.56, fc="white", ec=INK, lw=0.7, zorder=3))
        ax.plot([md, md], [i - 0.28, i + 0.28], color=INK, lw=1.3, zorder=4)
        for r, m in zip(fams[f], meds):
            v = r["verdict"]
            ax.scatter([m], [i + rng.uniform(-0.2, 0.2)], s=9, marker=VERDICT_MARK[v], color=VERDICT_COLOR[v],
                       edgecolor="white", lw=0.3, alpha=0.9, zorder=5)
        cfgs = sorted({r["configuration"] for r in fams[f]})
        summ[f] = {"short": FAMILY_SHORT.get(f, f), "pairs": len(fams[f]), "configurations": cfgs,
                   "pair_medians_ms": med_iqr(meds), "verdicts": dict(Counter(r["verdict"] for r in fams[f]))}
        ax.text(1.01, i, f"{len(fams[f])} pairs ({len(cfgs)} configs)  median {md:.0f} ms", transform=ax.get_yaxis_transform(),
                va="center", fontsize=6.3, color=INK)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([FAMILY_SHORT.get(f, f) for f in order], fontsize=6.8)
    ax.tick_params(axis="y", length=0)
    ax.grid(True, axis="x")
    ax.grid(False, axis="y")
    ax.set_xlabel("Lean single-check wall time, median of 3 repeats per pair (ms)")
    allm = np.array([np.median(r["seconds"]) for r in rows]) * 1000
    ax.set_xlim(min(allm.min(), floor["q1"] * 1000) * 0.9, allm.max() * 1.06)
    ax.set_ylim(len(order) - 0.5, -0.9)
    ax.text(floor["median"] * 1000, -0.72, f" process start {floor['median'] * 1000:.0f} ms", fontsize=6.2, color=INK2,
            va="center", ha="left")
    handles = [Line2D([], [], marker=VERDICT_MARK[v], color=VERDICT_COLOR[v], mec="white", mew=0.3, ls="none", ms=4.5,
                      label=f"{VERDICT_LABEL[v]} (Lean)") for v in VERDICT_ORDER]
    handles += [Patch(facecolor="white", edgecolor=INK, lw=0.7, label="IQR and median of the pairs"),
                Patch(facecolor=GRID, edgecolor=MUTED, ls="--", lw=0.6, label="process start: median, IQR")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=3, fontsize=6.2, handletextpad=0.4,
              columnspacing=1.0)
    fig.subplots_adjust(left=0.29, right=0.78, top=0.97, bottom=0.27)
    sec = np.array([np.median(r["seconds"]) for r in rows])
    rho = stats.spearmanr([r["input_bytes"] for r in rows], sec)
    kw = stats.kruskal(*[[np.median(r["seconds"]) for r in fams[f]] for f in order])
    by_v = {v: med_iqr([np.median(r["seconds"]) for r in rows if r["verdict"] == v]) for v in VERDICT_ORDER}
    return fig, {"families": summ, "order": order, "process_start": floor, "spearman_time_vs_input_bytes":
                 {"rho": float(rho.statistic), "p": float(rho.pvalue)}, "kruskal_wallis_family": {"H": float(kw.statistic), "p": float(kw.pvalue)},
                 "by_verdict": by_v, "all_pairs": med_iqr(sec),
                 "verdict_agreement_with_e1_grid": sum(r["verdict"] == r["e1_grid_verdict"] for r in rows),
                 "verdicts_stable_across_repeats": sum(r["verdict_stable"] for r in rows)}


# ================================================================ main
BENCHES = ["lean_scaling", "z3_candidates", "z3_schedule", "runtime_dist", "runtime_family"]


def env_text(env):
    return (f"{env['cpu']} ({env['physical_cores']} cores / {env['logical_cpus']} threads, {env['ram_gib']} GiB), "
            f"{env['os']}, Python {env['python']}, {env['lean']}, Z3 {env['z3']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recompute", nargs="?", const="all", default=None)
    ap.add_argument("--plot-only", action="store_true")
    ap.add_argument("--propose-worker", nargs=2, default=None)
    ap.add_argument("--cooldown", default=None)
    a = ap.parse_args()
    if a.propose_worker:
        propose_worker(int(a.propose_worker[0]), a.propose_worker[1])
        return
    sys.stdout.reconfigure(encoding="utf-8")
    apply()
    redo = set(BENCHES) if a.recompute == "all" else set((a.recompute or "").split(",")) - {""}
    if not a.plot_only:
        cat = Catalog()
        env = environment()
        dump("bench_env", env)
        fns = {"lean_scaling": bench_lean_scaling, "z3_candidates": bench_z3_candidates, "z3_schedule": bench_z3_schedule,
               "runtime_dist": bench_runtime_dist, "runtime_family": bench_runtime_family}
        for b in BENCHES:
            if b in redo or not (DATA_DIR / f"bench_{b}.json").exists():
                print(f"[{time.strftime('%H:%M:%S')}] measuring {b}", flush=True)
                t0 = time.perf_counter()
                with LoadMonitor() as mon:
                    res = fns[b](cat, log=lambda s: print(f"[{time.strftime('%H:%M:%S')}] {s}", flush=True))
                res["system_cpu_percent_during"] = mon.summary()
                res["env"] = env
                res["benchmark_wall_s"] = time.perf_counter() - t0
                dump(f"bench_{b}", res)
                print(f"  wrote bench_{b}.json ({res['benchmark_wall_s']:.0f} s)", flush=True)
    make_figures()


def load_note(d) -> str:
    m = (d.get("system_cpu_percent_during") or {}).get("median")
    return (f" The machine was not idle: median whole-system CPU utilisation during this benchmark was {m:.0f}% "
            f"(other desktop applications, antivirus scanning and other sessions' jobs).") if m is not None else ""


def stat_at(series, n):
    return series["stats"][series["n"].index(n)]


def make_figures():
    have = {b: (DATA_DIR / f"bench_{b}.json").exists() for b in BENCHES}
    env = load("bench_env")
    et = env_text(env)
    if have["lean_scaling"]:
        d = load("bench_lean_scaling")
        fig, s = plot_lean_scaling(d, env)
        dump("fig_lean_scaling", {"source": "paper/data/bench_lean_scaling.json", "env": env, **s})
        fa, fb = s["fits"]["requirements:single"], s["fits"]["requirements:batch_per_pair"]
        fc, fd = s["fits"]["coupled:single"], s["fits"]["coupled:batch_per_pair"]
        ser = {(x["kind"], x["mode"]): x for x in s["series"]}
        r1, r2k = stat_at(ser[("requirements", "single")], NS[0]), stat_at(ser[("requirements", "single")], NS[-1])
        b1, b2k = stat_at(ser[("requirements", "batch_per_pair")], NS[0]), stat_at(ser[("requirements", "batch_per_pair")], NS[-1])
        c1k = stat_at(ser[("coupled", "single")], KS[-1])
        save(fig, "fig_lean_scaling", meta=dict(
            title="Lean checker runtime vs document size",
            question="How does the compiled Lean checker's wall time grow with the number of mandatory requirements and "
                     "coupled constraints, and what does batching buy?",
            model="Wall-clock timing (time.perf_counter) of lean_runner.check (one Lean process per check), of the Lean "
                  "process alone on a pre-written input, and of lean_runner.check_batch over 100 identical pairs (per pair); "
                  "median and IQR of 7 interleaved repeats after warm-up; OLS fit of log10(time) on log10(size) over the "
                  "upper decade, 95% CI from the t distribution.",
            data=f"paper/data/bench_lean_scaling.json (raw timings) and paper/data/fig_lean_scaling.json (summaries), written "
                 f"by paper/scripts/fig_benchmarks.py. (a) SYNTHETIC documents: N = {NS[0]}..{NS[-1]} mandatory requirements "
                 f"over N matching documented capabilities (5 constraint shapes, all pass; Lean verdict REQUIREMENTS_MET for "
                 f"every N). (b) the real Demo B documents (quantum_mxc_wiring_heat_budget on bluefors_ld400_hdw) with the "
                 f"real mxc_wiring_heat_budget relation repeated k = {KS[0]}..{KS[-1]} times (Lean verdict "
                 f"DOES_NOT_MEET_REQUIREMENTS for every k: each copy fails as in Demo B); batches only up to k = {K_BATCH_MAX}. "
                 f"Machine: {et}.",
            claim="MEASURED",
            caption=(f"Wall time of the compiled Lean checker per experiment-configuration check versus (a) the number of "
                     f"mandatory requirements in synthetic documents and (b) the number of coupled constraints (the real "
                     f"Demo B heat-budget relation repeated). Points are the {SCALING_REPEATS} repeats, markers the median, "
                     f"bars the IQR; the grey band is the Lean process start (cryolean version, median "
                     f"{fmt_time(s['process_start']['median'])}). One process per check costs {fmt_time(r1['median'])} at "
                     f"N = {NS[0]} and {fmt_time(r2k['median'])} at N = {NS[-1]} (upper-decade log-log slope {ci_text(fa)}), "
                     f"because process start dominates; inside a 100-pair batch the per-pair cost rises from "
                     f"{fmt_time(b1['median'])} to {fmt_time(b2k['median'])} (slope {ci_text(fb)}), so the advantage of "
                     f"batching shrinks from {r1['median'] / b1['median']:.0f}x at N = {NS[0]} to "
                     f"{r2k['median'] / b2k['median']:.2f}x at N = {NS[-1]}. Coupled constraints cost more per item ({fmt_time(c1k['median'])} for k = "
                     f"{KS[-1]}; slopes {ci_text(fc)} single, {ci_text(fd)} batch). Dashed lines are power-law fits over the "
                     f"upper decade. All times are measured; verdicts come from the Lean checker." + load_note(d)),
            section="supplement"))
    if have["z3_candidates"] and have["z3_schedule"]:
        dc, ds = load("bench_z3_candidates"), load("bench_z3_schedule")
        fig, s = plot_z3_scaling(dc, ds)
        dump("fig_z3_scaling", {"source": ["paper/data/bench_z3_candidates.json", "paper/data/bench_z3_schedule.json"],
                                "env": env, **s})
        fr = s["candidates"]["series"]["rank_s"]["fit"]
        gs_ = s["schedule"]["propose_sat"]["growth_fit_n_ge_6"]
        gu_ = s["schedule"]["propose_unsat"]["growth_fit_n_ge_6"]
        cs = s["candidates"]["series"]
        sch = s["schedule"]
        n9s, n9u = sch["propose_sat"]["stats"][-1], sch["propose_unsat"]["stats"][-1]
        f16 = sch["feasibility_sat"]["stats"][-1]
        ln = [x["median"] for x in sch["lean_check_schedule"]["stats"]]
        save(fig, "fig_z3_scaling", meta=dict(
            title="Z3 proposer scalability",
            question="How does the untrusted Z3 side (equipment ranking, conflict explanation, campaign scheduling) scale "
                     "with the number of candidate configurations and of experiments, compared with Lean checking?",
            model="Wall-clock timing (time.perf_counter); (a) mean over the 11 catalogued experiments of the time per call, "
                  "median and IQR over 5 interleaved repeats, OLS slope of log10 time on log10 M; (b) median and IQR over 5 "
                  "repeats per n, growth factor per added experiment from an OLS fit of log10 time on n for n >= 6.",
            data="paper/data/bench_z3_candidates.json, paper/data/bench_z3_schedule.json, paper/data/fig_z3_scaling.json, written "
                 "by paper/scripts/fig_benchmarks.py. (a) the 26 real configurations replicated x1, x2, x4, x8, x16 with "
                 "perturbed ids (<id>~v<j>; documents otherwise identical) for every experiment; smt.rank_alternatives, "
                 "smt.all_conflicts on every candidate, the find_compatible_equipment search path (rank + Lean "
                 "check_candidates on <= 10 shown) and Lean check_batch of every candidate. (b) schedule.propose on the "
                 "documented 5 h cooldown of lakeshore_crx_vf with SYNTHETIC durations (1-8 h, seeded) and run lengths "
                 "with 25% slack (satisfiable) or 30 min short (unsatisfiable); its feasibility query alone; Lean "
                 f"check-schedule of the found schedule on synthetic copies of an accepted real profile. Machine: {et}.",
            claim="MEASURED",
            caption=(f"Scalability of the Z3 proposer (markers: median of 5 interleaved repeats; bars: IQR). (a) Ranking "
                     f"all candidate configurations is linear in their number (log-log slope {ci_text(fr)}; "
                     f"{fmt_time(cs['rank_s']['stats'][0]['median'])} for the 26 real configurations, "
                     f"{fmt_time(cs['rank_s']['stats'][-1]['median'])} for 416), as is explaining every candidate's "
                     f"conflicts (slope {ci_text(cs['conflicts_all_s']['fit'])}); Lean-checking every candidate in one batch "
                     f"grows more slowly (slope {ci_text(cs['lean_batch_s']['fit'])}) because one process start is amortised. "
                     f"At the catalogue's current size the search path is dominated by the one-process Lean checks of the "
                     f"ten shown candidates. (b) Finding a feasible campaign schedule takes "
                     f"{fmt_time(f16['median'])} even for 16 experiments, but schedule.propose, which also proves the "
                     f"optimal makespan (satisfiable) or infeasibility (unsatisfiable), grows exponentially (x"
                     f"{gs_['factor_per_step']:.1f} and x{gu_['factor_per_step']:.1f} per added experiment for n >= 6; "
                     f"{fmt_time(n9s['median'])} and {fmt_time(n9u['median'])} at n = 9; not finished within 300 s at n = 10), "
                     f"while Lean checks a schedule in {fmt_time(min(ln))}-{fmt_time(max(ln))}. Durations are synthetic; "
                     f"all times are measured." + load_note(dc).replace("this benchmark", "panel (a)")),
            section="supplement"))
    if have["runtime_dist"]:
        d = load("bench_runtime_dist")
        fig, s = plot_runtime_dist(d)
        dump("fig_runtime_dist", {"source": "paper/data/bench_runtime_dist.json", "env": env, **s, "info": d.get("info"),
                                  "verdicts": d.get("verdicts")})
        ss = s["distributions"]
        save(fig, "fig_runtime_dist", meta=dict(
            title="Runtime distributions",
            question="How long does each stage of a CryoLean check take, how variable is it, and where does a full check "
                     "spend its time?",
            model="Wall-clock timing (time.perf_counter) of repeated calls interleaved in random order; violins are Gaussian "
                  "KDEs of log10(time); boxes are IQR and median. The breakdown uses timing wrappers around the calls "
                  "verifier.check makes (lean_runner.check, lean_runner.axiom_audit, smt.*), behaviour unchanged.",
            data=f"paper/data/bench_runtime_dist.json and paper/data/fig_runtime_dist.json, written by paper/scripts/"
                 f"fig_benchmarks.py; {d['design']['repeats']} repeats per row after 2 warm-up rounds. Pairs: MET = "
                 f"{'/'.join(REP_PAIRS['REQUIREMENTS_MET'])}, NOT MET = {'/'.join(REP_PAIRS['DOES_NOT_MEET_REQUIREMENTS'])} "
                 f"(Demo A), NEED INFO = {'/'.join(REP_PAIRS['NEED_MORE_INFORMATION'])}; batch = all 286 pairs of the "
                 f"11 x 26 grid in one check_batch. Verdicts re-computed by Lean in every repeat. Machine: {et}.",
            claim="MEASURED",
            caption=(f"Distributions of {d['design']['repeats']} interleaved repeats of each stage. A single Lean check "
                     f"costs about one process start ({fmt_time(ss['lean_single:REQUIREMENTS_MET']['median'])} for the MET "
                     f"pair), batching the 286-pair grid brings it to {fmt_time(ss['lean_batch_grid']['median'])} per pair, "
                     f"and a Z3 conflict explanation takes {fmt_time(ss['z3_conflicts:DOES_NOT_MEET_REQUIREMENTS']['median'])}. "
                     f"A full check with suggestions takes {fmt_time(ss['pipeline:REQUIREMENTS_MET']['median'])} to "
                     f"{fmt_time(ss['pipeline:DOES_NOT_MEET_REQUIREMENTS']['median'])}; panel (b) attributes it to the Lean "
                     f"verdict, Z3 suggestions, Lean re-checks of the five suggested alternatives (one process each), and "
                     f"the verdict card's axiom-audit freshness test, which re-hashes the 107 MB checker binary on every "
                     f"check. All values are measured; every repeat's verdict came from Lean." + load_note(d)),
            section="main"))
    if have["runtime_family"]:
        d = load("bench_runtime_family")
        fig, s = plot_runtime_family(d)
        fm = [v["pair_medians_ms"]["median"] for v in s["families"].values()]
        dump("fig_runtime_family", {"source": "paper/data/bench_runtime_family.json", "env": env, **s})
        save(fig, "fig_runtime_family", meta=dict(
            title="Lean runtime per configuration family",
            question="Does the Lean checker's runtime depend on the kind of cryostat (configuration family) or on the "
                     "verdict over the real 11 x 26 grid?",
            model="Wall-clock timing (time.perf_counter) of lean_runner.check, one process per check; 3 repeats per pair in "
                  "shuffled order; per-pair median; Kruskal-Wallis test across families; Spearman correlation with input size.",
            data=f"paper/data/bench_runtime_family.json and paper/data/fig_runtime_family.json, written by paper/scripts/"
                 f"fig_benchmarks.py: all {len(d['rows'])} experiment x configuration pairs of the real catalog (11 experiments x "
                 f"26 configurations, documents from verifier.build_documents), {d['design']['repeats']} repeats each; "
                 f"verdict markers are the Lean verdicts of these runs; process start sampled after every 10th check. "
                 f"Families from the sourced equipment records (data/cryostats/*.json). Machine: {et}.",
            claim="MEASURED+COMPUTED",
            caption=(f"Lean single-check wall time for the {len(d['rows'])} real experiment-configuration pairs, grouped by "
                     f"configuration family (boxes: IQR and median of the per-pair medians of "
                     f"{d['design']['repeats']} repeats; markers: the Lean verdict of each pair; grey band: Lean process "
                     f"start, median {fmt_time(s['process_start']['median'])}). Family medians span {min(fm):.0f}-{max(fm):.0f} ms "
                     f"and do not differ significantly (Kruskal-Wallis H = {s['kruskal_wallis_family']['H']:.1f}, "
                     f"p = {s['kruskal_wallis_family']['p']:.2f}); time is uncorrelated with document size (Spearman "
                     f"rho = {s['spearman_time_vs_input_bytes']['rho']:.2f}). For real documents the cost of a check is "
                     f"that of launching the checker, not the cryostat or the verdict. Timings are measured; verdicts are "
                     f"computed by the Lean checker." + load_note(d)),
            section="supplement"))


if __name__ == "__main__":
    main()
