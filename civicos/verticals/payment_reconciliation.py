from __future__ import annotations
from typing import Any
from civicos.adapters.entity_resolution import resolve_pair
from civicos.connectors.official import source_ref
from civicos.core.models import ActionRecommendation, CaseResult, Claim


def _record(data: dict[str, Any], fallback_id: str, name_key: str) -> dict[str, Any]:
    supplied = data.get("vendor_record") or data.get("recipient_record") or {}
    return {
        "record_id": str(supplied.get("record_id") or data.get("vendor_id") or data.get("recipient_id") or fallback_id),
        "name": str(supplied.get("name") or data.get(name_key) or ""),
        "address": str(supplied.get("address") or data.get("address") or ""),
        "domain": str(supplied.get("domain") or data.get("domain") or ""),
        "directors": list(supplied.get("directors") or data.get("directors") or []),
        "source": supplied.get("source") or data.get("source") or "supplied_record",
    }


def reconcile_awards_and_payments(awards: list[dict[str, Any]], payments: list[dict[str, Any]]) -> CaseResult:
    """Reconcile supplied payment evidence to supplied awards conservatively.

    A confirmed reconciliation requires both an explicit award/procedure reference
    match and a SafeTrace SAME_AS entity decision. Anything weaker is review-only.
    This proves a supplied payment record links to a supplied award; it does not
    prove legality, performance, value-for-money, or absence/presence of misconduct.
    """
    confirmed: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []
    unmatched: list[str] = []

    for p_idx, payment in enumerate(payments):
        p_id = str(payment.get("payment_id") or f"payment:{p_idx}")
        recipient = _record(payment, f"recipient:{p_idx}", "recipient")
        candidates = []
        for a_idx, award in enumerate(awards):
            a_id = str(award.get("award_id") or award.get("procedure_id") or f"award:{a_idx}")
            vendor = _record(award, f"vendor:{a_idx}", "vendor")
            entity = resolve_pair(vendor, recipient)
            ref_match = bool(
                payment.get("award_id") and award.get("award_id") and str(payment.get("award_id")) == str(award.get("award_id"))
            ) or bool(
                payment.get("procedure_id") and award.get("procedure_id") and str(payment.get("procedure_id")) == str(award.get("procedure_id"))
            )
            amount = payment.get("amount_eur")
            award_value = award.get("value_eur")
            amount_within_award = isinstance(amount, (int, float)) and isinstance(award_value, (int, float)) and 0 <= float(amount) <= float(award_value)
            candidates.append({
                "payment_id": p_id,
                "award_id": a_id,
                "entity_decision": entity.decision,
                "entity_score": entity.score,
                "entity_evidence": entity.evidence,
                "reference_match": ref_match,
                "amount_within_award_value": amount_within_award,
                "amount_eur": amount,
                "award_value_eur": award_value,
            })

        strong = [c for c in candidates if c["reference_match"] and c["entity_decision"] == "auto_merge"]
        if len(strong) == 1:
            confirmed.append(strong[0])
        else:
            plausible = [c for c in candidates if c["reference_match"] or c["entity_decision"] in {"auto_merge", "human_review"}]
            if plausible:
                best = sorted(plausible, key=lambda c: (c["reference_match"], c["entity_score"]), reverse=True)[0]
                review.append(best)
            else:
                unmatched.append(p_id)

    claims = [
        Claim(
            claim_id=f"payment-reconciliation:{row['payment_id']}:{row['award_id']}",
            text=f"Supplied payment {row['payment_id']} reconciles to supplied award {row['award_id']} using both reference identity and SafeTrace legal-entity matching.",
            status="supported", confidence=min(1.0, float(row["entity_score"])),
            details={**row, "scope":"record-to-record reconciliation only; not a finding about legality or performance"},
        ) for row in confirmed
    ]
    claims += [
        Claim(
            claim_id=f"payment-review:{row['payment_id']}:{row['award_id']}",
            text=f"Supplied payment {row['payment_id']} has a plausible award link but requires human review.",
            status="unresolved", confidence=min(0.89, float(row["entity_score"])), details=row,
        ) for row in review
    ]

    payment_status = "reconciled_records" if confirmed else ("human_review_needed" if review else "unmatched")
    graph = {
        "type":"public_money_chain_v5",
        "stages":[
            {"id":"procurement","type":"Procurement/Award","status":"supplied_records","record_count":len(awards)},
            {"id":"entity","type":"LegalEntity","status":"resolved_or_reviewed","confirmed_links":len(confirmed),"review_links":len(review)},
            {"id":"payment","type":"Payment","status":payment_status,"record_count":len(payments),"confirmed_reconciliations":len(confirmed),"review_reconciliations":len(review),"unmatched":len(unmatched)},
        ],
        "edges":[{"from":"procurement","to":"entity","relation":"AWARDED_TO"},{"from":"entity","to":"payment","relation":"RECONCILED_TO"}],
        "reconciliations":{"confirmed":confirmed,"review":review,"unmatched_payment_ids":unmatched},
    }

    if review:
        title = "Review ambiguous award/payment links"
        priority = 98
    elif unmatched:
        title = "Find the missing award or stable recipient identifier"
        priority = 96
    else:
        title = "Verify payment source provenance and continue to audit context"
        priority = 90

    return CaseResult(
        case_id="public-money-payment-reconciliation", vertical="public-money",
        summary=f"Reconciled {len(payments)} supplied payment record(s): {len(confirmed)} confirmed record links, {len(review)} review link(s), {len(unmatched)} unmatched.",
        claims=claims,
        sources=[source_ref("berlin_procurement_awards"), source_ref("unternehmensregister"), source_ref("bundesrechnungshof")],
        actions=[ActionRecommendation(
            action_id="review:payment-reconciliation", title=title,
            why="A payment closes a major accountability gap only when its award reference and legal recipient identity can be supported independently. Ambiguity stays visible instead of being auto-joined.",
            missing_evidence=["primary payment source/provenance"] + (["stable award/procedure reference or recipient identifier"] if review or unmatched else []),
            requires_human_approval=False, consequence="informational", priority=priority,
            proof=[f"{len(confirmed)} confirmed reference+entity reconciliation(s)", f"{len(review)} ambiguous link(s)", f"{len(unmatched)} unmatched payment(s)"],
        )],
        graph=graph,
        uncertainties=[
            "This endpoint reconciles supplied records; it does not yet fetch a public payment ledger itself.",
            "A reconciled payment does not prove that the procurement, payment, or underlying conduct was lawful or unlawful.",
            "Amounts are supporting context only; equality or proximity of amounts is never sufficient for an automatic match."
        ],
        audit=[{"step":"award_payment_reconciliation_v5","awards":len(awards),"payments":len(payments),"confirmed":len(confirmed),"review":len(review),"unmatched":len(unmatched)}],
    )
