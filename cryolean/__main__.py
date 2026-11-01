"""Command line for the local backend.

    python -m cryolean build-db                 # (re)build data/cryolean.db from the JSON seeds
    python -m cryolean validate                 # source-data validation
    python -m cryolean methods                  # list bridge methods
    python -m cryolean call <method> '<json>'   # call a bridge method with JSON keyword arguments
    python -m cryolean demo                     # acceptance demonstrations A, B, C, D
    python -m cryolean serve [--port 8000]      # HTTP API + website in live mode (real Lean checks)
"""
from __future__ import annotations

import inspect
import json
import sys


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[0]
    if cmd == "build-db":
        from . import db
        print("built", db.build_database())
        return 0
    if cmd == "validate":
        from .catalog import Catalog
        from .validation import validate_catalog
        rep = validate_catalog(Catalog())
        for i in rep.issues:
            print(i)
        print(f"errors: {len(rep.errors)}  warnings: {len(rep.warnings)}")
        return 0 if rep.ok else 1
    if cmd == "methods":
        from .bridge import CryoLeanAPI
        for name, fn in inspect.getmembers(CryoLeanAPI, predicate=inspect.isfunction):
            if not name.startswith("_"):
                print(f"{name}{inspect.signature(fn)}".replace("(self, ", "(").replace("(self)", "()"))
                print("    " + (fn.__doc__ or "").strip().splitlines()[0] if fn.__doc__ else "")
        return 0
    if cmd == "call":
        from .bridge import CryoLeanAPI
        api = CryoLeanAPI()
        kwargs = json.loads(argv[2]) if len(argv) > 2 else {}
        print(json.dumps(getattr(api, argv[1])(**kwargs), indent=2, ensure_ascii=False))
        return 0
    if cmd == "serve":
        from .server import main as serve
        return serve(argv[1:])
    if cmd == "demo":
        from .demo import run
        return run()
    print(f"unknown command {cmd!r}\n{__doc__}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
