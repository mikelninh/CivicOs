from __future__ import annotations
from collections import Counter
from typing import Any
import re
from civicos.adapters.entity_resolution import resolve_pair
from civicos.connectors.official import source_ref
from civicos.core.models import ActionRecommendation, CaseResult, Claim
from civicos.providers.public_money_mcp import PublicMoneyProviderError, call_tool, provider_status


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower().replace("gmbh", "").replace("ag", "").replace("ug", ""))


def _vendor_record(row: dict[str, Any], index: int) -> dict[str, Any]:
    supplied = row.get("vendor_record") or {}
    return {
        "record_id": str(supplied.get("record_id") or row.get("vendor_id") or f"award:{index}"),
        "name": str(supplied.get("name") or row.get("vendor") or ""),
        "address": str(supplied.get("address") or row.get("vendor_address") or ""),
        "domain": str(supplied.get("domain") or row.get("vendor_domain") or ""),
        "directors": list(supplied.get("directors") or row.get("vendor_directors") or []),
        "source": supplied.get("source") or row.get("source") or "supplied_award_record",
    }


def _chain_graph(*, awards: int = 0, same_as: int = 0, review: int = 0, provider_output: bool = False, audit_output: bool = False) -> dict[str, Any]:
    pmm = provider_status()
    budget_status = "provider_output" if provider_output else ("provider_available" if pmm.get("available_in_process") else "provider_contract_only")
    audit_status = "provider_output" if audit_output else ("provider_available" if pmm.get("available_in_process") else "provider_contract_only")
    entity_status = "same_as_resolved" if same_as else ("human_review_needed" if review else ("records_present_no_link" if awards else "missing"))
    stages = [
        {"id":"budget","type":"Budget","status":budget_status},
        {"id":"procurement","type":"Procurement/Award","status":"supplied_records" if awards else "missing","record_count":awards},
        {"id":"entity","type":"LegalEntity","status":entity_status,"same_as_links":same_as,"review_links":review},
        {"id":"payment","type":"Payment","status":"missing","reason":"No recipient/payment-level provider is connected yet."},
        {"id":"audit","type":"AuditContext","status":audit_status},
    ]
    complete = sum(stage["status"] not in {"missing", "provider_contract_only"} for stage in stages)
    return {
        "type":"public_money_chain_v4",
        "stages":stages,
        "edges":[
            {"from":"budget","to":"procurement","relation":"FUNDS_PROGRAMME_OR_AUTHORITY"},
            {"from":"procurement","to":"entity","relation":"AWARDED_TO"},
            {"from":"entity","to":"payment","relation":"SHOULD_RECONCILE_TO"},
            {"from":"payment","to":"audit","relation":"CAN_BE_CHECKED_AGAINST"},
        ],
        "evidence_completeness":{"known_or_available_stages":complete,"total_stages":len(stages),"bottleneck":"payment"},
    }


def query_public_money_provider(query: dict[str, Any]) -> CaseResult:
    tool = str(query.get("tool") or "get_budget")
    kwargs = {k:v for k,v in query.items() if k != "tool"}
    status = provider_status()
    try:
        data = call_tool(tool, **kwargs)
        claims = [Claim(
            claim_id=f"pmm:{tool}",
            text=f"Public Money MCP returned structured output for {tool}.",
            status="supported", confidence=1.0,
            details={"provider":"Public Money MCP", "tool":tool, "result":data, "scope":"budget/audit context; not recipient/payment proof"},
        )]
        audit_output = tool == "lookup_brh_findings"
        graph = _chain_graph(provider_output=not audit_output, audit_output=audit_output)
        action = ActionRecommendation(
            action_id="close:payment-gap", title="Close the recipient/payment evidence gap",
            why="Budget and audit context can orient an investigation, but the decisive accountability link is whether a named legal entity actually received a payment connected to the award/programme.",
            official_route=str(source_ref("bundeshaushalt").url),
            missing_evidence=["recipient/payment-level evidence", "stable legal-entity identifier", "reconciliation to an award/programme"],
            requires_human_approval=False, consequence="informational", priority=96,
            proof=[f"provider tool: {tool}", "structured provider output", "payment stage explicitly unresolved"],
        )
        return CaseResult(
            case_id="public-money-provider", vertical="public-money",
            summary=f"Public Money MCP executed {tool}. CivicOS mapped the result into the money chain and identified payment reconciliation as the key unresolved stage.",
            claims=claims,
            sources=[source_ref("bundeshaushalt"), source_ref("bundesrechnungshof")],
            actions=[action], graph=graph,
            uncertainties=[
                "The current Public Money MCP bundle is not a live recipient/payment database.",
                "Anomaly heuristics are leads, not findings of wrongdoing.",
            ],
            audit=[{"step":"public_money_chain_v4", "tool":tool, "provider_status":status, "bottleneck":"payment"}],
        )
    except PublicMoneyProviderError as exc:
        graph = _chain_graph()
        return CaseResult(
            case_id="public-money-provider", vertical="public-money",
            summary="Public Money MCP provider is not available in this runtime; the money chain remains explicitly incomplete.",
            sources=[source_ref("bundeshaushalt"), source_ref("bundesrechnungshof")], graph=graph,
            actions=[ActionRecommendation(
                action_id="connect:pmm", title="Connect Public Money MCP, then close the payment layer",
                why="CivicOS has the budget/audit provider contract, but the runtime must connect pmm-mcp before those stages can be populated. Payment evidence remains a separate later integration.",
                official_route="https://github.com/mikelninh/pmm-mcp",
                missing_evidence=["running Public Money MCP provider", "recipient/payment-level provider"], requires_human_approval=False,
                consequence="informational", priority=100,
            )],
            uncertainties=[str(exc), "No budget result was invented as a fallback."],
            audit=[{"step":"public_money_chain_v4", "tool":tool, "provider_status":status, "status":"unavailable", "bottleneck":"budget_provider_and_payment"}],
        )


def analyse_awards(awards: list[dict[str, Any]]) -> CaseResult:
    label_counts = Counter(_norm(str(row.get("vendor", ""))) for row in awards if row.get("vendor"))
    repeated_labels = [(vendor, count) for vendor, count in label_counts.most_common() if count > 1]
    records = [_vendor_record(row, i) for i, row in enumerate(awards) if row.get("vendor")]
    identity_links: list[dict[str, Any]] = []
    review_links: list[dict[str, Any]] = []
    for i, left in enumerate(records):
        for right in records[i + 1:]:
            result = resolve_pair(left, right)
            if result.decision == "auto_merge": identity_links.append(result.to_dict())
            elif result.decision == "human_review": review_links.append(result.to_dict())

    claims: list[Claim] = []
    for vendor, count in repeated_labels:
        claims.append(Claim(claim_id=f"pattern:label:{vendor}", text=f"Normalised vendor label '{vendor}' appears in {count} supplied award records.", status="supported", confidence=1.0, details={"evidence_type":"repeated_label","does_not_prove_same_legal_entity":True}))
    for link in identity_links:
        claims.append(Claim(claim_id=f"entity:{link['left_id']}:{link['right_id']}", text=f"Two supplied vendor records meet the SafeTrace auto-merge threshold ({link['score']:.3f}).", status="supported", confidence=link["score"], details={"relation":"SAME_AS","evidence":link["evidence"],"provider":link["provider"]}))
    for link in review_links:
        claims.append(Claim(claim_id=f"entity-review:{link['left_id']}:{link['right_id']}", text=f"Two vendor records may refer to the same entity but require human review ({link['score']:.3f}).", status="unresolved", confidence=link["score"], details={"relation":"REVIEW","evidence":link["evidence"],"provider":link["provider"]}))

    graph = _chain_graph(awards=len(awards), same_as=len(identity_links), review=len(review_links))
    action = ActionRecommendation(
        action_id="close:payment-gap" if awards else "ingest:award-records",
        title="Verify the award, legal entity and actual payment" if awards else "Load award records from the official publication route",
        why="CivicOS can now show exactly where the accountability chain breaks. Supplied award records and entity matching do not establish that a payment was made to that legal entity.",
        official_route=str(source_ref("berlin_procurement_awards").url),
        missing_evidence=["primary award notices","stable organisation identifiers","recipient/payment evidence","reconciliation between award and payment"],
        requires_human_approval=False, consequence="informational", priority=96 if awards else 100,
        proof=[f"{len(repeated_labels)} repeated label pattern(s)", f"{len(identity_links)} SAME_AS link(s)", f"{len(review_links)} review link(s)", "payment stage visibly unresolved"],
    )
    return CaseResult(
        case_id="public-money-graph", vertical="public-money",
        summary=f"Mapped {len(awards)} award records into the public-money chain; entity resolution found {len(identity_links)} SAME_AS link(s), while payment reconciliation remains unresolved.",
        claims=claims,
        sources=[source_ref("berlin_procurement_awards"), source_ref("bundeshaushalt"), source_ref("bundesrechnungshof"), source_ref("unternehmensregister")],
        actions=[action], graph=graph,
        uncertainties=[
            "Repeated vendor labels are not proof of legal-entity identity.",
            "Repeated awards are observable patterns and investigation leads, not findings of corruption or misconduct.",
            "Entity-resolution matches are not findings of wrongdoing.",
            "Recipient-level payment evidence is distinct from budget appropriations, award notices and Public Money MCP's current bundled coverage.",
        ],
        audit=[{"step":"public_money_chain_v4","rows":len(awards),"repeated_labels":len(repeated_labels),"entity_auto_merges":len(identity_links),"entity_review_queue":len(review_links),"entity_provider":"SafeTrace Entity Resolution","public_money_provider":provider_status(),"bottleneck":"payment"}],
    )
