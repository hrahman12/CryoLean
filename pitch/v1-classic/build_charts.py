"""Charts for the CryoLean v1 · Classic deck. Rebuild: .venv python build_charts.py"""
import collections
from fractions import Fraction
import glob
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
REPO = HERE.parent.parent  # repository root: this deck lives in <repo>/pitch/<deck>/
sys.path.insert(0, str(HERE.parent / "shared"))
import chartstyle as cs  # noqa: E402

TO_K = {"mK": 1e-3, "K": 1.0}
TO_T = {"mT": 1e-3, "T": 1.0}

GROUPS = [  # (name, colour, keywords) first match wins
    ("Sub-kelvin (dilution, ADR, He-3)", cs.C["blue"],
     ["dilution", "adiabatic demag", "adr", "he-3", "1 k system", "bolometer"]),
    ("Lab cryostats and magnets", cs.C["green"],
     ["cryostat", "magnet", "property", "probe station", "cryocooler", "cryogenerator", "squid", "hall",
      "vti", "prober", "cold head", "detector", "srf", "dewar", "liquefier", "refrigerator", "nmr",
      "calibration", "fixed-point", "radiometer", "bolometer", "conductor", "neutron", "cooler", "rf_",
      "optical", "superconducting", "sorption", "calorimeter", "hpge", "noble", "jt", "dilatometer"]),
    ("Freezers and test chambers", cs.C["silver"], [""]),
]


def group_of(text):
    t = text.lower().replace("without dilution", "")
    for i, (_, _, kws) in enumerate(GROUPS):
        if any(k in t for k in kws):
            return i
    return len(GROUPS) - 1


def coldest_K(caps):
    for key, fld in (("temperature.base", "q"), ("temperature.range", "lo")):
        c = caps.get(key)
        if c and c["value"].get(fld):
            q = c["value"][fld]
            if q["unit"] in TO_K:
                return float(Fraction(str(q["value"]))) * TO_K[q["unit"]]
    return None


def field_T(caps):
    c = caps.get("magnetic_field.max")
    if c and c["value"].get("kind") == "max" and c.get("install") == "installed":
        q = c["value"]["q"]
        return float(Fraction(str(q["value"]))) * TO_T[q["unit"]]
    return None


def landscape():
    pts, n_cfg, no_temp = [], 0, 0
    for fn in sorted(glob.glob(str(REPO / "data/cryostats/*.json"))):
        f = json.load(open(fn, encoding="utf-8"))
        for c in f["configurations"]:
            n_cfg += 1
            caps = {x["key"]: x for x in c["capabilities"]}
            t = coldest_K(caps)
            if t is None:
                no_temp += 1
                continue
            g = group_of(f"{f.get('family', '')} {f.get('model', '')} {c.get('name', '')}")
            pts.append((t, field_T(caps), g, c.get("name", "")))
    n_field = sum(p[1] is not None for p in pts)
    print(f"configs {n_cfg}; plotted {len(pts)}; no coldest temperature {no_temp}; with field {n_field}")
    print("groups", collections.Counter(GROUPS[p[2]][0] for p in pts))
    tmin = min(p[0] for p in pts); tmax = max(p[0] for p in pts); bmax = max(p[1] for p in pts if p[1])
    print(f"coldest {tmin} K .. {tmax} K; max field {bmax} T")
    for p in sorted(pts, key=lambda p: -(p[1] or 0))[:6]:
        print("  top field", p)

    fig, ax = cs.figure(700, 396)
    import numpy as np
    rng = np.random.default_rng(7)
    strip = -3.0
    for gi, (name, col, _) in enumerate(GROUPS):
        sub = [p for p in pts if p[2] == gi]
        xs = [p[0] for p in sub if p[1] is not None]; ys = [p[1] for p in sub if p[1] is not None]
        ax.scatter(xs, ys, s=46, color=col, alpha=0.9, edgecolors="none", zorder=3,
                   label=f"{name} ({len(sub)})")
        xs2 = [p[0] for p in sub if p[1] is None]
        ys2 = strip + rng.uniform(-1.0, 1.0, len(xs2))
        ax.scatter(xs2, ys2, s=24, color=col, alpha=0.55, edgecolors="none", zorder=2)
    ax.set_xscale("log")
    ax.set_xlim(tmin / 2, tmax * 2)
    ax.set_ylim(strip - 1.4, 25.5)
    ax.axhline(-1.5, color=cs.C["line2"], lw=1)
    ax.set_yticks([strip, 0, 5, 10, 15])
    ax.set_yticklabels(["none", "0", "5", "10", "15"])
    top = max((p for p in pts if p[1]), key=lambda p: p[1])
    ax.annotate(f"{top[1]:g} T", (top[0], top[1]), xytext=(10, 2), textcoords="offset points",
                fontsize=14, fontweight="bold", color=cs.C["cream"], family="monospace", va="center")
    cold = min(pts, key=lambda p: p[0])
    ax.annotate(f"{cold[0]*1000:g} mK", (cold[0], strip + 0.3), xytext=(cold[0], 3.2), ha="center",
                fontsize=14, fontweight="bold", color=cs.C["cream"], family="monospace",
                arrowprops=dict(arrowstyle="-", color=cs.C["muted"], lw=1))
    ax.set_xticks([0.01, 0.1, 1, 10, 100])
    ax.set_xticklabels(["10 mK", "100 mK", "1 K", "10 K", "100 K"])
    ax.tick_params(labelsize=13)
    ax.set_xlabel("coldest temperature (log scale)", fontsize=13)
    ax.set_ylabel("strongest magnetic field (T)", fontsize=13)
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.0), ncol=1, fontsize=13, handletextpad=0.2, borderaxespad=0.3, labelspacing=0.3)
    fig.tight_layout(pad=1.0)
    print(cs.save(fig, HERE / "charts/landscape"))
    return len(pts), no_temp, n_field


if __name__ == "__main__":
    landscape()
