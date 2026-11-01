#!/usr/bin/env python
"""Review research candidates and promote one into the trusted catalog database.

    python scripts/promote_candidate.py --list
    python scripts/promote_candidate.py <candidate_id> --reviewed-by "Name"

Candidates with validation errors are refused; the reviewer is recorded in the promoted profile.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cryolean import research  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate_id", nargs="?")
    ap.add_argument("--reviewed-by")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    cat = Catalog()
    if a.list or not a.candidate_id:
        for c in research.list_candidates(cat):
            print(c["id"], c["kind"], c["document"].get("id"), c["review_status"], "valid" if c["validation"]["ok"] else "INVALID")
        return 0
    try:
        rec = research.promote(cat, a.candidate_id, a.reviewed_by or "")
    except research.ResearchError as e:
        print(f"refused: {e}")
        return 1
    print(f"promoted {rec['id']} ({rec['document'].get('id')}) reviewed by {rec['reviewed_by']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
