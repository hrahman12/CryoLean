"""Build the images for the v2 Demo-first deck.

    pitch/.venv/Scripts/python.exe pitch/v2-demo/build_charts.py

1. charts/demo.png: the top of the website's Demos tab (pitch/assets/site/demo-long@2x.png, newest site build),
   cropped to the header and the three numbered panels, downscaled to 2x of its slide slot.
2. charts/cryostat.svg: the generic title-slide cryostat with a teal ring (shared/make_cryostat_svg.py).
"""
import pathlib
import subprocess
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
PITCH = HERE.parent
OUT = HERE / "charts"
OUT.mkdir(exist_ok=True)

# 1 · Demos tab screenshot crop (source is 2912 px wide, a 2x capture)
src = Image.open(PITCH / "assets" / "site" / "demo-long@2x.png").convert("RGB")
box = (16, 0, 2896, 1772)                       # header + panels 1-3 (choose example, choose cryostat, check setup)
crop = src.crop(box)
slot_w = 690                                    # CSS px width of the .panel on slide 3
w = slot_w * 2
crop = crop.resize((w, round(crop.height * w / crop.width)), Image.LANCZOS)
crop.save(OUT / "demo.png", optimize=True)
print("demo.png", crop.size, "aspect", round(crop.width / crop.height, 4))

# 2 · title art
subprocess.run([sys.executable, str(PITCH / "shared" / "make_cryostat_svg.py"),
                "--ring-color", "teal", "--out", str(OUT / "cryostat.svg")], check=True)
print("cryostat.svg")
