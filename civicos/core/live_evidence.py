from __future__ import annotations
from datetime import timezone
from civicos.connectors.official import SourceError, fetch_official
from civicos.core.evidence_vault import EvidenceVault
from civicos.core.models import CaseResult


def refresh_case_sources(result: CaseResult, *, persist_public_evidence: bool = False) -> CaseResult:
    """Fetch every allowlisted source used by a case and attach cryptographic receipts.

    Failures are explicit and non-fatal: the original verified-route source remains,
    and the case records that freshness could not be established for that source.
    """
    vault = EvidenceVault() if persist_public_evidence else EvidenceVault(None)
    receipts = list(result.evidence_receipts)
    refreshed = []
    failures = []
    updated_sources = []

    for source in result.sources:
        try:
            receipt, body = fetch_official(source.source_id)
            if persist_public_evidence:
                receipt = vault.store_public_source(receipt, body)
            receipts.append(receipt)
            refreshed.append(source.source_id)
            updated_sources.append(source.model_copy(update={
                "state": "live_fetch",
                "verified_at": receipt.fetched_at.astimezone(timezone.utc).date().isoformat(),
            }))
        except SourceError as exc:
            failures.append({"source_id": source.source_id, "error": str(exc)})
            updated_sources.append(source)

    uncertainties = list(result.uncertainties)
    if failures:
        uncertainties.append(
            "One or more official sources could not be live-fetched for this run; those sources remain verified routes rather than current evidence."
        )

    return result.model_copy(update={
        "sources": updated_sources,
        "evidence_receipts": receipts,
        "uncertainties": uncertainties,
        "freshness": {
            "requested": True,
            "live_fetch_count": len(refreshed),
            "source_count": len(result.sources),
            "failures": failures,
            "all_sources_live": bool(result.sources) and not failures and len(refreshed) == len(result.sources),
        },
        "audit": list(result.audit) + [{
            "step": "live_source_refresh_v3",
            "refreshed": refreshed,
            "failures": failures,
            "persist_public_evidence": persist_public_evidence,
        }],
    })
