from __future__ import annotations
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, HttpUrl

ClaimStatus = Literal["supported", "disputed", "unresolved"]
SourceState = Literal["verified_route", "verified_snapshot", "live_fetch"]


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
    actions: list[ActionRecommendation] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    freshness: dict[str, Any] = Field(default_factory=dict)
    audit: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def next_action(self) -> ActionRecommendation | None:
        return self.actions[0] if self.actions else None
