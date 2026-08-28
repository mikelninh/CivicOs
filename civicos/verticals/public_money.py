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
            details={"provider":"Public Money MCP", "tool":tool, "result":data},
        )]
        action = ActionRecommendation(
            action_id="inspect:pmm-result", title="Inspect the budget/audit result and identify the next evidence gap",
            why="Public Money MCP provides inspectable budget and audit context, but recipient/payment-level evidence is a separate layer.",
            official_route=str(source_ref("bundeshaushalt").url),
            missing_evidence=["recipient/payment-level evidence when the question concerns who actually received funds"],
            requires_human_approval=False, consequence="informational", priority=90,
            proof=[f"provider tool: {tool}", "structured provider output", "explicit provider freshness limits"],
        )
        return CaseResult(
            case_id="public-money-provider", vertical="public-money",
            summary=f"Public Money MCP executed {tool}; use the result as budget/audit context, not recipient-level proof.",
            claims=claims,
            sources=[source_ref("bundeshaushalt"), source_ref("bundesrechnungshof")],
            actions=[action],
            uncertainties=[
                "The current Public Money MCP bundle is not a live recipient/payment database.",
                "Anomaly heuristics are leads, not findings of wrongdoing.",
            ],
            audit=[{"step":"public_money_mcp_v3", "tool":tool, "provider_status":status}],
        )
    except PublicMoneyProviderError as exc:
        return CaseResult(
            case_id="public-money-provider", vertical="public-money",
            summary="Public Money MCP provider is configured but not available in this runtime.",
            sources=[source_ref("bundeshaushalt"), source_ref("bundesrechnungshof")],
            actions=[ActionRecommendation(
                action_id="connect:pmm", title="Connect the Public Money MCP provider",
                why="CivicOS has the provider contract, but this runtime must install or connect the separate pmm-mcp service before executing its tools.",
                official_route="https://github.com/mikelninh/pmm-mcp",
                missing_evidence=["running Public Money MCP provider"], requires_human_approval=False,
                consequence="informational", priority=100,
            )],
            uncertainties=[str(exc), "No budget result was invented as a fallback."],
            audit=[{"step":"public_money_mcp_v3", "tool":tool, "provider_status":status, "status":"unavailable"}],
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

    action = ActionRecommendation(
        action_id="verify:repeat-awards" if repeated_labels or identity_links or review_links else "ingest:award-records",
        title="Verify the strongest award/entity pattern against primary records" if repeated_labels or identity_links or review_links else "Load award records from the official publication route",
        why="CivicOS separates repeated labels from evidence-backed legal-entity matching. Primary award notices and stable register identifiers remain necessary before drawing conclusions.",
        official_route=str(source_ref("berlin_procurement_awards").url),
        missing_evidence=["primary award notices","stable organisation identifiers","procedure context","recipient/payment evidence"],
        requires_human_approval=False, consequence="informational", priority=88 if awards else 100,
        proof=[f"{len(repeated_labels)} repeated label pattern(s)", f"{len(identity_links)} SAME_AS link(s)", f"{len(review_links)} review link(s)", "Public Money MCP available as budget/audit provider"],
    )
    return CaseResult(
        case_id="public-money-graph", vertical="public-money",
        summary=f"Analysed {len(awards)} award records: {len(repeated_labels)} repeated label pattern(s), {len(identity_links)} SAME_AS link(s), {len(review_links)} review link(s).",
        claims=claims,
        sources=[source_ref("berlin_procurement_awards"), source_ref("bundeshaushalt"), source_ref("bundesrechnungshof"), source_ref("unternehmensregister")],
        actions=[action],
        uncertainties=[
            "Repeated vendor labels are not proof of legal-entity identity.",
            "Entity-resolution matches are not findings of wrongdoing.",
            "Recipient-level payment evidence is distinct from budget appropriations, award notices and Public Money MCP's current bundled coverage.",
        ],
        audit=[{"step":"award_pattern_analysis_v3","rows":len(awards),"repeated_labels":len(repeated_labels),"entity_auto_merges":len(identity_links),"entity_review_queue":len(review_links),"entity_provider":"SafeTrace Entity Resolution","public_money_provider":provider_status()}],
    )
