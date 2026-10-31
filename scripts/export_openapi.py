#!/usr/bin/env python
"""Write the OpenAPI schema to openapi.json for Antigravity."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.api import app  # noqa: E402

(ROOT / "openapi.json").write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
print(f"wrote openapi.json ({len(app.openapi()['paths'])} paths)")
