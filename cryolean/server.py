"""HTTP API for the hosted CryoLean website (python -m cryolean serve).

The desktop app talks to the same CryoLeanAPI through the PyWebView bridge; a browser on the public web cannot, so this
thin FastAPI layer exposes the bridge methods the website needs. Every verdict still comes from the compiled Lean
checker inside CryoLeanAPI; Z3 output is returned only as suggestions that Lean re-checks. GET / serves the website
(site/index.html) in live mode, so one process is a complete deployment.

    python -m cryolean serve [--host 0.0.0.0] [--port 8000]
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from . import config, lean_runner
from .bridge import CryoLeanAPI

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title="CryoLean", description="Lean 4-verified cryostat compatibility checks", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("CRYOLEAN_CORS", "*").split(","), allow_methods=["GET", "POST"],
                   allow_headers=["*"])
_api: CryoLeanAPI | None = None


def api() -> CryoLeanAPI:
    global _api
    if _api is None:
        from . import db
        dbp, seeds = config.db_path(), list((ROOT / "data").rglob("*.json"))
        if not dbp.exists() or max(p.stat().st_mtime for p in seeds) > dbp.stat().st_mtime:
            db.build_database()            # the JSON seeds changed since the database was built
        _api = CryoLeanAPI()
    return _api


class Check(BaseModel):
    experiment_id: str
    configuration_id: str
    parameters: dict[str, Any] | None = None
    requirement_edits: list[dict[str, Any]] | None = None
    confirmed: bool = False
    suggestions: bool = True


class Find(BaseModel):
    experiment_id: str
    parameters: dict[str, Any] | None = None
    requirement_edits: list[dict[str, Any]] | None = None
    confirmed: bool = False
    max_results: int = 10
    include_hypothetical_options: bool = True


class LanyonAsk(BaseModel):
    question: str
    facts: str = ""


class ApplyFix(BaseModel):
    experiment_id: str
    fix: dict[str, Any]
    parameters: dict[str, Any] | None = None
    requirement_edits: list[dict[str, Any]] | None = None
    confirmed: bool = False


def _env(r: dict) -> JSONResponse:
    """Bridge envelopes are {ok, data | error}; errors keep their code and HTTP 422 so the page can show them."""
    return JSONResponse(r, status_code=200 if r.get("ok") else 422)


@app.get("/api/health")
def health():
    st = api().get_lean_status()
    cat = api()._catalog
    return {"ok": True, "lean": st.get("data"), "lean_source_hash": lean_runner.source_hash(),
            "catalog": {"experiments": len(cat.experiments), "configurations": len(cat.configurations)},
            "database": str(config.db_path())}


@app.post("/api/check")
def check(b: Check):
    """Lean verdict for one exact configuration, then Z3 suggestions (each re-checked by Lean)."""
    return _env(api().check_compatibility(b.experiment_id, b.configuration_id, b.parameters, b.requirement_edits, b.confirmed,
                                          None, b.suggestions))


@app.post("/api/apply-fix")
def apply_fix(b: ApplyFix):
    """Apply a verified fix exactly; Lean re-checks it. apply_fix.confirmed is true only for REQUIREMENTS_MET on the
    same Lean input hash that was verified before the fix was shown."""
    return _env(api().apply_fix(b.experiment_id, b.fix, b.parameters, b.requirement_edits, b.confirmed))


@app.post("/api/lanyon")
def lanyon_ask(b: LanyonAsk):
    """Website chat: Claude answers in plain English; Lanyon builds a certified model when the question asks for one.
    Neither changes a verdict."""
    from . import chat, lanyon
    q, facts = b.question[:2000], b.facts[:6000]
    try:
        data: dict[str, Any] = {"answer": chat.answer(q, facts), "answered_by": "claude", "lanyon": None}
    except chat.ChatUnavailable as e:
        return JSONResponse({"ok": False, "error": {"code": "CHAT_UNAVAILABLE", "message": str(e)}}, status_code=503)
    if chat.wants_model(q):
        try:
            data["lanyon"] = lanyon.ask(q, facts)
        except lanyon.LanyonUnavailable as e:
            data["lanyon"] = {"skipped": str(e)}
    return {"ok": True, "data": data}


@app.get("/api/lanyon/status")
def lanyon_status():
    from . import lanyon
    return {"ok": True, "data": {**lanyon.proposer_enabled(), "client": lanyon.client_status()}}


@app.post("/api/find")
def find(b: Find):
    """Lean decides every catalog configuration; Z3 ranks and proposes options; hypothetical ones re-checked by Lean."""
    return _env(api().find_compatible_equipment(b.experiment_id, b.parameters, b.requirement_edits, b.confirmed,
                                                b.max_results, b.include_hypothetical_options))


@app.get("/api/experiments/{experiment_id}/requirements")
def requirements(experiment_id: str):
    return _env(api().get_experiment_requirements(experiment_id))


@app.get("/api/configurations/{configuration_id}")
def configuration(configuration_id: str):
    return _env(api().get_equipment_details(configuration_id))


@app.get("/api/verdict-card/{result_id}")
def verdict_card(result_id: str):
    return _env(api().verdict_card(result_id))


@app.post("/api/repair-demo")
def repair_demo():
    """The 50-qubit wiring repair loop, run live: Lean rejects, Z3 proposes, Lean re-checks the proposal."""
    a = api()
    first = a.check_compatibility("quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw", None, None, True, None, True)
    if not first.get("ok"):
        return _env(first)
    r = first["data"]
    fixes = (r.get("suggestions") or {}).get("verified_fixes", [])
    steps = {"initial": r, "verified_fixes": fixes, "z3_proposals": fixes, "recheck": None}
    if fixes:
        fx = fixes[0]   # the user "applies" the first verified fix; Lean then checks that exact configuration again
        steps["applied"] = fx
        steps["recheck"] = a.apply_fix("quantum_mxc_wiring_heat_budget", fx, None, None, True).get("data")
    return {"ok": True, "data": steps}


@app.get("/", response_class=HTMLResponse)
def site():
    page = ROOT / "site" / "index.html"
    if not page.exists():
        return HTMLResponse("<p>Build the site first: python scripts/export_site_data.py && python scripts/build_site.py</p>", 404)
    html = page.read_text(encoding="utf-8")
    # live mode: the page calls this server for real Lean checks
    return HTMLResponse('<script>window.CRYOLEAN_API = "";</script>' + html)


def main(argv: list[str] | None = None) -> int:
    import argparse
    import uvicorn
    ap = argparse.ArgumentParser(prog="cryolean serve")
    ap.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    a = ap.parse_args(argv)
    uvicorn.run(app, host=a.host, port=a.port)
    return 0
