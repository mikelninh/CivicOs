from __future__ import annotations
from typing import Any

from civicos.connectors.official import source_ref
from civicos.core.models import ActionRecommendation, CaseResult, Claim


def run_golden_scenario(case_id: str, payload: dict[str, Any]) -> CaseResult:
    """Execute a bounded, data-declared golden scenario.

    This runtime exists to make the whole 12-case product/safety contract executable.
    It is intentionally *not* a general domain engine and must never be presented as
    one. Each fixture declares its source routes, claims, uncertainty and next action.
    The three flagship verticals (Benefits, Public Money, Decision Review) remain the
    deeper product implementations.
    """
    sources = [source_ref(source_id) for source_id in payload.get("source_ids", [])]
    claims = [Claim.model_validate(item) for item in payload.get("claims", [])]
    action = ActionRecommendation.model_validate(payload["action"])
    uncertainties = list(payload.get("uncertainties", []))
    if not uncertainties:
        uncertainties = ["This is a bounded golden-case scenario, not a general domain decision engine."]

    return CaseResult(
        case_id=case_id,
        vertical=str(payload.get("domain") or "golden-scenario"),
        summary=str(payload.get("summary") or f"Executed bounded golden scenario {case_id}."),
        claims=claims,
        sources=sources,
        actions=[action],
        uncertainties=uncertainties,
        graph={
            "type": "bounded_golden_scenario_v1",
            "case_id": case_id,
            "source_ids": [source.source_id for source in sources],
            "provider_contracts": list(payload.get("provider_contracts", [])),
            "maturity": "golden_case_contract_not_general_domain_engine",
        },
        audit=[{
            "step": "bounded_golden_scenario_v1",
            "case_id": case_id,
            "source_count": len(sources),
            "claim_count": len(claims),
            "provider_contracts": list(payload.get("provider_contracts", [])),
        }],
    )
