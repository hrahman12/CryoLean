#!/usr/bin/env python
"""Promote a reviewed research candidate into the trusted catalog.

    python scripts/promote_candidate.py <candidate_id> --reviewed-by "Name"

Refuses candidates with validation errors. Records the reviewer in the promoted profile.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.catalog import Catalog  # noqa: E402
from backend.research_pipeline import ResearchPipeline  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate_id")
    ap.add_argument("--reviewed-by", required=True)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    pipe = ResearchPipeline(Catalog())
    if args.list:
        for c in pipe.list_candidates():
            print(c["id"], c["kind"], c["document"].get("id"), c["review_status"], "valid" if c["validation"]["ok"] else "INVALID")
        return 0
    try:
        rec = pipe.promote(args.candidate_id, args.reviewed_by)
    except ValueError as e:
        print(f"refused: {e}")
        return 1
    print(f"promoted {rec['id']} -> data/{rec['promoted_to']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
