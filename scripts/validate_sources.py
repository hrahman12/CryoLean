#!/usr/bin/env python
"""Validate the evidence database and catalog provenance.

Checks (see backend/validation.py):
* every evidence record has id, claim, source URL (http/https), document title, status, access date;
* specification/observation records carry a verbatim quote;
* every capability value is an integer in the canonical unit of its vocabulary key, with the right shape;
* every sourced capability and requirement points at existing evidence records;
* UNKNOWN values carry evidence_status "unknown" and no normalized number;
* requirement keys exist in the vocabulary (or are explicitly proposed).

Exit code 1 on any error.  `--check-urls` additionally issues HEAD/GET requests (network).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.catalog import Catalog  # noqa: E402
from backend.validation import validate_catalog  # noqa: E402


def check_urls(catalog: Catalog, timeout: float = 15.0) -> list[str]:
    import httpx
    problems = []
    seen = set()
    for rec in catalog.evidence.values():
        url = rec.get("source_url")
        if not url or url in seen:
            continue
        seen.add(url)
        try:
            r = httpx.head(url, follow_redirects=True, timeout=timeout, headers={"User-Agent": "CryoLean-validator/0.1"})
            if r.status_code in (405, 403):
                r = httpx.get(url, follow_redirects=True, timeout=timeout, headers={"User-Agent": "CryoLean-validator/0.1"})
            if r.status_code >= 400:
                problems.append(f"{url} -> HTTP {r.status_code}")
        except Exception as e:  # network problems are reported, not fatal
            problems.append(f"{url} -> {type(e).__name__}: {e}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--check-urls", action="store_true", help="also verify that source URLs respond (network)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    catalog = Catalog(args.data_dir) if args.data_dir else Catalog()
    rep = validate_catalog(catalog)
    if not args.quiet:
        for i in rep.errors:
            print(i)
        for i in rep.warnings:
            print(i)
    print(f"\nevidence records: {len(catalog.evidence)}  equipment: {len(catalog.equipment)}  "
          f"configurations: {len(catalog.configurations)}  experiments: {len(catalog.experiments)}")
    print(f"errors: {len(rep.errors)}  warnings: {len(rep.warnings)}")
    rc = 0 if rep.ok else 1
    if args.check_urls:
        probs = check_urls(catalog)
        for p in probs:
            print("[url]", p)
        print(f"url problems: {len(probs)} (informational; sites may block automated requests)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
