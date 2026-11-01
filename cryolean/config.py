"""Paths and environment configuration (all local; no server required)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = Path(os.environ.get("CRYOLEAN_SEED_DIR", ROOT / "data"))
LEAN_DIR = ROOT / "lean"

_default_bin = LEAN_DIR / ".lake" / "build" / "bin" / ("cryolean.exe" if sys.platform == "win32" else "cryolean")


def db_path() -> Path:
    """SQLite database path. Override with CRYOLEAN_DB (tests use temporary copies)."""
    return Path(os.environ.get("CRYOLEAN_DB", str(ROOT / "data" / "cryolean.db")))


def lean_binary_path() -> Path:
    """Compiled Lean checker. Override with CRYOLEAN_LEAN_BIN."""
    return Path(os.environ.get("CRYOLEAN_LEAN_BIN", str(_default_bin)))


def lean_timeout() -> float:
    return float(os.environ.get("CRYOLEAN_LEAN_TIMEOUT", "120"))


def ai_provider() -> str:
    """'lexical' (offline default) or 'claude' (needs ANTHROPIC_API_KEY or an `ant auth login` profile)."""
    return os.environ.get("CRYOLEAN_AI_PROVIDER", "lexical")


def claude_model() -> str:
    return os.environ.get("CRYOLEAN_CLAUDE_MODEL", "claude-opus-5-5")
