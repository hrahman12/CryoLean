"""Screenshot a page (e.g. the CryoLean website) with headless Edge, for use on a slide.

    pitch/.venv/Scripts/python.exe pitch/shared/screenshot.py <url-or-file> <out.png> [--size 1456,1000] [--scale 2] [--wait 12]

The website on main is CryoLean-main/site/index.html (Live checker); add #demo for the Demos tab.
Pages with endless animations never go idle, so this waits a fixed real time (--wait seconds) and then shoots.
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from render import browser  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("out", type=pathlib.Path)
    ap.add_argument("--size", default="1456,1000")
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--wait", type=float, default=12.0, help="seconds to let the page load and animate")
    a = ap.parse_args()

    url = a.url
    if "://" not in url:
        p, _, frag = url.partition("#")
        url = pathlib.Path(p).resolve().as_uri() + (f"#{frag}" if frag else "")
    out = a.out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    profile = tempfile.mkdtemp(prefix="cryolean-shot-")
    cmd = [browser(), "--headless=new", f"--user-data-dir={profile}", "--disable-gpu", "--hide-scrollbars",
           "--no-first-run", "--mute-audio", "--autoplay-policy=user-gesture-required",
           f"--force-device-scale-factor={a.scale}", f"--window-size={a.size}",
           f"--timeout={int(a.wait * 1000)}", f"--screenshot={out}", url]
    try:
        subprocess.run(cmd, capture_output=True, timeout=a.wait + 60)
    except subprocess.TimeoutExpired:
        print("browser did not exit in time")
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    if not out.exists():
        print("no screenshot written")
        return 1
    print(out, out.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
