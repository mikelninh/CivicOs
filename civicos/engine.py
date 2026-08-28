from __future__ import annotations
from typing import Any
from civicos.verticals.benefits import analyse_benefits
from civicos.verticals.public_money import analyse_awards, query_public_money_provider
from civicos.verticals.decision_review import review_decision


def run(vertical: str, payload: Any):
    if vertical == "benefits":
        if not isinstance(payload, dict):
            raise TypeError("Benefits Graph expects a household object")
        return analyse_benefits(payload)
    if vertical == "public-money":
        if isinstance(payload, dict) and payload.get("tool"):
            return query_public_money_provider(payload)
        if not isinstance(payload, list):
            raise TypeError("Public Money Graph expects award records or a provider tool query")
        return analyse_awards(payload)
    if vertical == "decision-review":
        if isinstance(payload, dict):
            payload = payload.get("text", "")
        return review_decision(str(payload))
    raise ValueError(f"Unknown CivicOS vertical: {vertical}")
