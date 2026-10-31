"""Paths and environment configuration."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("CRYOLEAN_DATA_DIR", ROOT / "data"))
LEAN_DIR = ROOT / "lean"
REGISTRY_DIR = DATA_DIR / "registry"       # dynamic registrations (industries, vocabulary proposals)
CANDIDATES_DIR = DATA_DIR / "candidates"   # research candidates awaiting review (never trusted)
RESEARCH_REQUESTS_DIR = DATA_DIR / "research_requests"

_default_bin = LEAN_DIR / ".lake" / "build" / "bin" / ("cryolean.exe" if sys.platform == "win32" else "cryolean")


def lean_binary_path() -> Path:
    """Path of the compiled Lean checker. Override with CRYOLEAN_LEAN_BIN (tests use a bogus path)."""
    return Path(os.environ.get("CRYOLEAN_LEAN_BIN", str(_default_bin)))


LEAN_TIMEOUT_S = float(os.environ.get("CRYOLEAN_LEAN_TIMEOUT", "60"))
AI_PROVIDER = os.environ.get("CRYOLEAN_AI_PROVIDER", "lexical")  # "lexical" | "claude"
CLAUDE_MODEL = os.environ.get("CRYOLEAN_CLAUDE_MODEL", "claude-opus-5-5")
