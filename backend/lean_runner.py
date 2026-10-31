"""Run the compiled Lean checker.

The Python side never computes a verdict.  If the Lean binary is missing or
fails, ``LeanUnavailable`` is raised and the API answers 503 with
``verdict: null`` — there is no fallback verdict.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from . import config


class LeanUnavailable(Exception):
    """The Lean checker binary cannot be executed."""


class LeanDecodeError(Exception):
    """Lean rejected the input document (fail-closed decoding)."""


def lean_binary() -> Path | None:
    p = config.lean_binary_path()
    return p if p.exists() else None


def lean_version() -> str | None:
    b = lean_binary()
    if not b:
        return None
    try:
        out = subprocess.run([str(b), "version"], capture_output=True, text=True, timeout=20)
        return out.stdout.strip() or None
    except Exception:
        return None


def _run(args: list[str], timeout: float) -> str:
    b = lean_binary()
    if b is None:
        raise LeanUnavailable(f"Lean checker binary not found at {config.lean_binary_path()}; run `lake build` in lean/")
    try:
        proc = subprocess.run([str(b), *args], capture_output=True, text=True, timeout=timeout, encoding="utf-8")
    except (OSError, subprocess.TimeoutExpired) as e:
        raise LeanUnavailable(f"Lean checker failed to run: {e}")
    if proc.returncode not in (0, 2):
        raise LeanUnavailable(f"Lean checker exited with {proc.returncode}: {proc.stderr.strip()[:500]}")
    return proc.stdout


def run_check(configuration: dict, experiment: dict, timeout: float | None = None) -> dict:
    """Check one (configuration, experiment) pair. Returns the Lean result JSON."""
    doc = {"configuration": configuration, "experiment": experiment}
    fd, path = tempfile.mkstemp(suffix=".json", prefix="cryolean_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False)
        out = _run(["check", path], timeout or config.LEAN_TIMEOUT_S)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    try:
        res = json.loads(out.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as e:
        raise LeanUnavailable(f"Lean checker produced unreadable output: {e}: {out[:300]}")
    if res.get("error"):
        raise LeanDecodeError(res["error"])
    res["_input_document"] = doc
    return res


def run_batch(docs: list[tuple[dict, dict]], timeout: float | None = None) -> list[dict]:
    payload = [{"configuration": c, "experiment": e} for c, e in docs]
    fd, path = tempfile.mkstemp(suffix=".json", prefix="cryolean_batch_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        out = _run(["check-batch", path], timeout or config.LEAN_TIMEOUT_S * max(1, len(docs) // 4))
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    try:
        results = json.loads(out.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as e:
        raise LeanUnavailable(f"Lean checker produced unreadable output: {e}")
    for r, d in zip(results, payload):
        r["_input_document"] = d
    return results


def selftest() -> tuple[bool, str]:
    try:
        out = _run(["selftest"], 60)
    except LeanUnavailable as e:
        return False, str(e)
    return "all examples produced the expected verdict" in out, out


def proof_inventory() -> dict:
    """Theorems in the Lean project and a `sorry`/`admit` scan (static, cheap)."""
    src = config.LEAN_DIR / "CryoLean"
    theorems: list[dict] = []
    unproved: list[str] = []
    for p in sorted(src.glob("*.lean")):
        text = p.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            s = line.strip()
            if s.startswith("theorem "):
                theorems.append({"name": s.split()[1], "file": f"lean/CryoLean/{p.name}", "line": i})
            if "sorry" in s or s.startswith("admit"):
                if not s.startswith("--") and "sorry`" not in s and "`sorry" not in s:
                    unproved.append(f"{p.name}:{i}")
    return {"theorems": theorems, "unproved_markers": unproved, "lean_binary": str(config.lean_binary_path()),
            "lean_binary_present": lean_binary() is not None, "lean_version": lean_version()}
