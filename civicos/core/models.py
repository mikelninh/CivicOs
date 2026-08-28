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

class Claim(BaseModel):
    claim_id: str
    text: str
    status: ClaimStatus = "unresolved"
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str] = []
    counterevidence_ids: list[str] = []

class ActionRecommendation(BaseModel):
    action_id: str
    title: str
    why: str
    official_route: str | None = None
    missing_evidence: list[str] = []
    requires_human_approval: bool = True
    consequence: Literal["informational", "preparatory", "external"] = "preparatory"

class CaseResult(BaseModel):
    case_id: str
    vertical: str
    summary: str
    claims: list[Claim] = []
    sources: list[SourceRef] = []
    actions: list[ActionRecommendation] = []
    uncertainties: list[str] = []
    contradictions: list[str] = []
    audit: list[dict[str, Any]] = []

    @property
    def next_action(self) -> ActionRecommendation | None:
        return self.actions[0] if self.actions else None
