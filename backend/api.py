"""FastAPI application for the Antigravity frontend.

Run:  uvicorn backend.api:app --reload
Docs: http://127.0.0.1:8000/docs   (OpenAPI JSON at /openapi.json)
"""
from __future__ import annotations

import copy
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from . import config, lean_runner, verifier
from .ai_matching import build_matcher, match_request
from .catalog import Catalog, CatalogError
from .coverage import build_coverage
from .research_pipeline import ResearchPipeline
from .modifications import ModificationError, apply_overrides, describe_overrides
from .schemas import (CandidateSubmission, CompareRequest, ExplainRequest, IndustryCreate, InstrumentOverride, LeanUnavailableOut,
                      MatchRequest, RequirementEdit, ResearchRequestCreate, SearchRequest, SelectConfiguration,
                      SessionCreate, VerificationResult, VerifyRequest, VocabularyProposal)
from .sessions import SessionError, SessionStore, StaleResult
from solver.z3_search import ConfigurationSearch

DESCRIPTION = """
CryoLean answers **"Can this cryostat do my experiment?"** with exactly three verdicts:

| verdict | meaning |
|---|---|
| `ACCEPT` | *Requirements met* — every mandatory requirement is satisfied by documented capabilities and the Lean checker passed. |
| `REJECT` | *Doesn't meet requirements* — a documented limitation conflicts with a mandatory requirement. |
| `NEED_MORE_INFORMATION` | *Need more information* — the evidence does not establish every requirement (unknown, estimate, unit mismatch, unconfirmed). |

Every verdict is produced by the Lean 4 checker (`lean/`), whose soundness is proven in `lean/CryoLean/Soundness.lean`.
Z3 (`solver/`) only proposes candidates; the AI only matches natural language onto prepared experiments.
Industries, equipment, experiments and vocabulary are data and can be registered at runtime.
"""

app = FastAPI(title="CryoLean API", version="0.1.0", description=DESCRIPTION)
app.state.catalog = Catalog()
app.state.sessions = SessionStore()
app.state.pipeline = ResearchPipeline(app.state.catalog)
app.state.matcher = None


def catalog() -> Catalog:
    return app.state.catalog


def matcher():
    if app.state.matcher is None or app.state.matcher.catalog is not catalog():
        app.state.matcher = build_matcher(catalog())
    return app.state.matcher


@app.exception_handler(lean_runner.LeanUnavailable)
async def _lean_unavailable(_: Request, exc: lean_runner.LeanUnavailable):
    return JSONResponse(status_code=503, content=LeanUnavailableOut(error=str(exc)).model_dump())


@app.exception_handler(lean_runner.LeanDecodeError)
async def _lean_decode(_: Request, exc: lean_runner.LeanDecodeError):
    return JSONResponse(status_code=422, content={"verdict": None, "verified_by_lean": False,
                                                  "error": f"Lean rejected the input document: {exc}"})


@app.exception_handler(CatalogError)
async def _catalog_error(_: Request, exc: CatalogError):
    return JSONResponse(status_code=404, content={"error": str(exc)})


@app.exception_handler(StaleResult)
async def _stale(_: Request, exc: StaleResult):
    return JSONResponse(status_code=409, content={"error": str(exc), "stale": True, "verdict": None})


@app.exception_handler(ModificationError)
async def _mod_error(_: Request, exc: ModificationError):
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(SessionError)
async def _session_error(_: Request, exc: SessionError):
    return JSONResponse(status_code=400, content={"error": str(exc)})


# ----------------------------------------------------------------------------- meta
@app.get("/", tags=["meta"])
def root():
    return {"name": "CryoLean API", "docs": "/docs", "openapi": "/openapi.json",
            "verdicts": ["ACCEPT", "REJECT", "NEED_MORE_INFORMATION"], "catalog_version": catalog().version}


@app.get("/health", tags=["meta"])
def health():
    import z3
    inv = lean_runner.proof_inventory()
    return {"status": "ok" if inv["lean_binary_present"] else "degraded",
            "lean_checker_available": inv["lean_binary_present"], "lean_version": inv["lean_version"],
            "lean_theorems": len(inv["theorems"]), "unproved_markers": inv["unproved_markers"],
            "z3_version": z3.get_version_string(), "catalog_version": catalog().version,
            "catalog_loaded_at": catalog().loaded_at, "ai_provider": matcher().name}


@app.get("/lean/proofs", tags=["meta"])
def lean_proofs():
    """Theorem inventory of the trusted Lean core and a `sorry`/`admit` scan."""
    return lean_runner.proof_inventory()


@app.post("/catalog/reload", tags=["meta"])
def reload_catalog():
    catalog().reload()
    app.state.matcher = None
    return {"catalog_version": catalog().version}


# ----------------------------------------------------------------------------- industries
@app.get("/industries", tags=["industries"])
def list_industries(q: str | None = Query(default=None, description="Search industries by name")):
    inds = sorted(catalog().industries.values(), key=lambda i: i["id"])
    if q:
        ql = q.lower()
        inds = [i for i in inds if ql in i["id"] or ql in i.get("name", "").lower() or ql in i.get("description", "").lower()]
    return {"count": len(inds), "industries": inds,
            "note": "Industries are database entries. Any industry can be registered with POST /industries; the Lean checker never reads the label."}


@app.post("/industries", tags=["industries"], status_code=201)
def create_industry(body: IndustryCreate):
    ind = catalog().register_industry(body.name, body.description, body.id)
    app.state.matcher = None
    return ind


@app.get("/industries/{industry_id}", tags=["industries"])
def get_industry(industry_id: str):
    ind = catalog().industries.get(industry_id)
    if not ind:
        raise HTTPException(404, f"unknown industry '{industry_id}'")
    return {**ind, "experiments": [catalog().public_experiment(catalog().experiments[e]) for e in ind.get("experiment_ids", [])]}


# ----------------------------------------------------------------------------- experiments
@app.get("/experiments", tags=["experiments"])
def list_experiments(industry: str | None = None):
    exps = [catalog().public_experiment(e) for e in catalog().experiments.values() if not industry or e.get("industry") == industry]
    return {"count": len(exps), "experiments": exps}


@app.get("/experiments/{experiment_id}", tags=["experiments"])
def get_experiment(experiment_id: str):
    ex = catalog().get_experiment(experiment_id)
    out = catalog().public_experiment(ex)
    out["evidence"] = catalog().evidence_for({eid for r in ex.get("requirements", []) for eid in r.get("evidence_ids", [])}
                                             | {rc.get("evidence_id") for rc in ex.get("reported_conditions", []) if rc.get("evidence_id")})
    return out


# ----------------------------------------------------------------------------- equipment
@app.get("/equipment", tags=["equipment"])
def list_equipment(manufacturer: str | None = None):
    eqs = []
    for eq in catalog().equipment.values():
        if manufacturer and manufacturer.lower() not in eq.get("manufacturer", "").lower():
            continue
        pub = catalog().public_equipment(eq)
        pub["configurations"] = [{"id": c["id"], "name": c.get("name"), "notes": c.get("notes")} for c in eq.get("configurations", [])]
        eqs.append(pub)
    return {"count": len(eqs), "equipment": eqs}


@app.get("/equipment/{equipment_id}", tags=["equipment"])
def get_equipment(equipment_id: str):
    eq = catalog().get_equipment(equipment_id)
    pub = catalog().public_equipment(eq)
    return pub


@app.get("/configurations", tags=["equipment"])
def list_configurations():
    return {"count": len(catalog().configurations),
            "configurations": [{"id": c["id"], "equipment_id": c["equipment_id"], "manufacturer": c.get("manufacturer"),
                                "model": c.get("model"), "name": c.get("name")} for c in catalog().configurations.values()]}


@app.get("/configurations/{configuration_id}", tags=["equipment"])
def get_configuration(configuration_id: str, include_evidence: bool = True):
    cfg = catalog().get_configuration(configuration_id)
    out = catalog().public_configuration(copy.deepcopy(cfg))
    if include_evidence:
        for cap in out.get("capabilities", []):
            cap["evidence"] = catalog().evidence_for(cap.get("evidence_ids", []))
    out["lean_document"] = catalog().lean_configuration(cfg)
    return out


# ----------------------------------------------------------------------------- vocabulary / evidence
@app.get("/vocabulary", tags=["vocabulary"])
def vocabulary():
    return {"units": catalog().vocabulary["units"], "keys": catalog().vocabulary["keys"], "proposed": catalog().vocabulary_proposals}


@app.post("/vocabulary/propose", tags=["vocabulary"], status_code=201)
def propose_key(body: VocabularyProposal):
    try:
        return catalog().propose_vocabulary_key(body.key, body.shape, body.unit, body.description)
    except CatalogError as e:
        raise HTTPException(400, str(e))


@app.get("/evidence", tags=["evidence"])
def list_evidence(ids: str | None = Query(default=None, description="comma-separated ids"), status: str | None = None, limit: int = 200):
    if ids:
        return {"evidence": catalog().evidence_for([i.strip() for i in ids.split(",") if i.strip()])}
    recs = [{k: v for k, v in r.items() if not k.startswith("_")} for r in catalog().evidence.values()
            if not status or r.get("evidence_status") == status]
    return {"count": len(recs), "evidence": recs[:limit]}


@app.get("/evidence/{evidence_id}", tags=["evidence"])
def get_evidence(evidence_id: str):
    rec = catalog().evidence.get(evidence_id)
    if not rec:
        raise HTTPException(404, f"unknown evidence id '{evidence_id}'")
    return {k: v for k, v in rec.items() if not k.startswith("_")}


# ----------------------------------------------------------------------------- verification (stateless)
def _experiment_doc(experiment_id: str, confirmed: bool, edits: list[RequirementEdit]) -> dict:
    ex = catalog().lean_experiment(catalog().get_experiment(experiment_id))
    if edits:
        from .sessions import Session  # reuse the same editing rules
        s = Session.__new__(Session)
        s.experiment = ex
        s.result = None
        s.events = []
        s.edit_requirements([e.model_dump(exclude_none=True) for e in edits])
    ex["confirmed"] = bool(confirmed)
    return ex


@app.post("/verify", tags=["verification"], response_model=VerificationResult,
          responses={503: {"model": LeanUnavailableOut, "description": "Lean checker unavailable: no verdict"}})
def verify(body: VerifyRequest):
    """Check one experiment against one exact configuration. The verdict comes from Lean."""
    ex = _experiment_doc(body.experiment_id, body.confirmed, body.requirement_edits)
    cfg = catalog().lean_configuration(catalog().get_configuration(body.configuration_id))
    ovs = [o.model_dump(exclude_none=True) for o in body.instrument_overrides]
    cfg = apply_overrides(catalog(), cfg, ovs)
    return verifier.verify(catalog(), ex, cfg, extra={"instrument_overrides": describe_overrides(ovs)} if ovs else None)


@app.post("/compare", tags=["verification"],
          responses={503: {"model": LeanUnavailableOut}})
def compare(body: CompareRequest):
    """Same experiment against several configurations (possibly across manufacturers), one Lean verdict each."""
    ex = _experiment_doc(body.experiment_id, body.confirmed, body.requirement_edits)
    results = []
    for cid in body.configuration_ids:
        cfg = catalog().lean_configuration(catalog().get_configuration(cid))
        results.append(verifier.verify(catalog(), copy.deepcopy(ex), cfg))
    return {"experiment_id": body.experiment_id, "results": results}


@app.post("/search", tags=["verification"],
          responses={503: {"model": LeanUnavailableOut}})
def search(body: SearchRequest):
    """Z3 proposes configurations across ALL registered equipment; Lean then checks each candidate.
    Only candidates with a Lean verdict of ACCEPT are listed as `verified_compatible`."""
    ex = _experiment_doc(body.experiment_id, body.confirmed, body.requirement_edits)
    res = ConfigurationSearch(list(catalog().configurations.values())).search(
        ex, allow_hypothetical_options=body.allow_hypothetical_options, max_candidates=body.max_candidates,
        equipment_filter=body.equipment_filter)
    out = res.to_dict()
    verified, other = [], []
    for cand in res.candidates:
        base_id = cand.configuration_id.split("+")[0]
        cfg_doc = cand.configuration_document or catalog().lean_configuration(catalog().get_configuration(base_id))
        if cand.configuration_document:
            cfg_doc = catalog().lean_configuration({**cand.configuration_document, "equipment_id": cand.equipment_id})
        r = verifier.verify(catalog(), copy.deepcopy(ex), cfg_doc,
                            extra={"hypothetical": bool(cand.added_options), "added_options": cand.added_options, "smt_assumed_unknown": cand.assumed_unknown})
        entry = {"candidate": cand.to_dict(), "lean": r}
        entry["candidate"]["verified"] = r["verdict"] == "ACCEPT"
        (verified if r["verdict"] == "ACCEPT" else other).append(entry)
    out["verified_compatible"] = verified
    out["candidates_not_verified"] = other
    out["note"] += " Entries under verified_compatible carry a Lean ACCEPT for the exact document shown in lean_input."
    return out


# ----------------------------------------------------------------------------- AI
@app.post("/ai/match", tags=["ai"])
def ai_match(body: MatchRequest):
    """Map a natural-language request onto prepared experiment profiles (closed set). The user must confirm."""
    return match_request(catalog(), body.text, top_k=body.top_k, matcher=matcher())


@app.post("/ai/explain", tags=["ai"],
          responses={503: {"model": LeanUnavailableOut}})
def ai_explain(body: ExplainRequest):
    """Explain a result in plain language and (optionally) suggest alternatives found by Z3 and checked by Lean.
    The explanation reuses the Lean-generated sentences; nothing is invented."""
    if body.session_id:
        s = app.state.sessions.get(body.session_id)
        result = s.current_result(catalog())
        experiment = copy.deepcopy(s.experiment)
    elif body.result:
        result = body.result
        experiment = result.get("lean_input", {}).get("experiment")
        if experiment is None:
            raise HTTPException(400, "result must contain lean_input.experiment")
    else:
        raise HTTPException(400, "give session_id or result")
    lines = [result.get("summary") or ""]
    for c in result.get("checks", []):
        if c["mandatory"] and c["outcome"] != "pass":
            lines.append(c["explanation"])
    alternatives = []
    if body.suggest_alternatives and result.get("verdict") != "ACCEPT":
        res = ConfigurationSearch(list(catalog().configurations.values())).search(experiment, allow_hypothetical_options=True, max_candidates=5)
        for cand in res.candidates:
            base_id = cand.configuration_id.split("+")[0]
            if cand.configuration_document:
                cfg_doc = catalog().lean_configuration({**cand.configuration_document, "equipment_id": cand.equipment_id})
            else:
                cfg_doc = catalog().lean_configuration(catalog().get_configuration(base_id))
            r = verifier.verify(catalog(), copy.deepcopy(experiment), cfg_doc,
                                extra={"hypothetical": bool(cand.added_options), "added_options": cand.added_options, "smt_assumed_unknown": cand.assumed_unknown})
            alternatives.append({"configuration_id": cand.configuration_id, "equipment_id": cand.equipment_id,
                                 "kind": cand.kind, "added_options": cand.added_options, "lean_verdict": r["verdict"],
                                 "user_message": r["user_message"], "verified": r["verdict"] == "ACCEPT"})
    return {"verdict": result.get("verdict"), "explanation": [l for l in lines if l], "alternatives": alternatives,
            "note": "Alternatives were proposed by Z3 and individually checked by Lean; only verified=true entries are compatible."}


# ----------------------------------------------------------------------------- sessions
@app.post("/sessions", tags=["sessions"], status_code=201)
def create_session(body: SessionCreate):
    s = app.state.sessions.create(catalog(), body.experiment_id)
    return s.summary(catalog())


@app.get("/sessions/{session_id}", tags=["sessions"])
def get_session(session_id: str):
    return app.state.sessions.get(session_id).summary(catalog())


@app.patch("/sessions/{session_id}/requirements", tags=["sessions"])
def edit_requirements(session_id: str, edits: list[RequirementEdit]):
    s = app.state.sessions.get(session_id)
    s.edit_requirements([e.model_dump(exclude_none=True) for e in edits])
    return s.summary(catalog())


@app.post("/sessions/{session_id}/confirm", tags=["sessions"])
def confirm(session_id: str):
    s = app.state.sessions.get(session_id)
    s.confirm()
    return s.summary(catalog())


@app.put("/sessions/{session_id}/instrument-overrides", tags=["sessions"])
def set_overrides(session_id: str, overrides: list[InstrumentOverride]):
    """Describe how the user's instrument differs from the catalog configuration (invalidates the result).
    Undocumented modifications make the affected capability UNKNOWN."""
    s = app.state.sessions.get(session_id)
    s.set_overrides(catalog(), [o.model_dump(exclude_none=True) for o in overrides])
    return s.summary(catalog())


@app.post("/sessions/{session_id}/select-configuration", tags=["sessions"])
def select_configuration(session_id: str, body: SelectConfiguration):
    """Switch cryostat: keeps the experiment, clears any previous result."""
    s = app.state.sessions.get(session_id)
    s.select_configuration(catalog(), body.configuration_id)
    return s.summary(catalog())


@app.post("/sessions/{session_id}/verify", tags=["sessions"], response_model=VerificationResult,
          responses={503: {"model": LeanUnavailableOut}})
def session_verify(session_id: str):
    s = app.state.sessions.get(session_id)
    return s.verify(catalog())


@app.get("/sessions/{session_id}/result", tags=["sessions"], response_model=VerificationResult,
         responses={409: {"description": "No current result (stale or never checked)"}})
def session_result(session_id: str):
    s = app.state.sessions.get(session_id)
    return s.current_result(catalog())


# ----------------------------------------------------------------------------- research pipeline
@app.post("/research/requests", tags=["research"], status_code=201)
def create_research_request(body: ResearchRequestCreate):
    """Register a research request for an industry/experiment without a verified profile.
    Always answers NEED_MORE_INFORMATION; lists existing profiles that may match."""
    m = match_request(catalog(), body.description, top_k=3, matcher=matcher())
    if body.industry not in catalog().industries:
        catalog().register_industry(body.industry.replace("_", " ").title(), industry_id=body.industry)
    return app.state.pipeline.create_request(body.industry, body.description, m["matches"])


@app.get("/research/requests", tags=["research"])
def list_research_requests():
    return {"requests": app.state.pipeline.list_requests()}


@app.post("/research/candidates", tags=["research"], status_code=201)
def submit_candidate(body: CandidateSubmission):
    """Submit a research candidate (experiment or equipment profile). It is validated and stored as untrusted."""
    return app.state.pipeline.submit_candidate(body.kind, body.document, body.evidence, body.submitted_by, body.request_id)


@app.get("/research/candidates", tags=["research"])
def list_candidates():
    return {"candidates": app.state.pipeline.list_candidates()}


# ----------------------------------------------------------------------------- coverage
@app.get("/coverage", tags=["coverage"])
def coverage():
    return build_coverage(catalog())
