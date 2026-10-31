"""Typed API schemas (Pydantic) so the OpenAPI document is precise for Antigravity."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

Verdict = Literal["ACCEPT", "REJECT", "NEED_MORE_INFORMATION"]
Outcome = Literal["pass", "fail", "unknown", "unsupported"]


class Quantity(BaseModel):
    value: int = Field(description="Integer in the canonical unit (e.g. 1800 mK = 1.8 K)")
    unit: str


class Constraint(BaseModel):
    kind: Literal["point_within", "range_within", "at_least", "at_most", "present", "count_at_least"]
    q: Optional[Quantity] = None
    lo: Optional[Quantity] = None
    hi: Optional[Quantity] = None
    n: Optional[int] = None


class RequirementEdit(BaseModel):
    key: str
    constraint: Optional[Constraint] = None
    mandatory: Optional[bool] = Field(default=None, description="Only honoured for NEW requirements; prepared flags cannot be changed")
    rationale: Optional[str] = None
    remove: bool = False


class InstrumentOverride(BaseModel):
    key: str = Field(description="Vocabulary key of the capability that differs on the user's instrument")
    documented: bool = Field(description="true: a value the user vouches for (used as user_entered evidence). "
                                         "false: an undocumented modification; the capability becomes UNKNOWN.")
    value: Optional[dict[str, Any]] = Field(default=None, description="Capability value in canonical units, e.g. {kind: max, q: {value: 5000, unit: um}}")
    install: Optional[Literal["installed", "optional_not_installed", "unknown"]] = None
    note: str = ""


class VerifyRequest(BaseModel):
    experiment_id: str
    configuration_id: str
    confirmed: bool = Field(default=False, description="The user has reviewed the requirements. Lean never ACCEPTs an unconfirmed profile.")
    requirement_edits: list[RequirementEdit] = Field(default_factory=list)
    instrument_overrides: list[InstrumentOverride] = Field(default_factory=list)


class CompareRequest(BaseModel):
    experiment_id: str
    configuration_ids: list[str]
    confirmed: bool = False
    requirement_edits: list[RequirementEdit] = Field(default_factory=list)


class SearchRequest(BaseModel):
    experiment_id: str
    confirmed: bool = Field(default=True, description="Candidates are Lean-checked with this confirmation flag")
    allow_hypothetical_options: bool = True
    max_candidates: int = 8
    equipment_filter: Optional[list[str]] = None
    requirement_edits: list[RequirementEdit] = Field(default_factory=list)


class MatchRequest(BaseModel):
    text: str = Field(description="Natural-language description of what the user wants to do")
    top_k: int = 3


class ExplainRequest(BaseModel):
    session_id: Optional[str] = None
    result: Optional[dict[str, Any]] = None
    suggest_alternatives: bool = True


class SessionCreate(BaseModel):
    experiment_id: str


class SelectConfiguration(BaseModel):
    configuration_id: str


class IndustryCreate(BaseModel):
    name: str
    description: str = ""
    id: Optional[str] = None


class VocabularyProposal(BaseModel):
    key: str
    shape: Literal["range", "max", "min", "flag", "count"]
    unit: str = ""
    description: str


class ResearchRequestCreate(BaseModel):
    industry: str
    description: str


class CandidateSubmission(BaseModel):
    kind: Literal["experiment", "equipment"]
    document: dict[str, Any]
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    submitted_by: str
    request_id: Optional[str] = None


class CheckOut(BaseModel):
    key: str
    mandatory: bool
    outcome: Outcome
    constraint: dict[str, Any]
    capability: Optional[dict[str, Any]]
    explanation: str
    requirement_origin: Optional[str] = None
    requirement_rationale: Optional[str] = None
    requirement_evidence: list[dict[str, Any]] = []
    capability_evidence: list[dict[str, Any]] = []
    vocabulary: Optional[dict[str, Any]] = None


class VerificationResult(BaseModel):
    verdict: Verdict
    headline: str
    user_message: str
    next_step: str
    summary: Optional[str]
    verified_by_lean: bool
    checker: Optional[str]
    lean_version: Optional[str]
    lean_input_hash: Optional[str]
    configuration_id: str
    equipment_id: str
    experiment_id: str
    experiment_name: Optional[str]
    industry: Optional[str]
    mandatory_requirements: Optional[int]
    missing_information: list[str]
    failed_requirements: list[str]
    checks: list[CheckOut]
    catalog_version: str
    result_token: str
    checked_at: str
    lean_input: dict[str, Any]
    session_id: Optional[str] = None
    state_token: Optional[str] = None
    hypothetical: Optional[bool] = None
    added_options: Optional[list[str]] = None
    smt_assumed_unknown: Optional[list[str]] = None
    instrument_overrides: Optional[list[dict[str, Any]]] = None


class LeanUnavailableOut(BaseModel):
    verdict: None = None
    verified_by_lean: bool = False
    error: str
    detail: str = "The Lean checker is unavailable; no verdict can be produced. There is no fallback verdict."
