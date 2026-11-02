"""Render a CryoLean pitch deck (HTML, one <section class="slide"> per page) to PDF and PNGs.

    pitch/.venv/Scripts/python.exe pitch/shared/render.py pitch/v1-.../deck.html --pdf pitch/CryoLean_pitch_v1.pdf

Steps: layout check in headless Edge (deck loaded with ?check, see check.js), print to PDF with headless Edge,
verify page count and page size, rasterize every page to png/slide-N.png and a png/contact.png overview.
Exit code 1 if the layout check finds problems (unless --allow-issues) or the PDF is wrong.
"""
from __future__ import annotations

import argparse
import html as htmlmod
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

import pymupdf as fitz
from PIL import Image

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]
SLIDE_W_PT, SLIDE_H_PT = 1440.0, 810.0  # 1920 x 1080 CSS px, same page size as the LeanKeel PDF


def browser() -> str:
    for p in EDGE_CANDIDATES:
        if pathlib.Path(p).exists():
            return p
    sys.exit("no Edge/Chrome found")


def run_browser(args: list[str], timeout: int = 180) -> subprocess.CompletedProcess:
    profile = tempfile.mkdtemp(prefix="cryolean-pitch-edge-")
    try:
        cmd = [browser(), "--headless=new", f"--user-data-dir={profile}", "--disable-gpu", "--no-first-run",
               "--no-default-browser-check", "--disable-extensions", "--hide-scrollbars",
               "--force-device-scale-factor=1", *args]
        return subprocess.run(cmd, capture_output=True, timeout=timeout, text=True, encoding="utf-8", errors="replace")
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def layout_check(deck: pathlib.Path) -> dict:
    url = deck.as_uri() + "?check=1"
    res = run_browser(["--window-size=1456,819", "--virtual-time-budget=20000", "--dump-dom", url])
    m = re.search(r'<pre id="layout-report">(.*?)</pre>', res.stdout, re.S)
    if not m:
        return {"error": "no layout report (is shared/check.js included?)", "stderr": res.stderr[-800:]}
    return json.loads(htmlmod.unescape(m.group(1)))


def print_pdf(deck: pathlib.Path, pdf: pathlib.Path) -> None:
    pdf.parent.mkdir(parents=True, exist_ok=True)
    if pdf.exists():
        pdf.unlink()
    run_browser(["--run-all-compositor-stages-before-draw", "--virtual-time-budget=20000",
                 "--no-pdf-header-footer", "--print-to-pdf-no-header", f"--print-to-pdf={pdf}", deck.as_uri()])
    if not pdf.exists():
        sys.exit(f"PDF was not written: {pdf}")


def rasterize(pdf: pathlib.Path, outdir: pathlib.Path, zoom: float) -> list[pathlib.Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("slide-*.png"):
        old.unlink()
    paths = []
    with fitz.open(pdf) as doc:
        for i, page in enumerate(doc, start=1):
            s = 1456 * zoom / page.rect.width  # PNG is 1456 px wide at zoom 1, the design canvas
            pix = page.get_pixmap(matrix=fitz.Matrix(s, s), alpha=False)
            p = outdir / f"slide-{i}.png"
            pix.save(p)
            paths.append(p)
    return paths


def contact_sheet(pngs: list[pathlib.Path], out: pathlib.Path) -> None:
    if not pngs:
        return
    ims = [Image.open(p).convert("RGB") for p in pngs]
    w, h = 728, 410
    cols = 2
    rows = (len(ims) + cols - 1) // cols
    gap = 16
    sheet = Image.new("RGB", (cols * w + (cols + 1) * gap, rows * h + (rows + 1) * gap), (30, 36, 48))
    for i, im in enumerate(ims):
        im = im.resize((w, h), Image.LANCZOS)
        r, c = divmod(i, cols)
        sheet.paste(im, (gap + c * (w + gap), gap + r * (h + gap)))
    sheet.save(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("deck", type=pathlib.Path)
    ap.add_argument("--pdf", type=pathlib.Path, help="output PDF (default: next to the deck, deck.pdf)")
    ap.add_argument("--png", type=pathlib.Path, help="PNG folder (default: <deck folder>/png)")
    ap.add_argument("--zoom", type=float, default=1.0, help="PNG scale; 1.0 = 1456 x 819")
    ap.add_argument("--allow-issues", action="store_true", help="do not fail on layout-check issues")
    ap.add_argument("--skip-check", action="store_true")
    a = ap.parse_args()

    deck = a.deck.resolve()
    pdf = (a.pdf or deck.with_suffix(".pdf")).resolve()
    pngdir = (a.png or deck.parent / "png").resolve()
    n_slides = len(re.findall(r'<section[^>]*class="[^"]*\bslide\b', deck.read_text(encoding="utf-8")))

    ok = True
    if not a.skip_check:
        rep = layout_check(deck)
        if "error" in rep:
            print("LAYOUT CHECK ERROR:", rep)
            ok = False
        else:
            issues = rep["issues"]
            print(f"layout check: {rep['slides']} slides, {len(issues)} issue(s)")
            for it in issues:
                print("  ", json.dumps(it, ensure_ascii=False))
            if issues and not a.allow_issues:
                ok = False

    print_pdf(deck, pdf)
    with fitz.open(pdf) as doc:
        pages = len(doc)
        sizes = {(round(p.rect.width, 2), round(p.rect.height, 2)) for p in doc}
    print(f"pdf: {pdf} ({pages} pages, page size {sizes})")
    if pages != n_slides:
        print(f"PAGE COUNT MISMATCH: {n_slides} slides in HTML, {pages} pages in PDF (content spilling onto extra pages?)")
        ok = False
    if any(abs(w - SLIDE_W_PT) > 1 or abs(h - SLIDE_H_PT) > 1 for w, h in sizes):
        print(f"PAGE SIZE WRONG: expected {SLIDE_W_PT} x {SLIDE_H_PT} pt")
        ok = False

    pngs = rasterize(pdf, pngdir, a.zoom)
    contact_sheet(pngs, pngdir / "contact.png")
    print(f"png: {pngdir} ({len(pngs)} slides + contact.png)")
    print("RESULT:", "OK" if ok else "PROBLEMS FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
