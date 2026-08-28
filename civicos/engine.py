from __future__ import annotations
from typing import Any
from civicos.adapters.benefit_calculators import build_calculator_plans
from civicos.connectors.official import source_ref
from civicos.verticals.benefits import analyse_benefits
from civicos.verticals.public_money import analyse_awards, query_public_money_provider
from civicos.verticals.payment_reconciliation import reconcile_awards_and_payments
from civicos.verticals.decision_review import review_decision


def run(vertical: str, payload: Any):
    if vertical == "benefits":
        if not isinstance(payload, dict):
            raise TypeError("Benefits Graph expects a household object")
        result = analyse_benefits(payload)
        calculators = build_calculator_plans(payload)
        existing = {source.source_id for source in result.sources}
        extra_sources = [source_ref(plan.source_id) for plan in calculators if plan.source_id not in existing]
        return result.model_copy(update={
            "calculators": calculators,
            "sources": list(result.sources) + extra_sources,
            "audit": list(result.audit) + [{
                "step": "official_calculator_planning_v5",
                "calculator_count": len(calculators),
                "ready_or_external": sum(1 for plan in calculators if plan.state in {"ready", "official_tool_only", "guidance_only"}),
            }],
        })
    if vertical == "public-money":
        if isinstance(payload, dict) and payload.get("tool"):
            return query_public_money_provider(payload)
        if isinstance(payload, dict) and "awards" in payload and "payments" in payload:
            return reconcile_awards_and_payments(list(payload.get("awards") or []), list(payload.get("payments") or []))
        if not isinstance(payload, list):
            raise TypeError("Public Money Graph expects award records, an awards+payments reconciliation object, or a provider tool query")
        return analyse_awards(payload)
    if vertical == "decision-review":
        if isinstance(payload, dict):
            payload = payload.get("text", "")
        return review_decision(str(payload))
    raise ValueError(f"Unknown CivicOS vertical: {vertical}")
