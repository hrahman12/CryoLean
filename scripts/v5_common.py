"""Shared helpers for the v5 deep scrape: the local snapshot cache and verbatim-quote checks.

Snapshots (raw bytes + extracted text) live in research/v5/cache/, which is gitignored: only URLs, hashes and short
quotes are committed. Every quote that backs an imported value must occur in the snapshot text after norm()."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V5 = ROOT / "research" / "v5"
CACHE = V5 / "cache"

_DASHES = dict.fromkeys(map(ord, "‐‑‒–—―−﹘﹣－"), "-")
_QUOTES = {ord("‘"): "'", ord("’"): "'", ord("‚"): "'", ord("‛"): "'", ord("′"): "'",
           ord("“"): '"', ord("”"): '"', ord("„"): '"', ord("″"): '"'}


def url_id(url: str) -> str:
    return hashlib.sha1(url.strip().encode("utf-8")).hexdigest()[:16]


def paths(url: str) -> dict:
    i = url_id(url)
    return {"id": i, "raw": CACHE / f"{i}.raw", "text": CACHE / f"{i}.txt", "meta": CACHE / f"{i}.json"}


def norm(s: str) -> str:
    """Comparison form: NFKC, unified dashes and quotes, no soft hyphens or zero-width marks, table separators and all
    whitespace runs collapsed to one space, case kept."""
    s = unicodedata.normalize("NFKC", s).translate(_DASHES).translate(_QUOTES)
    s = re.sub("[­​‌‍﻿]", "", s)
    s = s.replace("|", " ")
    return re.sub(r"\s+", " ", s).strip()


def load_text(url: str) -> str | None:
    p = paths(url)["text"]
    return p.read_text(encoding="utf-8") if p.exists() else None


def load_meta(url: str) -> dict | None:
    p = paths(url)["meta"]
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def quote_in(text: str, quote: str) -> bool:
    q = norm(quote)
    return bool(q) and q in norm(text)


_NUM = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?")


def numbers(s: str) -> list[str]:
    """Numerals printed in s; thousands separators removed (1,000 -> 1000), decimal commas read as points."""
    out = []
    for m in _NUM.finditer(norm(s)):
        t = m.group(0)
        if re.fullmatch(r"[-+]?\d{1,3}(,\d{3})+(\.\d+)?", t):
            t = t.replace(",", "")
        out.append(t.replace(",", "."))
    return out


def number_in(quote: str, value) -> bool:
    """True when the printed value (as the extractor read it from the source) occurs as a numeral in the quote."""
    try:
        v = Decimal(str(value).replace(",", "").strip())
    except InvalidOperation:
        return False
    for t in numbers(quote):
        try:
            d = Decimal(t)
        except InvalidOperation:
            continue
        if d == v or abs(d) == abs(v):
            return True
    return False
