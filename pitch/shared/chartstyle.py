"""Matplotlib style for CryoLean pitch charts (dark, matches shared/deck.css).

    import sys; sys.path.insert(0, r"C:/Users/User_1/Desktop/CryoLean/CryoLean/pitch/shared")
    import chartstyle as cs
    fig, ax = cs.figure(640, 420)          # size in slide pixels (the <img> slot it will fill)
    ...
    cs.save(fig, "charts/verdicts")         # writes verdicts.svg (vector, text stays text) + verdicts.png (2x)

Sizing: a figure made with figure(w, h) is exactly w x h CSS px on the slide when shown at that size,
so a 11 pt label is about 15 px on the slide, like the LeanKeel charts.
"""
from __future__ import annotations

import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

C = {
    "bg": "#060d1a", "panel": "#081226", "line": "#1c2b48", "line2": "#2a3a5a",
    "cream": "#f2ede4", "text": "#c6d0dd", "muted": "#8794a8", "dim": "#5b6a82",
    "orange": "#f5a524", "amber": "#f5a524", "purple": "#b8a4ff", "teal": "#2dd4bf",
    "pink": "#f0609e", "blue": "#4c9be8", "green": "#22c08a", "silver": "#c9d2dc",
}
# verdict colours, same everywhere
VERDICT = {"met": C["teal"], "info": C["amber"], "not": C["pink"]}
VERDICT_LABEL = {"met": "Requirements met", "info": "Need more information", "not": "Does not meet requirements"}
SERIES = [C["teal"], C["orange"], C["purple"], C["pink"], C["blue"], C["green"], C["silver"]]

SANS = ["Arial", "Liberation Sans", "DejaVu Sans"]
MONO = ["Consolas", "Liberation Mono", "DejaVu Sans Mono"]


def apply() -> None:
    plt.rcParams.update({
        "figure.facecolor": "none", "axes.facecolor": "none", "savefig.facecolor": "none",
        "savefig.transparent": True,
        "font.family": "sans-serif", "font.sans-serif": SANS, "font.monospace": MONO,
        "font.size": 11, "text.color": C["text"],
        "axes.edgecolor": C["line2"], "axes.labelcolor": C["text"], "axes.titlecolor": C["cream"],
        "axes.titlesize": 13, "axes.titleweight": "bold", "axes.labelsize": 11,
        "axes.grid": True, "axes.axisbelow": True,
        "grid.color": C["line"], "grid.linewidth": 0.8, "grid.alpha": 1.0,
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.color": C["muted"], "ytick.color": C["muted"], "xtick.labelsize": 10, "ytick.labelsize": 10,
        "xtick.major.size": 0, "ytick.major.size": 0,
        "legend.frameon": False, "legend.fontsize": 10, "legend.labelcolor": C["text"],
        "axes.prop_cycle": plt.cycler(color=SERIES),
        "svg.fonttype": "none",       # keep text as text in SVG (rendered by the browser in Arial/Consolas)
        "pdf.fonttype": 42,
        "lines.linewidth": 2.0,
        "lines.solid_capstyle": "round",
    })


def figure(w_px: float, h_px: float, **kw):
    """Figure that is w_px x h_px CSS pixels on the slide."""
    apply()
    fig, ax = plt.subplots(figsize=(w_px / 96, h_px / 96), dpi=96, **kw)
    return fig, ax


def figure3d(w_px: float, h_px: float):
    apply()
    fig = plt.figure(figsize=(w_px / 96, h_px / 96), dpi=96)
    ax = fig.add_subplot(111, projection="3d")
    style3d(ax)
    return fig, ax


def style3d(ax) -> None:
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.set_pane_color((0, 0, 0, 0))
        axis._axinfo["grid"]["color"] = C["line"]
        axis._axinfo["grid"]["linewidth"] = 0.7
        axis.line.set_color(C["line2"])
        axis.label.set_color(C["text"])
    ax.tick_params(colors=C["muted"], labelsize=9)


def save(fig, stem: str | pathlib.Path, png_scale: float = 2.0) -> tuple[pathlib.Path, pathlib.Path]:
    stem = pathlib.Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    svg, png = stem.with_suffix(".svg"), stem.with_suffix(".png")
    fig.savefig(svg, transparent=True)
    fig.savefig(png, dpi=96 * png_scale, transparent=True)
    plt.close(fig)
    return svg, png


apply()
