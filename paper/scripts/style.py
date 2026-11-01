"""Shared visual identity, paths and figure metadata for the CryoLean paper.

Every figure script does:

    from style import *
    apply()
    fig, ax = plt.subplots(figsize=(COL1, 2.6))
    ...
    save(fig, "fig_heat_budget", meta=dict(title=..., question=..., model=..., data=..., claim="COMPUTED", caption=...))

`save` writes paper/figures/<name>.png (300 dpi), .svg and .pdf, and paper/figures/meta/<name>.json, which
paper/scripts/build_figure_index.py turns into paper/FIGURE_INDEX.md.

Claim classes (paper/CLAIM_AUDIT.md uses the same words):
    PROVEN       machine-checked by the Lean 4 kernel (a theorem)
    COMPUTED     produced by running CryoLean (Lean checker / Z3) on this machine
    MEASURED     a timing or resource measurement on this machine
    MODELED      derived from a documented physical model and stated assumptions (not measured)
    SOURCED      taken from manufacturer documentation or the scientific literature
    ILLUSTRATIVE a schematic; not data
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, ListedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper"
FIG_DIR = PAPER / "figures"
META_DIR = FIG_DIR / "meta"
INT_DIR = PAPER / "interactive"
DATA_DIR = PAPER / "data"
sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------- palette (validated: scripts/validate_palette.js, light)
# categorical, fixed order, never cycled; slot 3 (icy blue) is < 3:1 on white -> always direct-label it
NAVY = "#2a4d8f"
LAVENDER = "#7c6ee6"
ICY = "#2fa9d9"
ORANGE = "#d9663a"
CATEGORICAL = [NAVY, LAVENDER, ICY, ORANGE]

INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#ffffff"
DEEP_NAVY = "#0e1a33"          # brand banner background, used only for the schematic

# verdicts use the reserved status colours + hatch + text label (never colour alone)
VERDICT_COLOR = {"REQUIREMENTS_MET": "#0ca30c", "DOES_NOT_MEET_REQUIREMENTS": "#d03b3b",
                 "NEED_MORE_INFORMATION": "#fab219", "BUILD_ERROR": "#898781"}
VERDICT_HATCH = {"REQUIREMENTS_MET": "", "DOES_NOT_MEET_REQUIREMENTS": "////", "NEED_MORE_INFORMATION": "....", "BUILD_ERROR": "xx"}
VERDICT_SHORT = {"REQUIREMENTS_MET": "MET", "DOES_NOT_MEET_REQUIREMENTS": "NOT MET", "NEED_MORE_INFORMATION": "NEED INFO",
                 "BUILD_ERROR": "n/a"}
VERDICT_LABEL = {"REQUIREMENTS_MET": "Requirements met", "DOES_NOT_MEET_REQUIREMENTS": "Does not meet requirements",
                 "NEED_MORE_INFORMATION": "Need more information", "BUILD_ERROR": "Not evaluable"}
VERDICT_ORDER = ["REQUIREMENTS_MET", "NEED_MORE_INFORMATION", "DOES_NOT_MEET_REQUIREMENTS"]
VERDICT_CMAP = ListedColormap([VERDICT_COLOR[v] for v in VERDICT_ORDER])
VERDICT_INDEX = {v: i for i, v in enumerate(VERDICT_ORDER)}

# sequential: one hue (blue), light -> dark (reference ramp steps 100..700)
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#1c5cab", "#104281", "#0d366b"]
SEQ_CMAP = LinearSegmentedColormap.from_list("cryo_seq", SEQ_BLUE)
# brand ramp for 3D surfaces: icy blue -> lavender -> navy (monotone in lightness)
BRAND_CMAP = LinearSegmentedColormap.from_list("cryo_brand", ["#d8f1fb", "#8fd0ee", "#9a8ef0", "#5a4fc4", "#1f3a6e"])
# diverging: blue <- neutral grey -> orange (margin: negative = violated, positive = slack)
DIV_CMAP = LinearSegmentedColormap.from_list("cryo_div", ["#d9663a", "#f0c2ad", "#f0efec", "#a9c6ee", "#2a4d8f"])

COL1 = 3.4     # single column width, inches
COL2 = 7.0     # full width


def apply():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7, "legend.frameon": False,
        "axes.edgecolor": AXIS, "axes.linewidth": 0.6, "axes.labelcolor": INK, "axes.titleweight": "bold",
        "xtick.color": INK2, "ytick.color": INK2, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True,
        "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.6, "lines.markersize": 4,
        "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "pdf.fonttype": 42, "svg.fonttype": "none",
        "mathtext.fontset": "dejavusans",
    })


def verdict_legend(ax, verdicts=VERDICT_ORDER, **kw):
    handles = [Patch(facecolor=VERDICT_COLOR[v], hatch=VERDICT_HATCH[v], edgecolor="white", label=VERDICT_LABEL[v])
               for v in verdicts]
    return ax.legend(handles=handles, **kw)


REQUIRED_META = ("title", "question", "model", "data", "claim", "caption")
CLAIMS = {"PROVEN", "COMPUTED", "MEASURED", "MODELED", "SOURCED", "ILLUSTRATIVE"}


def save(fig, name: str, meta: dict, interactive: str | None = None):
    """Write PNG/SVG/PDF + metadata. meta needs title, question, model, data, claim (one or more of CLAIMS,
    joined by '+'), caption; optional: section ('main' or 'supplement'), notes."""
    missing = [k for k in REQUIRED_META if not meta.get(k)]
    if missing:
        raise ValueError(f"{name}: metadata missing {missing}")
    bad = [c for c in meta["claim"].split("+") if c.strip() not in CLAIMS]
    if bad:
        raise ValueError(f"{name}: unknown claim class {bad}")
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg", "pdf"):
        fig.savefig(FIG_DIR / f"{name}.{ext}")
    plt.close(fig)
    caller = Path(inspect.stack()[1].filename).resolve()
    script = caller.relative_to(ROOT).as_posix() if caller.is_relative_to(ROOT) else caller.name
    rec = {"name": name, **meta, "script": script, "command": f"python {script}",
           "files": [f"paper/figures/{name}.{e}" for e in ("png", "svg", "pdf")],
           "interactive": f"paper/interactive/{interactive}" if interactive else None}
    (META_DIR / f"{name}.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"saved {name}")


def save_html(fig, name: str):
    """Interactive Plotly figure (rotate/zoom). Plotly.js from the CDN keeps the repo small."""
    INT_DIR.mkdir(parents=True, exist_ok=True)
    fig.update_layout(font=dict(family="DejaVu Sans, Arial", size=12), paper_bgcolor="white")
    fig.write_html(INT_DIR / f"{name}.html", include_plotlyjs="cdn", full_html=True)
    print(f"saved interactive {name}.html")
    return f"{name}.html"


def load(name: str):
    return json.loads((DATA_DIR / f"{name}.json").read_text(encoding="utf-8"))


def dump(name: str, obj):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


__all__ = [n for n in dir() if not n.startswith("_")] + ["plt"]
