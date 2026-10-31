"""Research-on-demand pipeline.

When a user asks for an industry or experiment that has no verified profile the
backend cannot answer: it returns NEED_MORE_INFORMATION together with a research
request that records the ten pipeline steps.  Candidate profiles produced by
research (human or AI) are validated and stored under ``data/candidates/``;
they never enter the trusted catalog until ``scripts/promote_candidate.py`` is
run with a reviewer name.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .catalog import Catalog, _read_json, _write_json
from .validation import Report, validate_experiment, validate_configuration, validate_evidence_record

PIPELINE_STEPS = [
    "Search for relevant published experimental methods",
    "Identify the cryogenic equipment used",
    "Retrieve manufacturer documentation and specifications",
    "Extract the experiment's requirements",
    "Record source references and applicable conditions",
    "Validate the extracted information (scripts/validate_sources.py)",
    "Convert the confirmed information into structured profiles (data/candidates/)",
    "Run Z3 configuration search",
    "Use Lean to check proposed configurations",
    "Return a result with evidence and verification details",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ResearchPipeline:
    def __init__(self, catalog: Catalog, requests_dir: Path | None = None, candidates_dir: Path | None = None):
        self.catalog = catalog
        self.requests_dir = Path(requests_dir or config.RESEARCH_REQUESTS_DIR)
        self.candidates_dir = Path(candidates_dir or config.CANDIDATES_DIR)

    # ------------------------------------------------------------ requests
    def create_request(self, industry: str, description: str, matched_profiles: list[dict] | None = None) -> dict:
        rid = "rr_" + uuid.uuid4().hex[:10]
        rec = {
            "id": rid,
            "industry": industry,
            "description": description,
            "created_at": _now(),
            "status": "open",
            "verdict": "NEED_MORE_INFORMATION",
            "explanation": ("No verified experiment profile covers this request. The research pipeline below must be "
                            "completed and its output reviewed before any configuration can be verified."),
            "matched_existing_profiles": matched_profiles or [],
            "steps": [{"n": i + 1, "step": s, "status": "pending"} for i, s in enumerate(PIPELINE_STEPS)],
            "candidate_ids": [],
        }
        _write_json(self.requests_dir / f"{rid}.json", rec)
        return rec

    def list_requests(self) -> list[dict]:
        if not self.requests_dir.exists():
            return []
        return [_read_json(p) for p in sorted(self.requests_dir.glob("rr_*.json"))]

    def get_request(self, rid: str) -> dict | None:
        p = self.requests_dir / f"{rid}.json"
        return _read_json(p) if p.exists() else None

    # ------------------------------------------------------------ candidates
    def submit_candidate(self, kind: str, document: dict, evidence: list[dict], submitted_by: str,
                         request_id: str | None = None) -> dict:
        """Validate and store a candidate experiment/equipment profile. Never trusted automatically."""
        if kind not in ("experiment", "equipment"):
            raise ValueError("kind must be 'experiment' or 'equipment'")
        rep = Report()
        ev_index = dict(self.catalog.evidence)
        for i, rec in enumerate(evidence):
            validate_evidence_record(rec, f"candidate.evidence[{i}]", rep, self.catalog.vocabulary["units"])
            if rec.get("id"):
                ev_index[rec["id"]] = rec
        if kind == "experiment":
            validate_experiment(document, "candidate.experiment", rep, self.catalog.vocabulary, ev_index, self.catalog.vocabulary_proposals)
        else:
            for cfg in document.get("configurations", []):
                validate_configuration(cfg, f"candidate.equipment:{cfg.get('id')}", rep, self.catalog.vocabulary, ev_index, self.catalog.vocabulary_proposals)
            if not document.get("configurations"):
                rep.error("candidate.equipment", "no configurations")
        cid = "cand_" + uuid.uuid4().hex[:10]
        rec = {
            "id": cid,
            "kind": kind,
            "document": document,
            "evidence": evidence,
            "submitted_by": submitted_by,
            "submitted_at": _now(),
            "request_id": request_id,
            "trust": "candidate",
            "validation": {"ok": rep.ok, "errors": [str(i) for i in rep.errors], "warnings": [str(i) for i in rep.warnings]},
            "review_status": "unreviewed",
            "note": "Candidate data is never used for verification until promoted by a reviewer (scripts/promote_candidate.py).",
        }
        _write_json(self.candidates_dir / f"{cid}.json", rec)
        if request_id:
            req = self.get_request(request_id)
            if req:
                req["candidate_ids"].append(cid)
                for s in req["steps"]:
                    if s["n"] <= 7:
                        s["status"] = "done" if rep.ok else "needs_fix"
                _write_json(self.requests_dir / f"{request_id}.json", req)
        return rec

    def list_candidates(self) -> list[dict]:
        if not self.candidates_dir.exists():
            return []
        return [_read_json(p) for p in sorted(self.candidates_dir.glob("cand_*.json"))]

    def get_candidate(self, cid: str) -> dict | None:
        p = self.candidates_dir / f"{cid}.json"
        return _read_json(p) if p.exists() else None

    def promote(self, cid: str, reviewed_by: str) -> dict:
        """Move a reviewed candidate into the trusted catalog. Requires a reviewer; refuses invalid candidates."""
        rec = self.get_candidate(cid)
        if not rec:
            raise ValueError(f"unknown candidate {cid}")
        if not rec["validation"]["ok"]:
            raise ValueError("candidate has validation errors; fix them before promotion: " + "; ".join(rec["validation"]["errors"][:5]))
        if not reviewed_by:
            raise ValueError("a reviewer name is required")
        doc = rec["document"]
        doc["review"] = {"reviewed_by": reviewed_by, "reviewed_at": _now(), "promoted_from": cid, "submitted_by": rec["submitted_by"]}
        data = self.catalog.data_dir
        if rec["evidence"]:
            ev_path = data / "evidence" / f"promoted_{cid}.json"
            _write_json(ev_path, rec["evidence"])
        if rec["kind"] == "experiment":
            target = data / "experiments" / f"{doc['id']}.json"
        else:
            target = data / "cryostats" / f"{doc['id']}.json"
        if target.exists():
            raise ValueError(f"{target.name} already exists in the trusted catalog")
        _write_json(target, doc)
        rec["review_status"] = "promoted"
        rec["promoted_to"] = str(target.relative_to(data))
        _write_json(self.candidates_dir / f"{cid}.json", rec)
        self.catalog.reload()
        return rec
