#!/usr/bin/env python
"""Fetch source pages and PDFs into the local v5 snapshot cache and extract their text.

    python scripts/v5_snapshot.py URL [URL ...]      # prints one JSON line per URL
    python scripts/v5_snapshot.py --file urls.txt     # one URL per line
    python scripts/v5_snapshot.py --refresh URL       # fetch again even if cached

The text file (research/v5/cache/<id>.txt) is what extraction reads and what quotes are checked against: HTML table
rows become 'cell | cell | cell' lines, PDFs get '=== page N ===' markers. robots.txt is honoured, requests to one host
are spaced by at least 1.5 s (across processes) and the user agent names the project."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v5_common import CACHE, ROOT, paths  # noqa: E402

UA = "CryoLean-research/0.5 (+https://github.com/hrahman12/CryoLean; equipment specification verification)"
HOST_GAP = 1.5
MAX_BYTES = 60 * 1024 * 1024
_robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}


def _wait_host(host: str):
    d = CACHE / "_hosts"
    d.mkdir(parents=True, exist_ok=True)
    f = d / re.sub(r"[^A-Za-z0-9.-]", "_", host)
    try:
        last = float(f.read_text())
    except (OSError, ValueError):
        last = 0.0
    gap = time.time() - last
    if gap < HOST_GAP:
        time.sleep(HOST_GAP - gap)
    f.write_text(str(time.time()))


def _allowed(url: str) -> bool:
    u = urlparse(url)
    base = f"{u.scheme}://{u.netloc}"
    if base not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            r = requests.get(base + "/robots.txt", headers={"User-Agent": UA}, timeout=20)
            if r.status_code == 200:
                rp.parse(r.text.splitlines())
            else:
                rp = None
        except requests.RequestException:
            rp = None
        _robots[base] = rp
    rp = _robots[base]
    return True if rp is None else rp.can_fetch(UA, url)


def html_text(raw: bytes, encoding: str | None) -> tuple[str, str]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(raw, "lxml", from_encoding=encoding)
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    for t in soup(["script", "style", "noscript", "svg", "template", "iframe"]):
        t.decompose()
    for tr in soup.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
        tr.replace_with(soup.new_string("\n" + " | ".join(cells) + "\n"))
    for br in soup.find_all("br"):
        br.replace_with(soup.new_string("\n"))
    block = ["p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "dt", "dd", "table",
             "ul", "ol", "header", "footer", "tbody", "thead", "caption", "figcaption", "blockquote", "pre"]
    for b in soup.find_all(block):
        b.insert_before(soup.new_string("\n"))
        b.insert_after(soup.new_string("\n"))
    lines = [re.sub(r"[ \t ]+", " ", l).strip() for l in soup.get_text("").splitlines()]
    out, blank = [], False
    for l in lines:
        if l:
            out.append(l)
            blank = False
        elif not blank:
            out.append("")
            blank = True
    return "\n".join(out).strip() + "\n", title


def pdf_text(raw: bytes) -> tuple[str, str, int]:
    import pymupdf
    doc = pymupdf.open(stream=raw, filetype="pdf")
    parts = [f"=== page {i} ===\n" + page.get_text("text") for i, page in enumerate(doc, 1)]
    title = (doc.metadata or {}).get("title") or ""
    n = doc.page_count
    doc.close()
    return "\n".join(parts), title, n


def snapshot(url: str, refresh: bool = False) -> dict:
    url = url.strip()
    p = paths(url)
    if p["meta"].exists() and not refresh:
        m = json.loads(p["meta"].read_text(encoding="utf-8"))
        if m.get("status") == 200 and p["text"].exists():
            return {**m, "cached": True}
    CACHE.mkdir(parents=True, exist_ok=True)
    meta = {"url": url, "id": p["id"], "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    if not url.lower().startswith(("http://", "https://")):
        return {**meta, "status": None, "error": "not an http(s) URL"}
    if not _allowed(url):
        meta.update(status=None, error="disallowed by robots.txt")
        p["meta"].write_text(json.dumps(meta, indent=1), encoding="utf-8")
        return meta
    _wait_host(urlparse(url).netloc)
    try:
        r = requests.get(url, headers={"User-Agent": UA, "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.5"},
                         timeout=60, stream=True, allow_redirects=True)
        buf = bytearray()
        for chunk in r.iter_content(1 << 16):
            buf += chunk
            if len(buf) > MAX_BYTES:
                raise ValueError("larger than 60 MB")
        raw = bytes(buf)
    except (requests.RequestException, ValueError) as e:
        meta.update(status=None, error=f"{type(e).__name__}: {str(e)[:200]}")
        p["meta"].write_text(json.dumps(meta, indent=1), encoding="utf-8")
        return meta
    ctype = (r.headers.get("content-type") or "").lower()
    meta.update(status=r.status_code, final_url=r.url, content_type=ctype, bytes=len(raw),
                sha256=hashlib.sha256(raw).hexdigest())
    if r.status_code != 200:
        p["meta"].write_text(json.dumps(meta, indent=1), encoding="utf-8")
        return meta
    p["raw"].write_bytes(raw)
    try:
        if raw[:5] == b"%PDF-" or "pdf" in ctype:
            text, title, pages = pdf_text(raw)
            meta.update(kind="pdf", pages=pages)
        else:
            text, title = html_text(raw, r.encoding if "charset" in ctype else None)
            meta.update(kind="html")
    except Exception as e:  # malformed documents are reported, never fatal
        meta.update(error=f"text extraction failed: {type(e).__name__}: {str(e)[:200]}")
        p["meta"].write_text(json.dumps(meta, indent=1), encoding="utf-8")
        return meta
    p["text"].write_text(text, encoding="utf-8")
    meta.update(title=title[:300], chars=len(text), text_path=p["text"].relative_to(ROOT).as_posix())
    if len(text.strip()) < 400:
        meta["warning"] = "very little text: the page may need JavaScript"
    p["meta"].write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--file")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    urls = list(a.urls)
    if a.file:
        urls += [l.strip() for l in Path(a.file).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    for u in urls:
        m = snapshot(u, a.refresh)
        print(json.dumps({k: m.get(k) for k in ("url", "id", "status", "kind", "pages", "chars", "title", "text_path",
                                                 "error", "warning", "cached") if m.get(k) is not None}, ensure_ascii=False))


if __name__ == "__main__":
    main()
