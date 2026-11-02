"""HTTP API for the hosted CryoLean website (python -m cryolean serve).

The desktop app talks to the same CryoLeanAPI through the PyWebView bridge; a browser on the public web cannot, so this
thin FastAPI layer exposes the bridge methods the website needs. Every verdict still comes from the compiled Lean
checker inside CryoLeanAPI; Z3 output is returned only as suggestions that Lean re-checks. GET / serves the website
(site/index.html) in live mode, so one process is a complete deployment.

    python -m cryolean serve [--host 0.0.0.0] [--port 8000]
"""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config, lean_runner
from .bridge import CryoLeanAPI

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title="CryoLean", description="Lean 4-verified cryostat compatibility checks", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("CRYOLEAN_CORS", "*").split(","), allow_methods=["GET", "POST"],
                   allow_headers=["*"])
_api: CryoLeanAPI | None = None
_init_lock = threading.Lock()


def api() -> CryoLeanAPI:
    global _api
    if _api is None:
        with _init_lock:
            if _api is None:
                _api = _create_api()
    return _api


def _create_api():
    from . import db
    dbp, seeds = config.db_path(), list((ROOT / "data").rglob("*.json"))
    if not dbp.exists() or max(p.stat().st_mtime for p in seeds) > dbp.stat().st_mtime:
        db.build_database()
    return CryoLeanAPI()


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


class BridgeCall(BaseModel):
    method: str
    args: list[Any] = []
    receipt: str | None = None


WEB_METHODS = frozenset({
    "list_industries", "list_experiments", "list_equipment", "get_experiment_requirements",
    "get_equipment_details", "get_lean_status", "get_research_coverage", "get_industry_coverage",
    "get_verification_details", "check_compatibility", "find_compatible_equipment", "compare_equipment",
    "get_verified_repairs", "apply_verified_repair", "match_experiment", "schedule_campaign",
})


@app.post("/api/bridge")
def bridge(b: BridgeCall):
    from . import http_receipts
    if b.method not in WEB_METHODS or len(b.args) > 8:
        return _env({"ok": False, "error": {"code": "invalid_input", "message": "Unsupported web operation", "verdict": None}})
    a = api()
    result_methods = {"get_verification_details", "get_verified_repairs", "apply_verified_repair"}
    try:
        if b.method == 'check_compatibility' and len(b.args)>5 and b.args[5]:
            raise ValueError('Web checks use documented catalog configurations; inline equipment modifications are not accepted.')
        if b.method == 'compare_equipment' and len(b.args)>1 and len(b.args[1])>20:
            raise ValueError('Compare at most 20 configurations at a time.')
        if b.method in result_methods and b.receipt:
            http_receipts.restore(a, b.args[0], b.receipt)
        # Hosted lexical matching has no external AI dependency.
        result = getattr(a, b.method)(*b.args)
        if result.get("ok"):
            ids = set()
            if b.method in result_methods and b.args:
                ids.add(b.args[0])
            data = result.get("data", {})
            if isinstance(data, dict) and data.get("result_id"):
                ids.add(data["result_id"])
            result["receipts"] = {rid: http_receipts.issue(a, rid) for rid in ids}
        return _env(result)
    except (ValueError, KeyError, TypeError, IndexError) as e:
        return _env({"ok": False, "error": {"code": "invalid_input", "message": str(e), "verdict": None}})


def _env(r: dict) -> JSONResponse:
    """Bridge envelopes are {ok, data | error}; errors keep their code and HTTP 422 so the page can show them."""
    return JSONResponse(r, status_code=200 if r.get("ok") else 422)


@app.get("/api/health")
def health():
    st = api().get_lean_status()
    cat = api()._catalog
    return {"ok": True, "lean": st.get("data"), "lean_source_hash": lean_runner.source_hash(),
            "catalog": {"experiments": len(cat.experiments), "configurations": len(cat.configurations)},
            "transport": "real Lean subprocess and local Z3"}


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
    return _env(api().get_verification_details(result_id))


@app.post("/api/repair-demo")
def repair_demo():
    """The 50-qubit wiring repair loop, run live: Lean rejects, Z3 proposes, Lean re-checks the proposal."""
    a = api()
    first = a.check_compatibility("quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw", None, None, True, None, True)
    if not first.get("ok"):
        return _env(first)
    r = first["data"]
    fixes = a.get_verified_repairs(r["result_id"])
    if not fixes.get("ok"): return _env(fixes)
    found = fixes["data"]["fixes"]
    steps = {"initial": r, "verified_fixes": found, "recheck": None}
    if found:
        applied = a.apply_verified_repair(r["result_id"], found[0]["id"])
        if not applied.get("ok"): return _env(applied)
        steps["applied"] = found[0]["parameters"]
        steps["recheck"] = applied["data"]
    return {"ok": True, "data": steps}


@app.get("/", response_class=HTMLResponse)
def site():
    page = ROOT / "frontend" / "dist" / "index.html"
    if not page.exists():
        return HTMLResponse("<p>Build the frontend first: npm run build</p>", 404)
    html = page.read_text(encoding="utf-8")
    # live mode: the page calls this server for real Lean checks
    return HTMLResponse('<script>window.CRYOLEAN_API = "";</script>' + html)


if (ROOT / "frontend/dist/assets").is_dir():
    app.mount("/assets", StaticFiles(directory=ROOT / "frontend/dist/assets"), name="assets")
if (ROOT / "frontend/public").is_dir():
    app.mount("/coverage", StaticFiles(directory=ROOT / "frontend/public/coverage", check_dir=False), name="coverage")
    app.mount("/research", StaticFiles(directory=ROOT / "frontend/public/research", check_dir=False), name="research")


@app.get('/recordings.json')
def recordings():
    return FileResponse(ROOT/'frontend/public/recordings.json',media_type='application/json')


def main(argv: list[str] | None = None) -> int:
    import argparse
    import uvicorn
    ap = argparse.ArgumentParser(prog="cryolean serve")
    ap.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    a = ap.parse_args(argv)
    uvicorn.run(app, host=a.host, port=a.port)
    return 0
