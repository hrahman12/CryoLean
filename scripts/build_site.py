#!/usr/bin/env python
"""Inline site/data.json (from scripts/export_site_data.py) into site/template.html -> site/index.html."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = (ROOT / "site/data.json").read_text(encoding="utf-8").replace("</", "<" + chr(92) + "/")
page = (ROOT / "site/template.html").read_text(encoding="utf-8").replace("__DATA__", data).replace("__CRYO3D__", (ROOT / "site/cryo3d.js").read_text(encoding="utf-8"))
(ROOT / "site/index.html").write_text(page, encoding="utf-8")
print("site/index.html", len(page), "bytes")
