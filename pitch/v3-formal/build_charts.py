"""Build the art for the v3 (formal methods) deck.

This deck has no data charts: its visuals are verbatim Lean code panels and a diagram drawn in HTML.
The only generated asset is the title illustration, a generic cryostat drawn in code with a purple (Lean) ring.

    pitch/.venv/Scripts/python.exe pitch/v3-formal/build_charts.py
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SHARED = HERE.parent / "shared"
OUT = HERE / "charts"
OUT.mkdir(exist_ok=True)

subprocess.run([sys.executable, str(SHARED / "make_cryostat_svg.py"),
                "--ring-color", "purple", "--out", str(OUT / "cryostat.svg")], check=True)
print("wrote", OUT / "cryostat.svg")
