#!/usr/bin/env python
"""Static audit of the trusted Lean core with for-all-dev/forensics (https://github.com/for-all-dev/forensics).

Uses the forensics extractor directly (the Windows-friendly route; the Bun app's pipeline.ts assumes Unix paths):

    1. lake build                      in .tools/forensics/extractor   (core-only Lean, toolchain v4.35.0)
    2. lake build CryoLean             in lean/
    3. lake env <extractor> CryoLean   in lean/  ->  docs/forensics/cryolean-forensics.json

It then summarises, per declaration: transitive axioms (sorry / native_decide / non-standard), flags
(partial, opaque, implemented_by, extern, unsafe, ...) and statement smells (trivial conclusions, vacuous
hypotheses, ...), writes docs/forensics/summary.json, and exits 1 if any trusted declaration depends on
sorryAx, a native_decide axiom or any axiom outside {propext, Classical.choice, Quot.sound}.

Prerequisites: clone forensics into .tools/forensics (pinned commit below) and have elan/lake on PATH.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / ".tools" / "forensics"
PINNED_COMMIT = "e5b80ca2590bab3129013cbdf61ec67a32fd9e2c"
OUT = ROOT / "docs" / "forensics"
STANDARD = {"propext", "Classical.choice", "Quot.sound"}


def sh(args, cwd, **kw):
    print("$", " ".join(map(str, args)), f"(in {cwd})", flush=True)
    return subprocess.run(args, cwd=cwd, text=True, encoding="utf-8", errors="replace", **kw)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if not (FX / "extractor").exists():
        print(f"forensics is not checked out at {FX}; run:\n  git clone https://github.com/for-all-dev/forensics {FX}\n"
              f"  git -C {FX} checkout {PINNED_COMMIT}")
        return 2
    if sh(["lake", "build"], FX / "extractor").returncode != 0:
        return 2
    exe = next((p for p in (FX / "extractor" / ".lake" / "build" / "bin").glob("forensics-extract*")), None)
    if exe is None:
        print("extractor binary not found after build")
        return 2
    if sh(["lake", "build", "CryoLean"], ROOT / "lean").returncode != 0:
        return 2
    p = sh(["lake", "env", str(exe), "CryoLean"], ROOT / "lean", capture_output=True)
    if p.returncode != 0:
        print(p.stderr[-3000:])
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "cryolean-forensics.json").write_text(p.stdout, encoding="utf-8")
    data = json.loads(p.stdout)
    decls = data if isinstance(data, list) else data.get("decls") or data.get("declarations") or []
    bad, smells, flags = [], [], []
    for d in decls:
        name = d.get("name")
        axioms = d.get("axioms") or d.get("transitiveAxioms") or []
        names = [a.get("name") if isinstance(a, dict) else a for a in axioms]
        extra = [a for a in names if a and a not in STANDARD]
        if extra:
            bad.append({"decl": name, "axioms": extra})
        if d.get("smells"):
            smells.append({"decl": name, "smells": d["smells"]})
        f = [x for x in (d.get("flags") or []) if x not in ("generated", "rflProof", "decideProof", "noncomputable", "defProp")]
        if f:
            flags.append({"decl": name, "flags": f})
    summary = {"forensics_commit": PINNED_COMMIT, "declarations": len(decls), "nonstandard_axioms": bad,
               "statement_smells": smells, "unsafe_flags": flags, "clean": not bad}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"{len(decls)} declarations; non-standard axioms: {len(bad)}; smells: {len(smells)}; flags: {len(flags)}")
    print(f"wrote {OUT / 'cryolean-forensics.json'} and {OUT / 'summary.json'}")
    if shutil.which("bun"):
        print("Full UI and linters: cd .tools/forensics/app && bun install && bun server.ts ../../../lean")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
