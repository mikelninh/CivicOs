from __future__ import annotations
from datetime import timezone
from civicos.connectors.official import SourceError, fetch_official
from civicos.core.evidence_vault import EvidenceVault
from civicos.core.models import CaseResult
from civicos.core.source_evidence import extract_live_facts


def refresh_case_sources(result: CaseResult, *, persist_public_evidence: bool = False) -> CaseResult:
    """Fetch allowlisted sources, create receipts, and extract narrow evidence-linked facts.

    A successful fetch proves the exact bytes CivicOS received. A verified fact is
    stronger: a declared deterministic fact profile was also found in those bytes.
    Neither state proves a whole eligibility decision, legal applicability, or a
    misconduct conclusion.
    """
    vault = EvidenceVault.from_env() if persist_public_evidence else EvidenceVault()
    receipts = list(result.evidence_receipts)
    excerpts = list(result.evidence_excerpts)
    facts = list(result.evidence_facts)
    refreshed: list[str] = []
    failures: list[dict] = []
    updated_sources = []

    if persist_public_evidence and not vault.enabled:
        failures.append({
            "source_id": "evidence-vault",
            "error": "persist_public_evidence=true but CIVICOS_EVIDENCE_DIR is not configured; receipts remain receipt-only",
        })

    for source in result.sources:
        try:
            receipt, body = fetch_official(source.source_id)
            if persist_public_evidence and vault.enabled:
                receipt = vault.store_public_source(receipt, body)
            source_excerpts, source_facts = extract_live_facts(source.source_id, body, receipt.receipt_id)
            receipts.append(receipt)
            excerpts.extend(source_excerpts)
            facts.extend(source_facts)
            refreshed.append(source.source_id)
            updated_sources.append(source.model_copy(update={
                "state": "live_fetch",
                "verified_at": receipt.fetched_at.astimezone(timezone.utc).date().isoformat(),
            }))
        except SourceError as exc:
            failures.append({"source_id": source.source_id, "error": str(exc)})
            updated_sources.append(source)

    # Link only facts whose profile explicitly names the claim they support.
    verified_by_claim: dict[str, list] = {}
    for fact in facts:
        if fact.status == "verified" and fact.claim_id:
            verified_by_claim.setdefault(fact.claim_id, []).append(fact)

    updated_claims = []
    linked_claim_count = 0
    for claim in result.claims:
        supporting = verified_by_claim.get(claim.claim_id, [])
        if not supporting:
            updated_claims.append(claim)
            continue
        linked_claim_count += 1
        evidence_ids = list(dict.fromkeys(claim.evidence_ids + [fact.receipt_id for fact in supporting]))
        details = dict(claim.details)
        details["live_verified_facts"] = [fact.fact_id for fact in supporting]
        updated_claims.append(claim.model_copy(update={"evidence_ids": evidence_ids, "details": details}))

    uncertainties = list(result.uncertainties)
    source_failures = [f for f in failures if f["source_id"] != "evidence-vault"]
    if source_failures:
        uncertainties.append(
            "One or more official sources could not be live-fetched for this run; those sources remain verified routes rather than current evidence."
        )
    if any(f["source_id"] == "evidence-vault" for f in failures):
        uncertainties.append("Public-source persistence was requested but no evidence-vault directory is configured; live receipts were still created in memory.")
    if refreshed and not facts:
        uncertainties.append("Official bytes were fetched, but no declared v0.4 fact profile matched; CivicOS therefore created receipts without upgrading any claim to evidence-linked fact support.")

    return result.model_copy(update={
        "sources": updated_sources,
        "claims": updated_claims,
        "evidence_receipts": receipts,
        "evidence_excerpts": excerpts,
        "evidence_facts": facts,
        "uncertainties": uncertainties,
        "freshness": {
            "requested": True,
            "live_fetch_count": len(refreshed),
            "source_count": len(result.sources),
            "verified_fact_count": sum(f.status == "verified" for f in facts),
            "evidence_linked_claim_count": linked_claim_count,
            "failures": failures,
            "all_sources_live": bool(result.sources) and not source_failures and len(refreshed) == len(result.sources),
        },
        "audit": list(result.audit) + [{
            "step": "live_source_refresh_v4",
            "refreshed": refreshed,
            "verified_facts": [fact.fact_id for fact in facts if fact.status == "verified"],
            "evidence_linked_claims": list(verified_by_claim),
            "failures": failures,
            "persist_public_evidence": persist_public_evidence,
        }],
    })
