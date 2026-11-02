"""Draw the generic cryostat used on CryoLean title slides (no real model), in the deck palette.

    pitch/.venv/Scripts/python.exe pitch/shared/make_cryostat_svg.py            -> shared/cryostat.svg
    ... make_cryostat_svg.py --ring 3 --ring-color pink --out x.svg               -> ring stopped at stage 3, red

Stages, warm to cold: 300 K flange, 50 K, 4 K, still, cold plate, mixing chamber, sample.
The plates shift from cream to teal as they get colder; a purple ring (Lean's check) sits at the sample by default.
"""
from __future__ import annotations

import argparse
import pathlib
import random

PALETTE = {"purple": "#b8a4ff", "teal": "#2dd4bf", "orange": "#f5a524", "pink": "#f0609e"}

# (label, y, height, half-width, fill) warm -> cold
PLATES = [
    ("300 K", 70, 20, 180, "#ece7dd"),
    ("50 K", 140, 12, 160, "#e2e4e3"),
    ("4 K", 200, 12, 140, "#d6e4e8"),
    ("1 K", 255, 11, 118, "#c6e7ea"),
    ("100 mK", 305, 10, 98, "#ade9e4"),
    ("10 mK", 350, 10, 78, "#7fded0"),
]
CX = 330


def build(ring_stage: int | None, ring_color: str, labels: bool) -> str:
    rnd = random.Random(7)
    out: list[str] = []
    add = out.append
    add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 740 440" width="740" height="440">')
    add("<defs>"
        '<radialGradient id="cold" cx="50%" cy="50%" r="50%">'
        '<stop offset="0" stop-color="#2dd4bf" stop-opacity="0.55"/>'
        '<stop offset="0.45" stop-color="#2dd4bf" stop-opacity="0.16"/>'
        '<stop offset="1" stop-color="#2dd4bf" stop-opacity="0"/></radialGradient>'
        '<filter id="glow" x="-50%" y="-200%" width="200%" height="500%">'
        '<feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '<linearGradient id="face" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#ffffff" stop-opacity="0.35"/><stop offset="1" stop-color="#000000" stop-opacity="0.18"/></linearGradient>'
        '<linearGradient id="fadev" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#fff" stop-opacity="1"/><stop offset="0.8" stop-color="#fff" stop-opacity="1"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        '<mask id="fade" maskUnits="userSpaceOnUse" x="0" y="0" width="740" height="440">'
        '<rect x="0" y="300" width="740" height="140" fill="url(#fadev)"/><rect x="0" y="0" width="740" height="300" fill="#fff"/></mask>'
        "</defs>")

    # faint isotherms behind everything, fading out at the bottom edge
    add('<g mask="url(#fade)">')
    for i, (rx, ry, op) in enumerate([(300, 64, 0.10), (230, 50, 0.13), (160, 36, 0.17), (100, 23, 0.22)]):
        add(f'<ellipse cx="{CX}" cy="400" rx="{rx}" ry="{ry}" fill="none" stroke="#2dd4bf" stroke-opacity="{op}" stroke-width="1"/>')
    add("</g>")
    add(f'<circle cx="{CX}" cy="398" r="78" fill="url(#cold)"/>')

    # outer vacuum can, dashed
    add('<rect x="128" y="96" width="404" height="330" rx="28" fill="none" stroke="#2a3a5a" stroke-width="1.5" stroke-dasharray="3 7"/>')

    # frost particles inside the can, denser near the cold end
    for _ in range(70):
        x = rnd.uniform(140, 520)
        y = rnd.uniform(110, 420)
        if rnd.random() < (y - 100) / 340:
            r = rnd.choice([0.9, 1.2, 1.6, 2.0])
            col = rnd.choice(["#2dd4bf", "#9fb3c8", "#2dd4bf", "#c9d2dc"])
            add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{col}" fill-opacity="{rnd.uniform(0.25, 0.7):.2f}"/>')

    # wiring from the flange down to the mixing chamber (drawn first, plates cover it)
    wires = [(205, 268, PALETTE["purple"]), (238, 284, PALETTE["purple"]), (455, 392, PALETTE["orange"]), (430, 380, PALETTE["purple"])]
    for x0, x1, col in wires:
        add(f'<path d="M{x0} 90 C {x0} 200, {x1} 230, {x1} 350" fill="none" stroke="{col}" stroke-opacity="0.55" stroke-width="1.6"/>')

    # support rods between plates
    for (lab_a, ya, ha, wa, _), (lab_b, yb, hb, wb, _) in zip(PLATES, PLATES[1:]):
        for fx in (-0.82, -0.32, 0.32, 0.82):
            x = CX + fx * wb
            add(f'<line x1="{x:.1f}" y1="{ya + ha}" x2="{x:.1f}" y2="{yb}" stroke="#7f8ea3" stroke-width="2"/>')

    # pulse-tube head with a status light (a nod to the LeanKeel mast)
    add('<line x1="400" y1="10" x2="400" y2="42" stroke="#dfe5ec" stroke-width="3"/>')
    add('<line x1="388" y1="10" x2="412" y2="10" stroke="#dfe5ec" stroke-width="3"/>')
    add(f'<circle cx="400" cy="27" r="6" fill="{PALETTE["orange"]}"/>')
    add('<rect x="372" y="40" width="56" height="30" rx="3" fill="#dfe5ec" stroke="#9aa6b5" stroke-width="1"/>')
    add('<rect x="380" y="47" width="40" height="7" rx="1" fill="#c9c3f5" fill-opacity="0.85"/>')

    # plates
    for i, (lab, y, h, hw, fill) in enumerate(PLATES):
        add(f'<rect x="{CX - hw}" y="{y}" width="{2 * hw}" height="{h}" rx="3" fill="{fill}"/>')
        add(f'<rect x="{CX - hw}" y="{y}" width="{2 * hw}" height="{h}" rx="3" fill="url(#face)"/>')
        if labels:
            ly = y + h / 2
            add(f'<line x1="{CX + hw + 10}" y1="{ly}" x2="548" y2="{ly}" stroke="#3a4a68" stroke-width="1" stroke-dasharray="1 4"/>')
            add(f'<text x="556" y="{ly + 5}" font-family="Consolas, monospace" font-size="15" fill="#8794a8">{lab}</text>')

    # cold finger, sample holder and sample
    add('<rect x="322" y="360" width="16" height="30" fill="#9fdcd4"/>')
    add(f'<rect x="310" y="390" width="40" height="12" rx="2" fill="{PALETTE["teal"]}"/>')
    if labels:
        add('<line x1="360" y1="396" x2="548" y2="396" stroke="#3a4a68" stroke-width="1" stroke-dasharray="1 4"/>')
        add('<text x="556" y="401" font-family="Consolas, monospace" font-size="15" fill="#2dd4bf">sample</text>')

    # Lean's check ring
    ring_y = {None: 396}.get(ring_stage, None)
    if ring_stage is not None:
        lab, y, h, hw, _ = PLATES[max(0, min(ring_stage, len(PLATES) - 1))]
        ring_y, ring_rx = y + h / 2, hw + 22
    else:
        ring_rx = 58
    col = PALETTE.get(ring_color, ring_color)
    add(f'<ellipse cx="{CX}" cy="{ring_y}" rx="{ring_rx}" ry="{max(9, ring_rx * 0.2):.1f}" fill="none" stroke="{col}" stroke-width="3" filter="url(#glow)"/>')

    add("</svg>")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ring", type=int, default=None, help="plate index 0-5 for the ring (default: at the sample)")
    ap.add_argument("--ring-color", default="purple")
    ap.add_argument("--no-labels", action="store_true")
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path(__file__).with_name("cryostat.svg"))
    a = ap.parse_args()
    a.out.write_text(build(a.ring, a.ring_color, not a.no_labels), encoding="utf-8")
    print(a.out)


if __name__ == "__main__":
    main()
