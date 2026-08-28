from __future__ import annotations
from datetime import datetime, timezone
import hashlib
from .models import EvidenceReceipt, Claim

def make_receipt(source_id: str, body: bytes, *, content_type: str = "", status_code: int = 200) -> EvidenceReceipt:
    digest = hashlib.sha256(body).hexdigest()
    return EvidenceReceipt(
        receipt_id=f"{source_id}:{digest[:16]}",
        source_id=source_id,
        fetched_at=datetime.now(timezone.utc),
        sha256=digest,
        bytes_read=len(body),
        content_type=content_type,
        status_code=status_code,
    )

def find_contradictions(claims: list[Claim]) -> list[str]:
    """Conservative placeholder: contradictions must be explicit, never inferred from mere difference."""
    disputed = [c for c in claims if c.status == "disputed"]
    return [f"{c.claim_id}: {c.text}" for c in disputed]
