from __future__ import annotations
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, HttpUrl

ClaimStatus = Literal["supported", "disputed", "unresolved"]
SourceState = Literal["verified_route", "verified_snapshot", "live_fetch"]
FactStatus = Literal["verified", "not_found"]
ChangeState = Literal["unchanged", "content_changed", "fact_changed", "fact_removed", "fact_added"]
CalculatorState = Literal["ready", "missing_inputs", "official_tool_only", "guidance_only", "temporarily_unavailable"]


class SourceRef(BaseModel):
    source_id: str
    title: str
    publisher: str
    url: HttpUrl
    state: SourceState = "verified_route"
    verified_at: str


class EvidenceReceipt(BaseModel):
    receipt_id: str
    source_id: str
    fetched_at: datetime
    sha256: str
    bytes_read: int
    content_type: str = ""
    status_code: int = 200
    storage_state: Literal["receipt_only", "stored"] = "receipt_only"
    storage_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceExcerpt(BaseModel):
    excerpt_id: str
    receipt_id: str
    source_id: str
    text: str
    locator: str = "normalized_text_window"
    extraction_method: str = "deterministic_pattern"


class EvidenceFact(BaseModel):
    fact_id: str
    claim_id: str | None = None
    source_id: str
    receipt_id: str
    label: str
    value: Any = None
    status: FactStatus = "verified"
    excerpt_id: str | None = None
    extraction_method: str = "deterministic_pattern"
    details: dict[str, Any] = Field(default_factory=dict)


class SourceChangeImpact(BaseModel):
    source_id: str
    state: ChangeState
    previous_sha256: str | None = None
    current_sha256: str
    added_fact_ids: list[str] = Field(default_factory=list)
    removed_fact_ids: list[str] = Field(default_factory=list)
    changed_fact_ids: list[str] = Field(default_factory=list)
    affected_claim_ids: list[str] = Field(default_factory=list)
    affected_golden_case_ids: list[str] = Field(default_factory=list)
    regression_fixture: dict[str, Any] = Field(default_factory=dict)


class CalculatorPlan(BaseModel):
    benefit: str
    tool_name: str
    official_route: str
    state: CalculatorState
    supplied_inputs: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    result_scope: str
    note: str = ""
    deterministic_preview: dict[str, Any] = Field(default_factory=dict)


class Claim(BaseModel):
    claim_id: str
    text: str
    status: ClaimStatus = "unresolved"
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str] = Field(default_factory=list)
    counterevidence_ids: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class ActionRecommendation(BaseModel):
    action_id: str
    title: str
    why: str
    official_route: str | None = None
    missing_evidence: list[str] = Field(default_factory=list)
    requires_human_approval: bool = True
    consequence: Literal["informational", "preparatory", "external"] = "preparatory"
    priority: int = Field(default=50, ge=0, le=100)
    estimated_support: str | None = None
    proof: list[str] = Field(default_factory=list)


class CaseResult(BaseModel):
    case_id: str
    vertical: str
    summary: str
    claims: list[Claim] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)
    evidence_receipts: list[EvidenceReceipt] = Field(default_factory=list)
    evidence_excerpts: list[EvidenceExcerpt] = Field(default_factory=list)
    evidence_facts: list[EvidenceFact] = Field(default_factory=list)
    source_changes: list[SourceChangeImpact] = Field(default_factory=list)
    calculators: list[CalculatorPlan] = Field(default_factory=list)
    actions: list[ActionRecommendation] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    freshness: dict[str, Any] = Field(default_factory=dict)
    graph: dict[str, Any] = Field(default_factory=dict)
    audit: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def next_action(self) -> ActionRecommendation | None:
        return self.actions[0] if self.actions else None
