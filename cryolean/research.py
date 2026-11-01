"""Research-on-demand pipeline with a validation gate (SQLite-backed).

An unregistered experiment or industry never gets a verdict on guesses:
``create_request`` records the 12 pipeline steps and answers
NEED_MORE_INFORMATION.  Research output (human- or AI-produced) is submitted as
a candidate, validated, and stored UNTRUSTED.  ``promote`` moves it into the
trusted tables only with a reviewer name and no validation errors.
"""
from __future__ import annotations

import json
import uuid

from . import db
from .catalog import Catalog
from .validation import Report, validate_configuration, validate_evidence_record, validate_experiment

STEPS = [
    "Identify the intended experiment",
    "Search relevant scientific literature",
    "Identify the required cryogenic equipment",
    "Retrieve manufacturer specifications",
    "Extract physical operating requirements",
    "Record supporting sources (URL, title, page, verbatim quote)",
    "Identify missing information",
    "Construct a candidate experiment profile",
    "Validate the extracted requirements (validation gate)",
    "Register the approved profile (reviewer promotion)",
    "Use Z3 to search compatible configurations",
    "Use Lean to check the selected configuration",
]


class ResearchError(ValueError):
    pass


def create_request(catalog: Catalog, industry: str, description: str, matches: list[dict] | None = None) -> dict:
    rid = "rr_" + uuid.uuid4().hex[:10]
    doc = {"id": rid, "industry": industry, "description": description, "created_at": db.now(), "status": "open",
           "verdict": "NEED_MORE_INFORMATION",
           "explanation": ("No validated experiment profile covers this request yet. Complete the research steps; "
                           "nothing becomes trusted until it passes validation and a reviewer approves it."),
           "matched_existing_profiles": matches or [],
           "steps": [{"n": i + 1, "step": s, "status": "pending"} for i, s in enumerate(STEPS)], "candidate_ids": []}
    con = catalog.connect()
    with con:
        con.execute("INSERT INTO research_requests VALUES (?,?,?)", (rid, doc["created_at"], db.dumps(doc)))
    con.close()
    return doc


def list_requests(catalog: Catalog) -> list[dict]:
    con = catalog.connect()
    try:
        return [json.loads(r["doc"]) for r in con.execute("SELECT doc FROM research_requests ORDER BY created_at")]
    finally:
        con.close()


def _update_request(catalog: Catalog, rid: str, fn) -> None:
    con = catalog.connect()
    with con:
        row = con.execute("SELECT doc FROM research_requests WHERE id = ?", (rid,)).fetchone()
        if row:
            doc = json.loads(row["doc"])
            fn(doc)
            con.execute("UPDATE research_requests SET doc = ? WHERE id = ?", (db.dumps(doc), rid))
    con.close()


class _Overlay:
    """Catalog view that also sees the candidate's own evidence (for validation only)."""

    def __init__(self, catalog: Catalog, evidence: list[dict]):
        self.vocabulary = catalog.vocabulary
        self.coupled_models = catalog.coupled_models
        self.evidence = {**catalog.evidence, **{e["id"]: e for e in evidence if e.get("id")}}


def submit_candidate(catalog: Catalog, kind: str, document: dict, evidence: list[dict], submitted_by: str,
                     request_id: str | None = None) -> dict:
    if kind not in ("experiment", "equipment"):
        raise ResearchError("kind must be 'experiment' or 'equipment'")
    rep = Report()
    for i, rec in enumerate(evidence):
        validate_evidence_record(rec, f"candidate.evidence[{i}]", rep)
        if rec.get("id") in catalog.evidence:
            rep.error(f"candidate.evidence[{i}]", f"evidence id {rec['id']!r} already exists in the trusted database (a candidate may not replace it)")
    ov = _Overlay(catalog, evidence)
    if kind == "experiment":
        validate_experiment(ov, document, "candidate.experiment", rep)
        if document.get("id") in catalog.experiments:
            rep.error("candidate.experiment", f"id {document.get('id')!r} already exists in the trusted catalog")
    else:
        if document.get("id") in catalog.equipment:
            rep.error("candidate.equipment", f"equipment id {document.get('id')!r} already exists in the trusted catalog")
        for cfg in document.get("configurations", []):
            if cfg.get("id") in catalog.configurations:
                rep.error("candidate.equipment", f"configuration id {cfg.get('id')!r} already exists in the trusted catalog")
        if not document.get("configurations"):
            rep.error("candidate.equipment", "no configurations")
        for cfg in document.get("configurations", []):
            validate_configuration(ov, cfg, f"candidate.configuration:{cfg.get('id')}", rep)
    cid = "cand_" + uuid.uuid4().hex[:10]
    rec = {"id": cid, "kind": kind, "document": document, "evidence": evidence, "submitted_by": submitted_by,
           "submitted_at": db.now(), "request_id": request_id, "trust": "candidate", "validation": rep.as_dict(),
           "review_status": "unreviewed",
           "note": "Candidates are never used for verification until promoted by a named reviewer."}
    con = catalog.connect()
    with con:
        con.execute("INSERT INTO candidates VALUES (?,?,?,?,?,?,?)",
                    (cid, kind, "unreviewed", submitted_by, rec["submitted_at"], request_id, db.dumps(rec)))
    con.close()
    if request_id:
        def upd(doc):
            doc["candidate_ids"].append(cid)
            for s in doc["steps"]:
                if s["n"] <= 9:
                    s["status"] = "done" if rep.ok else "needs_fix"
        _update_request(catalog, request_id, upd)
    return rec


def get_candidate(catalog: Catalog, cid: str) -> dict | None:
    con = catalog.connect()
    try:
        row = con.execute("SELECT doc FROM candidates WHERE id = ?", (cid,)).fetchone()
        return json.loads(row["doc"]) if row else None
    finally:
        con.close()


def list_candidates(catalog: Catalog) -> list[dict]:
    con = catalog.connect()
    try:
        return [json.loads(r["doc"]) for r in con.execute("SELECT doc FROM candidates ORDER BY submitted_at")]
    finally:
        con.close()


def promote(catalog: Catalog, cid: str, reviewed_by: str) -> dict:
    rec = get_candidate(catalog, cid)
    if not rec:
        raise ResearchError(f"unknown candidate {cid}")
    if not reviewed_by or not reviewed_by.strip():
        raise ResearchError("a reviewer name is required")
    if not rec["validation"]["ok"]:
        raise ResearchError("candidate has validation errors: " + "; ".join(rec["validation"]["errors"][:5]))
    if rec["review_status"] == "promoted":
        raise ResearchError("candidate already promoted")
    doc = dict(rec["document"])
    doc["review"] = {"reviewed_by": reviewed_by, "reviewed_at": db.now(), "promoted_from": cid, "submitted_by": rec["submitted_by"]}
    con = catalog.connect()
    with con:
        for e in rec["evidence"]:
            con.execute("INSERT INTO evidence VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (e["id"], e.get("evidence_status", "unknown"), e.get("source_url"), e.get("document_title"), e.get("location"),
                         e.get("quote"), e.get("doi"), e.get("accessed"), "promoted", db.dumps(e)))
        if rec["kind"] == "experiment":
            con.execute("INSERT INTO experiments VALUES (?,?,?,?,?,?,?)",
                        (doc["id"], doc.get("industry", "unspecified"), doc.get("name"), doc.get("plain_name"), "trusted", "promoted",
                         db.dumps(doc)))
        else:
            db.insert_equipment(con, doc, source="promoted", trust="trusted", replace=False)
        rec["review_status"] = "promoted"
        rec["reviewed_by"] = reviewed_by
        con.execute("UPDATE candidates SET review_status = 'promoted', doc = ? WHERE id = ?", (db.dumps(rec), cid))
    con.close()
    if rec.get("request_id"):
        def upd(d):
            for s in d["steps"]:
                if s["n"] == 10:
                    s["status"] = "done"
            d["status"] = "profile_registered"
        _update_request(catalog, rec["request_id"], upd)
    catalog.reload()
    return rec
