#!/usr/bin/env python
"""Draw docs/images/pipeline.svg: the CryoLean pipeline with each tool's logo embedded (GitHub renders SVGs
through <img>, which blocks external resources, so the logos are inlined as base64)."""
from __future__ import annotations

import base64
import io
from html import escape
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
LOGOS = ROOT / "docs" / "images" / "logos"
OUT = ROOT / "docs" / "images" / "pipeline.svg"

W, H = 1500, 1010
FONT = "Segoe UI, Helvetica, Arial, sans-serif"
MONO = "Consolas, Menlo, monospace"


def logo(name: str, size: int = 44) -> str:
    p = LOGOS / name
    if p.suffix == ".svg":
        return "data:image/svg+xml;base64," + base64.b64encode(p.read_bytes()).decode()
    im = Image.open(p).convert("RGBA")
    im.thumbnail((size * 2, size * 2))
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


parts: list[str] = []


def add(s: str) -> None:
    parts.append(s)


def text(x, y, s, size=14, weight="normal", fill="#1f2328", anchor="start", family=FONT, style="normal"):
    add(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}" font-style="{style}">{escape(s)}</text>')


def img(x, y, name, size=40):
    add(f'<image x="{x}" y="{y}" width="{size}" height="{size}" href="{logo(name, size)}" '
        f'preserveAspectRatio="xMidYMid meet"/>')


def box(x, y, w, h, fill="#ffffff", stroke="#d0d7de", dash=None, r=10, sw=1.5):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def card(x, y, w, h, logos, title, lines, path=None, fill="#ffffff", stroke="#d0d7de", dash=None, mono_lines=()):
    box(x, y, w, h, fill, stroke, dash)
    lx = x + 12
    for n in logos:
        img(lx, y + 12, n, 40)
        lx += 46
    text(lx + 4, y + 30, title, 16, "bold")
    if path:
        text(lx + 4, y + 49, path, 12, fill="#59636e", family=MONO)
    ty = y + 76
    for i, ln in enumerate(lines):
        mono = i in mono_lines
        text(x + 14, ty, ln, 13 if not mono else 12.5, family=MONO if mono else FONT, fill="#1f2328")
        ty += 19


def arrow(x1, y1, x2, y2, color="#59636e", dash=None, label=None, lx=None, ly=None, width=2):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{d} '
        f'marker-end="url(#ah-{color[1:]})"/>')
    if label:
        text(lx if lx is not None else (x1 + x2) / 2, ly if ly is not None else (y1 + y2) / 2 - 6, label, 11.5,
             fill=color, anchor="middle", style="italic")


def path_arrow(d, color="#59636e", dash=None, width=2):
    ds = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{ds} marker-end="url(#ah-{color[1:]})"/>')


COLORS = ["#59636e", "#bc4c00", "#1a7f37", "#0969da", "#8250df"]
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add("<defs>" + "".join(
    f'<marker id="ah-{c[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
    f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>' for c in COLORS) + "</defs>")
box(0, 0, W, H, "#ffffff", "#ffffff", r=0)

# ---------------------------------------------------------------- title
text(30, 44, "CryoLean pipeline", 28, "bold")
text(30, 70, "Lanyon, Z3 and Claude propose. The Lean 4 kernel decides. Only Lean-verified fixes reach the user, and every "
     "verdict comes back as a card with its theorems, axioms and source hash.", 15, fill="#59636e")

# ---------------------------------------------------------------- column headers
COLS = {"in": (44, 276), "un": (342, 416), "tr": (832, 390), "out": (1250, 220)}
text(COLS["in"][0], 112, "INPUTS", 13, "bold", "#59636e")
text(COLS["un"][0], 112, "UNTRUSTED  ·  proposers (hints only)", 13, "bold", "#bc4c00")
text(COLS["tr"][0], 112, "TRUSTED  ·  Lean 4 kernel", 13, "bold", "#1a7f37")
text(COLS["out"][0], 112, "OUTPUTS", 13, "bold", "#59636e")

# zones
box(340, 122, 420, 720, "#fff8f2", "#bc4c00", dash="8 6", r=14)
box(830, 122, 392, 720, "#f0faf3", "#1a7f37", r=14, sw=2)

# ---------------------------------------------------------------- inputs
x, w = COLS["in"]
card(x, 130, w, 150, ["codex.png", "pywebview.png"], "Desktop UI + website",
     ["PyWebView window (bridge), or", "python -m cryolean serve: website +", "/api/check, /api/apply-fix,", "/api/lanyon. Same CryoLeanAPI."],
     "cryolean/server.py")
card(x, 296, w, 150, ["sqlite.jpg"], "Cryostat sheet",
     ["220 configurations,", "3,335 sourced evidence records.", "Missing facts stay UNKNOWN."],
     "data/cryostats  ->  SQLite")
card(x, 462, w, 150, ["sqlite.jpg"], "Experiment sheet",
     ["204 experiments from published", "procedures, 20 industries,", "40 physical properties,", "13 coupled models."],
     "data/experiments  ->  SQLite")
card(x, 628, w, 150, ["python.png"], "Python boundary",
     ["Exact rational units (no floats)", "and fail-closed JSON for Lean.", "Python never decides a verdict."],
     "cryolean/serialize.py")

# ---------------------------------------------------------------- untrusted proposers
x, w = COLS["un"]
cw = w - 20
card(x + 10, 132, cw, 160, ["z3.jpg"], "Z3 feasibility search",
     ["assert_and_track: unsat core = the reason,", "with the datasheet facts it rests on.",
      "Ranked alternative cryostats and minimal", "parameter changes, each re-checked by Lean."], "cryolean/smt.py", stroke="#e7b48f")
card(x + 10, 304, cw, 160, ["z3.jpg"], "Z3 campaign scheduler",
     ["Packs several ACCEPTED experiments into", "one cooldown and minimises the makespan.",
      "If they cannot fit, the unsat core names", "which experiments conflict."], "cryolean/schedule.py", stroke="#e7b48f")
card(x + 10, 476, cw, 160, ["claude.svg"], "Claude: new rule or new sheet",
     ["Matches plain language to a profile", "(closed set). Drafts new Lean rules or",
      "new sheets, stored as untrusted", "candidates until reviewed."], "cryolean/ai.py, research.py", stroke="#e7b48f")
card(x + 10, 648, cw, 182, ["lanyon.png"], "Lanyon AI: fixes, chat, simulation",
     ["Proposes repair values for failing setups", "and answers the website chat (/api/lanyon).",
      "Every candidate is re-checked by Lean.", "Certified simulations (Lean + Rocq proof)", "count only via the Gatekeeper."],
     "cryolean/lanyon.py", stroke="#e7b48f")

# ---------------------------------------------------------------- trusted Lean kernel
x, w = COLS["tr"]
cw = w - 20
card(x + 5, 132, cw, 236, ["lean.png"], "verdict cfg e",
     ["One universal checker over exact rationals", "with SI dimensions. Proved:",
      "verdict_accept_iff   accept <-> AcceptSpec", "verdict_reject_sound reject -> violation",
      "fail_needs_trusted   rejects need sources", "accept_no_unknown    no guessing",
      "pass_dims_all_match  no unit mix-ups"],
     "lean/CryoLean/Checker.lean, Soundness.lean", stroke="#7fc79a", mono_lines=(2, 3, 4, 5, 6))
card(x + 5, 380, cw, 180, ["lean.png"], "validSchedule",
     ["Bounds: cooldown <= start, stop <= run end.", "Slots pairwise disjoint. Only accepted",
      "experiments. Proved:", "validSchedule_sound / _complete", "_bounds / _disjoint / _only_accepted"],
     "lean/CryoLean/Schedule.lean", stroke="#7fc79a", mono_lines=(3, 4))
card(x + 5, 572, cw, 258, ["lean.png", "forall.png"], "Gatekeeper + audit",
     ["Admits Lean code only if it compiles,", "has no sorry / axiom / native_decide,",
      "and #print axioms is a subset of", "{propext, Classical.choice, Quot.sound}.",
      "Forall forensics audits the kernel itself", "(scripts/run_forensics.py): 839 declarations,",
      "0 smells, 0 unsafe flags. Its judges found", "one soundness gap, now fixed and proved."],
     "cryolean/gatekeeper.py", stroke="#7fc79a")

# ---------------------------------------------------------------- outputs
x, w = COLS["out"]
box(x, 132, w, 236, "#ffffff", "#d0d7de")
text(x + 14, 160, "Three verdicts", 16, "bold")
for i, (v, c, d) in enumerate([("REQUIREMENTS_MET", "#1a7f37", "every mandatory check passed"),
                               ("DOES_NOT_MEET", "#cf222e", "sourced limit violated"),
                               ("NEED_MORE_INFO", "#9a6700", "missing or untrusted data")]):
    yy = 190 + i * 58
    add(f'<rect x="{x + 14}" y="{yy}" width="{w - 28}" height="48" rx="8" fill="{c}" fill-opacity="0.09" stroke="{c}"/>')
    text(x + 24, yy + 20, v, 13.5, "bold", c, family=MONO)
    text(x + 24, yy + 38, d + (" + reason" if i == 1 else ""), 12, fill="#1f2328")
box(x, 380, w, 180, "#ffffff", "#d0d7de")
text(x + 14, 408, "Schedule", 16, "bold")
add(f'<rect x="{x + 14}" y="{424}" width="{w - 28}" height="48" rx="8" fill="#1a7f37" fill-opacity="0.09" stroke="#1a7f37"/>')
text(x + 24, 444, "Schedule OK", 13.5, "bold", "#1a7f37", family=MONO)
text(x + 24, 462, "checked slot list", 12)
add(f'<rect x="{x + 14}" y="{482}" width="{w - 28}" height="62" rx="8" fill="#cf222e" fill-opacity="0.07" stroke="#cf222e"/>')
text(x + 24, 502, "Rejected", 13.5, "bold", "#cf222e", family=MONO)
text(x + 24, 520, "with Lean's reasons, or", 12)
text(x + 24, 536, "Z3's unsat core", 12)
box(x, 572, w, 258, "#ffffff", "#d0d7de")
text(x + 14, 600, "Fixes + Registry", 16, "bold")
for i, ln in enumerate(["Suggested fixes:", "Lean-verified only, else", "\"No verified solution found\".", "Apply fix re-runs Lean on", "the same input hash.", "",
                        "Rule Registry: admitted rules", "only (SHA-256, theorems)."]):
    text(x + 14, 626 + i * 19, ln, 13, family=MONO if ln == "certified_simulation" else FONT)

# ---------------------------------------------------------------- arrows
# inputs -> proposers and kernel
path_arrow("M320,205 C 334,205 334,212 350,212")
path_arrow("M320,371 C 334,371 334,384 350,384")
path_arrow("M320,537 C 334,537 334,556 350,556")
add('<line x1="320" y1="703" x2="328" y2="703" stroke="#59636e" stroke-width="2"/>')
path_arrow("M328,703 L 328,862 L 1026,862 L 1026,846", "#59636e")
text(680, 880, "exact Lean JSON for every check", 12, fill="#59636e", anchor="middle", style="italic")
# proposers -> kernel (dashed: hints)
arrow(752, 212, 840, 232, "#bc4c00", "6 5", "hint", 795, 210)
arrow(752, 384, 840, 440, "#bc4c00", "6 5", "slots", 795, 398)
arrow(752, 556, 840, 650, "#bc4c00", "6 5", "Lean code", 792, 578)
arrow(752, 739, 840, 739, "#bc4c00", "6 5", "proof", 795, 731)
arrow(752, 700, 840, 330, "#8250df", "6 5", "fix candidates", 770, 470)
# kernel -> outputs
arrow(1214, 250, 1248, 250, "#1a7f37", width=2.5)
arrow(1214, 470, 1248, 470, "#1a7f37", width=2.5)
arrow(1214, 700, 1248, 700, "#1a7f37", width=2.5)
# Z3 suggestions re-checked by Lean

# ---------------------------------------------------------------- verdict card back to UI
box(30, 900, 1440, 86, "#f6f8fa", "#0969da", r=12, sw=2)
img(46, 920, "lean.png", 44)
text(102, 936, "Verdict card, back to the UI", 17, "bold", "#0969da")
text(102, 960, "verdict  ·  reason  ·  theorem names  ·  their axioms (cached #print axioms)  ·  Lean source hash  ·  input hash",
     14, family=FONT)
text(1452, 948, "Lanyon and Z3 output are hints, never verdicts.", 15, "bold", "#bc4c00", anchor="end")
path_arrow("M1360,836 L 1360,896", "#0969da")
path_arrow("M22,900 L 22,205 L 40,205", "#0969da")

add("</svg>")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(parts), encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
