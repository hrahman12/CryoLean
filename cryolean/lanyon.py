"""Lanyon AI integration: certified simulations whose proofs go through CryoLean's Gatekeeper.

Lanyon (lanyon-cli, a standard-library Python client) turns a physics prompt into a specification (/specify),
certifies it with an exported Lean + Rocq proof (/verify), compiles a C99 kernel (/compile), runs it (/simulate)
and saves everything locally (/download):

    <download dir>/<session id>/specification-<sha>.rkt, proof-<sha>.lean, proof_<sha>.v,
                                implementation-<sha>.c, simulation-<sha>/{results,analysis}/
    <save dir>/events.json, ids.json      (the server's event log: proof.certified carries the certificate)

CryoLean's rule: a Lanyon result may be used as evidence with status `certified_simulation` ONLY when
  1. the pinned client (sha256 below) produced it,
  2. the session log holds a `proof.certified` event and no `proof.discrepancy_detected` event,
  3. the exported `proof-*.lean` passes the Gatekeeper (compiles here, no sorry/axiom/native_decide,
     `#print axioms` ⊆ {propext, Classical.choice, Quot.sound}) and is admitted to the rule Registry.
Otherwise the numbers are recorded as `inferred_estimate`, which the Lean checker never treats as a pass or a fail.

Running Lanyon sends the prompt (and a SHA-256 of user@host) to Lanyon's servers on Modal. It is run only when the
user explicitly asks (bridge `run_lanyon_model`, or `python -m cryolean lanyon ...`); nothing runs automatically.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import config, gatekeeper
from .catalog import Catalog

CLIENT = config.ROOT / ".tools" / "lanyon" / "lanyon-cli.pyz"
CLIENT_SHA256 = "34d8c73ff0463dcc68e6fbda03d0e8ab74e91af8d74304542a11c70e9534886d"
RUNS = config.ROOT / "research" / "lanyon" / "runs"
CERTIFIED_WORDS = ("certified", "verified", "valid", "passed", "accepted")


class LanyonUnavailable(RuntimeError):
    pass


def client_status() -> dict:
    if not CLIENT.exists():
        return {"available": False, "path": str(CLIENT), "reason": "client not installed (.tools/lanyon/lanyon-cli.pyz)"}
    digest = hashlib.sha256(CLIENT.read_bytes()).hexdigest()
    return {"available": digest == CLIENT_SHA256, "path": str(CLIENT), "sha256": digest, "pinned_sha256": CLIENT_SHA256,
            "reason": None if digest == CLIENT_SHA256 else "client hash does not match the pinned hash"}


def run(problem: str, instructions: str | None = None, name: str | None = None, timeout: float = 3600) -> dict:
    """Run specify -> verify -> compile -> [simulate] -> download, non-interactively, then import the session."""
    st = client_status()
    if not st["available"]:
        raise LanyonUnavailable(st["reason"])
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = (RUNS / f"{stamp}_{name or 'run'}").resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "problem.txt").write_text(problem, encoding="utf-8")
    args = [sys.executable, "-I", "-u", str(CLIENT), "--specify", "problem.txt", "--verify", "--compile"]
    if instructions:
        (run_dir / "instructions.txt").write_text(instructions, encoding="utf-8")
        args += ["--simulate", "instructions.txt"]
    args += ["--download", "--download-dir", str(run_dir / "sessions"), "--save-dir", str(run_dir / "save")]
    try:
        proc = subprocess.run(args, cwd=run_dir, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=timeout)
    except subprocess.TimeoutExpired:
        raise LanyonUnavailable(f"Lanyon did not finish within {timeout:.0f} s; resume with --session from {run_dir}")
    (run_dir / "run.log").write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8")
    out = {"run_dir": str(run_dir), "exit_code": proc.returncode,
           "exit_meaning": {0: "every stage succeeded", 1: "a stage failed (later stages not run)", 2: "nothing was sent"}
           .get(proc.returncode, "unexpected")}
    return out


def download(run_dir: str | Path, timeout: float = 1800) -> dict:
    """Resume a run's session and save everything it produced (a failed stage skips the run's own --download)."""
    st = client_status()
    if not st["available"]:
        raise LanyonUnavailable(st["reason"])
    run_dir = Path(run_dir).resolve()
    ids = json.loads((run_dir / "save" / "ids.json").read_text(encoding="utf-8"))
    args = [sys.executable, "-I", "-u", str(CLIENT), "--session", str(ids["session_id"]), "--download",
            "--download-dir", str(run_dir / "sessions"), "--save-dir", str(run_dir / "save")]
    proc = subprocess.run(args, cwd=run_dir, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout)
    (run_dir / "download.log").write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8")
    return {"run_dir": str(run_dir), "exit_code": proc.returncode}


def _events(save_dir: Path) -> list[dict]:
    f = save_dir / "events.json"
    if not f.exists():
        return []
    page = json.loads(f.read_text(encoding="utf-8"))
    return page.get("events", []) if isinstance(page, dict) else []


def import_session(catalog: Catalog, run_dir: str | Path) -> dict:
    """Read a finished Lanyon run (save/events.json, save/ids.json, sessions/<id>/...), gate every exported Lean
    proof, and decide whether its results may be used as `certified_simulation` evidence."""
    run_dir = Path(run_dir).resolve()
    save = run_dir / "save"
    ids = json.loads((save / "ids.json").read_text(encoding="utf-8")) if (save / "ids.json").exists() else {}
    events = _events(save)
    certs = [e["payload"] for e in events if e.get("type") == "proof.certified"]
    discrepancies = [e for e in events if e.get("type") == "proof.discrepancy_detected"]
    session_id = ids.get("session_id")
    sess_dirs = [d for d in (run_dir / "sessions").glob("*") if d.is_dir()] if (run_dir / "sessions").exists() else []
    if session_id:
        sess_dirs = [d for d in sess_dirs if d.name == str(session_id)] or sess_dirs
    proofs, sims, gates = [], [], []
    for d in sess_dirs:
        proofs += sorted(d.glob("proof-*.lean"))
        sims += sorted(p for p in d.glob("simulation-*") if p.is_dir())
    for p in proofs:
        src = p.read_text(encoding="utf-8")
        res = gatekeeper.submit(catalog, f"lanyon:{session_id}:{p.name}", src, proposer=f"lanyon:{session_id}")
        gates.append({"file": str(p), "sha256": res["report"]["sha256"], "admitted": res["admitted"],
                      "reason": res["report"].get("reason"), "theorems": res["report"]["theorems"],
                      "registry_rule": (res["entry"] or {}).get("id")})
    cert_ok = [c for c in certs if any(w in str(c.get("status", "")).lower() for w in CERTIFIED_WORDS)]
    admitted = [g for g in gates if g["admitted"]]
    certified = bool(cert_ok) and not discrepancies and bool(admitted)
    why = []
    if not certs:
        why.append("no proof.certified event in the session log")
    elif not cert_ok:
        why.append("certificate status is " + ", ".join(str(c.get("status")) for c in certs))
    if discrepancies:
        why.append(f"{len(discrepancies)} proof.discrepancy_detected event(s)")
    if not proofs:
        why.append("no exported Lean proof was downloaded")
    elif not admitted:
        why.append("the exported Lean proof did not pass the Gatekeeper: " + "; ".join(str(g["reason"]) for g in gates))
    return {"run_dir": str(run_dir), "session_id": session_id, "certificates": certs, "gatekeeper": gates,
            "simulations": [{"dir": str(s), "results": [str(x) for x in sorted((s / "results").rglob("*")) if x.is_file()][:200],
                             "analysis": [str(x) for x in sorted((s / "analysis").rglob("*")) if x.is_file()][:200]}
                            for s in sims],
            "certified": certified,
            "evidence_status": "certified_simulation" if certified else "inferred_estimate",
            "why_not_certified": None if certified else "; ".join(why)}


def capability_record(imported: dict, key: str, value: dict, claim: str, source_url: str | None = None) -> dict:
    """A capability entry (data/cryostats schema) carrying a Lanyon result. Its status is `certified_simulation`
    only when `import_session` said so; otherwise `inferred_estimate` (never a pass or fail in Lean)."""
    status = imported["evidence_status"]
    rec = {"key": key, "install": "installed", "value": value, "evidence_status": status,
           "evidence_ids": [f"lanyon:{imported['session_id']}"],
           "claim": claim, "source_url": source_url}
    if status == "certified_simulation":
        g = next(g for g in imported["gatekeeper"] if g["admitted"])
        rec["certificate"] = {"lanyon_session": imported["session_id"],
                              "certificate_id": next(c.get("certificate_id") for c in imported["certificates"]),
                              "proof_sha256": g["sha256"], "registry_rule": g["registry_rule"]}
    return rec


# ---------------------------------------------------------------------------- Lanyon as a repair proposer
# Lanyon is the AI proposer for repairs: given a failing coupled relation, it specifies and certifies a physics model
# and writes candidate parameter values. Its candidates are HINTS: verifier.suggest sends every one of them through
# the Lean checker on the exact configuration Apply fix will use, and discards anything that is not REQUIREMENTS_MET.
# Because this sends the problem to Lanyon's servers, it runs only when CRYOLEAN_LANYON_PROPOSER=1 is set.
import os

CANDIDATE_FILE = "candidates.json"


def proposer_enabled() -> dict:
    if os.environ.get("CRYOLEAN_LANYON_PROPOSER") != "1":
        return {"enabled": False, "reason": "Lanyon proposer is off (set CRYOLEAN_LANYON_PROPOSER=1 to send repair problems to Lanyon)"}
    st = client_status()
    return {"enabled": st["available"], "reason": st["reason"]}


def repair_problem(exp_doc: dict, cfg_doc: dict, failing: list[dict], adjustable: dict) -> tuple[str, str]:
    """Plain-language repair problem + simulation instructions for Lanyon (numbers are the exact Lean inputs)."""
    rel = "\n".join(f"- {c.get('name') or c.get('id')}: {c.get('explanation')}" for c in failing)
    params = "\n".join(f"- {n}: may {m.get('adjustable')}{' (integer)' if m.get('integer') else ''}" for n, m in adjustable.items()
                       if m.get("adjustable"))
    problem = (f"Cryostat configuration '{cfg_doc.get('name')}' fails these coupled constraints for experiment "
               f"'{exp_doc.get('name') or exp_doc.get('id')}':\n{rel}\n\nAdjustable experiment parameters:\n{params}\n\n"
               "Model the constraint and find values of the adjustable parameters that satisfy it with the smallest change "
               "from the current values. Do not change any equipment specification or requirement.")
    instr = (f"Write {CANDIDATE_FILE} in results/: a JSON list of objects "
             '{"parameter": <name>, "value": "<exact decimal or a/b>", "unit": "<unit symbol>"}, best candidate first.')
    return problem, instr


def propose_repairs(catalog: Catalog, exp_doc: dict, cfg_doc: dict, failing: list[dict], adjustable: dict,
                    timeout: float = 1800) -> dict:
    """Run Lanyon on the repair problem and return its candidates (unverified hints) plus the run's certification."""
    st = proposer_enabled()
    if not st["enabled"]:
        raise LanyonUnavailable(st["reason"])
    problem, instr = repair_problem(exp_doc, cfg_doc, failing, adjustable)
    r = run(problem, instr, name="repair", timeout=timeout)
    imported = import_session(catalog, r["run_dir"])
    cands = []
    for sim in imported["simulations"]:
        for f in sim["results"]:
            if Path(f).name == CANDIDATE_FILE:
                try:
                    raw = json.loads(Path(f).read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                for c in raw if isinstance(raw, list) else []:
                    if isinstance(c, dict) and {"parameter", "value", "unit"} <= set(c) and c["parameter"] in adjustable:
                        cands.append({"parameter": str(c["parameter"]), "value": str(c["value"]), "unit": str(c["unit"])})
    return {"session_id": imported["session_id"], "run_dir": r["run_dir"], "certified": imported["certified"],
            "evidence_status": imported["evidence_status"], "why_not_certified": imported["why_not_certified"],
            "candidates": cands}
