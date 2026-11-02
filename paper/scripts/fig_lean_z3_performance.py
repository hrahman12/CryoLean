"""Figure 3: Lean 4 checker vs Z3 runtime against problem size (pairs), measured on this machine.

    python paper/scripts/fig_lean_z3_performance.py --measure --db FULL.db [--grid-db COPY.db] [--repeats N]
    python paper/scripts/fig_lean_z3_performance.py            # plot from paper/data/fig_lean_z3_performance.json

Lean: lean_runner.check_batch (one process) on the first n pairs of the experiment x configuration grid,
and the full grid via scripts/build_grid.py (process pool). Z3: smt.evaluate per pair and
smt.rank_alternatives over the same pairs."""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import statistics as st
import subprocess
import sys
import time
from collections import Counter

from style import *  # noqa: F401,F403

from cryolean import grid, lean_runner, serialize, smt  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402

NAME = "fig_lean_z3_performance"
LEAN_SIZES = [1, 10, 100, 1000, 5000]
Z3_SIZES = [1, 10, 100, 1000]


def all_pairs(cat, limit):
    cfgs = grid.configuration_documents(cat)
    out = []
    for eid in sorted(cat.experiments):
        exp = serialize.working_experiment(cat, eid, None, None, True)
        out += grid.experiment_pairs(cat, exp, cfgs)
        if len(out) >= limit:
            break
    return out[:limit]


def stats(xs):
    return {"median_s": st.median(xs), "min_s": min(xs), "max_s": max(xs), "runs_s": xs}


def measure(db, grid_db, repeats, grid_repeats):
    cat = Catalog(db)
    pairs = all_pairs(cat, max(LEAN_SIZES))
    lean, z3e, z3r = [], [], []
    for n in LEAN_SIZES:
        ts, verdicts = [], None
        for _ in range(repeats):
            t = time.perf_counter()
            res = lean_runner.check_batch(pairs[:n])
            ts.append(time.perf_counter() - t)
            verdicts = dict(Counter(r["verdict"] for r in res))
        lean.append({"pairs": n, **stats(ts), "verdicts": verdicts})
        print("lean", n, st.median(ts), flush=True)
    for n in Z3_SIZES:
        reps = repeats if n <= 100 else 3
        ts, evs = [], []
        for _ in range(reps):
            t = time.perf_counter()
            evs = [smt.evaluate(c, e) for c, e in pairs[:n]]
            ts.append(time.perf_counter() - t)
        z3e.append({"pairs": n, **stats(ts), "status": dict(Counter(ev.status for ev in evs))})
        ts = []
        for _ in range(reps):
            t = time.perf_counter()
            smt.rank_alternatives(pairs[:n])
            ts.append(time.perf_counter() - t)
        z3r.append({"pairs": n, **stats(ts)})
        print("z3", n, z3e[-1]["median_s"], st.median(ts), flush=True)
    full, out_lines = [], ""
    for _ in range(grid_repeats):
        t = time.perf_counter()
        p = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_grid.py"), "--db", grid_db],
                           capture_output=True, text=True, env=dict(os.environ), cwd=ROOT, encoding="utf-8")
        full.append(time.perf_counter() - t)
        out_lines = p.stdout.strip()
        print(out_lines, flush=True)
        if p.returncode:
            raise SystemExit(p.stderr)
    s = grid.summary(Catalog(grid_db))
    dump(NAME, {
        "machine": {"cpu_count": os.cpu_count(), "grid_workers": grid.workers(), "platform": platform.platform(),
                    "processor": platform.processor(), "python": platform.python_version()},
        "lean_binary": str(lean_runner.lean_binary()), "lean_version": lean_runner.version(),
        "lean_source_hash": lean_runner.source_hash(), "catalog_db": str(db), "repeats": repeats,
        "pair_order": "experiments sorted by id, each against all configurations sorted by id; first n pairs",
        "lean_check_batch": lean, "z3_evaluate": z3e, "z3_rank_alternatives": z3r,
        "lean_full_grid": {"pairs": len(cat.experiments) * len(cat.configurations), "summary_overall": s.get("overall"),
                           **stats(full), "command": "python scripts/build_grid.py --db <copy of full_v4.db>",
                           "stdout": out_lines}})


def plot():
    d = load(NAME)
    apply()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(COL2, 2.7), sharex=True)
    series = [("Lean check_batch (1 process)", d["lean_check_batch"], NAVY, "o"),
              ("Z3 evaluate (per pair, serial)", d["z3_evaluate"], ORANGE, "s"),
              ("Z3 rank_alternatives", d["z3_rank_alternatives"], LAVENDER, "^")]
    g = d["lean_full_grid"]
    for lab, rows, c, m in series:
        x = [r["pairs"] for r in rows]
        med = [r["median_s"] for r in rows]
        err = [[r["median_s"] - r["min_s"] for r in rows], [r["max_s"] - r["median_s"] for r in rows]]
        a1.errorbar(x, med, yerr=err, color=c, marker=m, capsize=2, label=lab)
        a2.plot(x, [1e3 * r["median_s"] / r["pairs"] for r in rows], color=c, marker=m, label=lab)
    lab = f"Lean full grid, {d['machine']['grid_workers']} workers"
    a1.errorbar([g["pairs"]], [g["median_s"]], yerr=[[g["median_s"] - g["min_s"]], [g["max_s"] - g["median_s"]]],
                color=ICY, marker="D", ls="none", capsize=2, label=lab)
    a2.plot([g["pairs"]], [1e3 * g["median_s"] / g["pairs"]], color=ICY, marker="D", ls="none", label=lab)
    a1.annotate(f"{g['pairs']:,} pairs\n{g['median_s']:.0f} s", (g["pairs"], g["median_s"]), xytext=(0, -10),
                textcoords="offset points", ha="right", va="top", fontsize=6.5, color=INK2)
    for a in (a1, a2):
        a.set_xscale("log")
        a.set_yscale("log")
        a.set_xlabel("problem size (experiment x configuration pairs)")
    a1.set_ylabel("wall time (s)")
    a1.set_title("Total runtime")
    a2.set_ylabel("time per pair (ms)")
    a2.set_title("Per-pair latency")
    a1.legend(loc="upper left", fontsize=6)
    lt = d["lean_check_batch"][-1]
    zt = d["z3_evaluate"][-1]
    cap = (f"Measured runtime of the Lean 4 checker (decides every verdict) and Z3 (explains and ranks) against "
           f"problem size on a {d['machine']['cpu_count']}-CPU machine. Medians of {d['repeats']} runs (3 runs for "
           f"Z3 at 1000 pairs); bars span min to max. Lean check_batch in one process: {lt['pairs']} pairs in "
           f"{lt['median_s']:.2f} s ({1e3 * lt['median_s'] / lt['pairs']:.2f} ms/pair). Z3 evaluate, serial: "
           f"{zt['pairs']} pairs in {zt['median_s']:.1f} s ({1e3 * zt['median_s'] / zt['pairs']:.1f} ms/pair). "
           f"Full grid ({g['pairs']:,} pairs, scripts/build_grid.py, {d['machine']['grid_workers']} worker processes, "
           f"including serialisation and database writes): median {g['median_s']:.0f} s over {len(g['runs_s'])} runs. "
           f"Z3 was not run on the full grid and no extrapolation is drawn.")
    save(fig, NAME, dict(
        title="Lean 4 and Z3 runtime vs problem size", section="main",
        question="How do verification (Lean) and solver (Z3) runtimes scale with the number of experiment x configuration pairs?",
        model="Wall-clock timing (time.perf_counter) of lean_runner.check_batch, smt.evaluate, smt.rank_alternatives "
              "and scripts/build_grid.py on the same pairs.",
        data=f"paper/data/{NAME}.json (catalog full_v4.db, 204 experiments x 220 configurations)",
        claim="MEASURED", caption=cap,
        notes=f"Machine: {d['machine']}. Lean binary {d['lean_binary']}, source hash {d['lean_source_hash']}."))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--db")
    ap.add_argument("--grid-db")
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--grid-repeats", type=int, default=3)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if a.measure:
        if not a.grid_db:
            a.grid_db = a.db + ".perfcopy.db"
            shutil.copyfile(a.db, a.grid_db)
        measure(a.db, a.grid_db, a.repeats, a.grid_repeats)
    plot()
