from __future__ import annotations
from typing import Any
from civicos.verticals.benefits import analyse_benefits
from civicos.verticals.public_money import analyse_awards
from civicos.verticals.decision_review import review_decision

def run(vertical: str, payload: Any):
    if vertical == "benefits": return analyse_benefits(payload)
    if vertical == "public-money": return analyse_awards(payload)
    if vertical == "decision-review":
        if isinstance(payload, dict): payload = payload.get("text", "")
        return review_decision(str(payload))
    raise ValueError(f"Unknown CivicOS vertical: {vertical}")
