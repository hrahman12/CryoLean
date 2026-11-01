"""Run the compiled Lean checker (local subprocess; no server).

Python never computes a verdict.  If the binary is missing or fails,
``LeanUnavailable`` is raised and callers return ``verdict: None`` — there is no
fallback verdict.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from . import config

VERDICTS = ("REQUIREMENTS_MET", "DOES_NOT_MEET_REQUIREMENTS", "NEED_MORE_INFORMATION")


class LeanUnavailable(RuntimeError):
    """The Lean checker binary cannot be executed."""


class LeanDecodeError(ValueError):
    """Lean rejected the input document (fail-closed decoding)."""


def lean_binary() -> Path | None:
    p = config.lean_binary_path()
    return p if p.exists() else None


def _run(args: list[str], timeout: float | None = None) -> str:
    b = lean_binary()
    if b is None:
        raise LeanUnavailable(f"Lean checker binary not found at {config.lean_binary_path()}; run `lake build` in lean/")
    try:
        proc = subprocess.run([str(b), *args], capture_output=True, text=True, encoding="utf-8",
                              timeout=timeout or config.lean_timeout())
    except (OSError, subprocess.TimeoutExpired) as e:
        raise LeanUnavailable(f"Lean checker failed to run: {e}")
    if proc.returncode not in (0, 2):
        raise LeanUnavailable(f"Lean checker exited with {proc.returncode}: {proc.stderr.strip()[:500]}")
    return proc.stdout


def _with_file(payload, args_prefix: list[str], timeout: float | None = None) -> str:
    fd, path = tempfile.mkstemp(suffix=".json", prefix="cryolean_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False))   # one-shot dumps uses the C encoder; dump(f) does not
        return _run([*args_prefix, path], timeout)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _parse(out: str):
    try:
        return json.loads(out.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as e:
        raise LeanUnavailable(f"Lean checker produced unreadable output: {e}: {out[:300]}")


def check(configuration: dict, experiment: dict) -> dict:
    res = _parse(_with_file({"configuration": configuration, "experiment": experiment}, ["check"]))
    if res.get("error"):
        raise LeanDecodeError(res["error"])
    if res.get("verdict") not in VERDICTS:
        raise LeanUnavailable(f"unexpected verdict {res.get('verdict')!r}")
    return res


def check_candidates(experiment: dict, candidates: list[dict]) -> list[dict]:
    """Uses the proven `checkCandidates` entry point (candidates_accept_sound)."""
    res = _parse(_with_file({"experiment": experiment, "candidates": candidates}, ["check-candidates"],
                            timeout=config.lean_timeout() * max(1, len(candidates) // 8 + 1)))
    if isinstance(res, dict) and res.get("error"):
        raise LeanDecodeError(res["error"])
    return res


def check_schedule(doc: dict) -> dict:
    """Proven `validSchedule` (validSchedule_sound / _bounds / _disjoint / _only_accepted)."""
    res = _parse(_with_file(doc, ["check-schedule"], timeout=config.lean_timeout() * max(1, len(doc.get("experiments", [])))))
    if res.get("error"):
        raise LeanDecodeError(res["error"])
    return res


def run_lean_file(path: Path, timeout: float = 600, cwd: Path | None = None) -> tuple[int, str, str]:
    """`lake env lean <file>` from a Lake project (default: CryoLean's, so CryoLean is importable). Used by the Gatekeeper."""
    try:
        proc = subprocess.run(["lake", "env", "lean", str(path)], cwd=cwd or config.LEAN_DIR, capture_output=True, text=True,
                              encoding="utf-8", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise LeanUnavailable(f"could not run lake: {e}")
    return proc.returncode, proc.stdout, proc.stderr


def source_hash() -> str:
    """SHA-256 of the trusted Lean sources and the compiled checker (the 'source hash' on every verdict card)."""
    import hashlib
    h = hashlib.sha256()
    for p in sorted((config.LEAN_DIR / "CryoLean").glob("*.lean")) + [config.LEAN_DIR / "Main.lean"]:
        h.update(p.name.encode())
        h.update(p.read_bytes())
    b = lean_binary()
    if b:
        h.update(b.read_bytes())
    return h.hexdigest()


AUDIT_FILE = config.LEAN_DIR / "audit-axioms.json"


def axiom_audit() -> dict:
    """Cached `#print axioms` results for the key theorems (written by scripts/audit_axioms.py).
    Marked stale when the Lean sources or binary changed since the audit."""
    if not AUDIT_FILE.exists():
        return {"status": "missing", "theorems": {}}
    data = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
    data["status"] = "current" if data.get("source_hash") == source_hash() else "stale"
    return data


def check_batch(pairs: list[tuple[dict, dict]]) -> list[dict]:
    res = _parse(_with_file([{"configuration": c, "experiment": e} for c, e in pairs], ["check-batch"],
                            timeout=config.lean_timeout() * max(1, len(pairs) // 8 + 1)))
    return res


def version() -> str | None:
    try:
        return _run(["version"], 30).strip() or None
    except LeanUnavailable:
        return None


def selftest() -> tuple[bool, str]:
    try:
        out = _run(["selftest"], 120)
    except LeanUnavailable as e:
        return False, str(e)
    return "all examples produced the expected verdict" in out, out


def theorem_inventory() -> dict:
    """Static inventory of the trusted Lean core (names, files) and a sorry/admit/axiom scan."""
    src = config.LEAN_DIR / "CryoLean"
    theorems, problems = [], []
    for p in sorted(src.glob("*.lean")):
        text = p.read_text(encoding="utf-8")
        code = re.sub(r"/-.*?-/", "", text, flags=re.S)
        for i, line in enumerate(text.splitlines(), 1):
            s = line.strip()
            if s.startswith("theorem "):
                theorems.append({"name": s.split()[1], "file": f"lean/CryoLean/{p.name}", "line": i})
        for pat in (r"\bsorry\b", r"\badmit\b", r"^\s*axiom\b", r"native_decide"):
            if re.search(pat, "\n".join(l.split("--")[0] for l in code.splitlines()), flags=re.M):
                problems.append(f"{p.name}: {pat}")
    return {"theorems": theorems, "count": len(theorems), "unproved_or_unsafe_markers": problems,
            "lean_binary": str(config.lean_binary_path()), "lean_binary_present": lean_binary() is not None}
