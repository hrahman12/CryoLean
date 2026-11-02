"""Charts and images for the v5 'Vision and ask' deck.

    pitch/.venv/Scripts/python.exe pitch/v5-vision/build_charts.py

1. charts/matrix.svg : the 180 featured pairings (20 industries x 9 squares, best-match machines)
   from CryoLean-main/site/matrix_data.json. Counts are computed here, not typed in.
2. charts/demo_site.png : crop of the website's DEMOS tab (pitch/assets/site/demo-long@2x.png).
"""
import collections
import json
import pathlib
import sys

from matplotlib.patches import FancyBboxPatch
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
PITCH = HERE.parent
REPO = HERE.parent.parent  # repository root: this deck lives in <repo>/pitch/<deck>/
sys.path.insert(0, str(PITCH / "shared"))
import chartstyle as cs  # noqa: E402

OUT = HERE / "charts"
OUT.mkdir(exist_ok=True)
PT = 72 / 96  # px -> pt

# ---------- 1. the 180 matrix ----------
data = json.loads((REPO / "site" / "matrix_data.json").read_text(encoding="utf-8"))
rows = []
for ind in data["industries"]:
    cells = [c for row in ind["best"]["cells"] for c in row]
    rows.append((ind["name"].split(" and ")[0], cells))
count = collections.Counter(c for _, cells in rows for c in cells)
assert len(rows) == 20 and sum(count.values()) == 180, count
print("matrix counts:", dict(count))  # expected R 134 / N 26 / D 20
COL = {"R": cs.VERDICT["met"], "N": cs.VERDICT["info"], "D": cs.VERDICT["not"]}

W, H = 600, 470
fig, ax = cs.figure(W, H)
ax.set_position([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(H, 0)
ax.axis("off")

# legend with computed counts (top)
legend = [("R", "met"), ("N", "need info"), ("D", "do not meet")]
lx = 34
for key, word in legend:
    ax.add_patch(FancyBboxPatch((lx, 22), 16, 16, boxstyle="round,pad=0,rounding_size=3",
                                fc=COL[key], ec="none"))
    t = ax.text(lx + 26, 31, f"{count[key]}", va="center", ha="left", family="monospace",
                fontweight="bold", fontsize=18 * PT, color=cs.C["cream"])
    ax.text(lx + 26 + 40, 31, word, va="center", ha="left", fontsize=15 * PT, color=cs.C["text"])
    lx += 26 + 40 + {"met": 62, "need info": 100, "do not meet": 0}[word] + 18

SIZE, XSTEP, GROUP = 18, 23, 12
X0, Y0, YSTEP = 196, 74, 19.8
for g in range(3):
    gx = X0 + g * (3 * XSTEP + GROUP)
    ax.text(gx + (2 * XSTEP + SIZE) / 2, Y0 - 12, f"exp {g + 1}", ha="center", va="bottom",
            fontsize=13 * PT, color=cs.C["muted"], family="monospace")
for r, (name, cells) in enumerate(rows):
    y = Y0 + r * YSTEP
    ax.text(X0 - 14, y + SIZE / 2, name, ha="right", va="center", fontsize=14 * PT, color=cs.C["text"])
    for i, c in enumerate(cells):
        g, j = divmod(i, 3)
        x = X0 + g * (3 * XSTEP + GROUP) + j * XSTEP
        ax.add_patch(FancyBboxPatch((x, y), SIZE, SIZE - 2, boxstyle="round,pad=0,rounding_size=3",
                                    fc=COL[c], ec="none"))
# key number written on the chart
right = X0 + 3 * (3 * XSTEP + GROUP)
ax.text(right + 22, Y0 + 8 * YSTEP, "180", ha="left", va="center", family="monospace",
        fontweight="bold", fontsize=34 * PT, color=cs.C["cream"])
ax.text(right + 22, Y0 + 8 * YSTEP + 34, "pairings,\nevery square\na Lean verdict", ha="left", va="top",
        fontsize=14 * PT, color=cs.C["text"], linespacing=1.35)
print(cs.save(fig, OUT / "matrix"))

# ---------- 2. DEMOS-tab screenshot ----------
src = Image.open(PITCH / "assets" / "site" / "demo-long@2x.png").convert("RGB")
crop = src.crop((0, 0, src.width, 1790))   # header + the three numbered panels
crop = crop.resize((1366, round(1366 * crop.height / crop.width)), Image.LANCZOS)
crop.save(OUT / "demo_site.png", optimize=True)
print("demo_site.png", crop.size)
