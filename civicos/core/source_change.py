from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable
from civicos.core.models import EvidenceFact, SourceChangeImpact

ROOT = Path(__file__).resolve().parents[2]
IMPACT_MAP = json.loads((ROOT / "data" / "source_impact_map.json").read_text(encoding="utf-8"))


def _fact_map(facts: Iterable[EvidenceFact]) -> dict[str, EvidenceFact]:
    return {fact.fact_id: fact for fact in facts}


def evaluate_source_change(
    source_id: str,
    *,
    previous_sha256: str | None,
    current_sha256: str,
    previous_facts: list[EvidenceFact] | None = None,
    current_facts: list[EvidenceFact] | None = None,
) -> SourceChangeImpact:
    previous_facts = previous_facts or []
    current_facts = current_facts or []
    before = _fact_map(previous_facts)
    after = _fact_map(current_facts)

    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(
        fact_id for fact_id in set(before) & set(after)
        if before[fact_id].value != after[fact_id].value
    )

    if previous_sha256 == current_sha256 and not added and not removed and not changed:
        state = "unchanged"
    elif removed:
        state = "fact_removed"
    elif changed:
        state = "fact_changed"
    elif added:
        state = "fact_added"
    else:
        state = "content_changed"

    mapping = IMPACT_MAP.get("sources", {}).get(source_id, {})
    affected_claims = sorted(set(mapping.get("claim_ids", []))) if state != "unchanged" else []
    affected_cases = sorted(set(mapping.get("golden_case_ids", []))) if state != "unchanged" else []
    fixture = {
        "fixture_version": "0.5.0",
        "source_id": source_id,
        "change_state": state,
        "expected": {
            "recheck_claim_ids": affected_claims,
            "rerun_golden_case_ids": affected_cases,
            "human_review_required": bool(removed or changed),
        },
        "fact_delta": {"added": added, "removed": removed, "changed": changed},
    }

    return SourceChangeImpact(
        source_id=source_id,
        state=state,
        previous_sha256=previous_sha256,
        current_sha256=current_sha256,
        added_fact_ids=added,
        removed_fact_ids=removed,
        changed_fact_ids=changed,
        affected_claim_ids=affected_claims,
        affected_golden_case_ids=affected_cases,
        regression_fixture=fixture,
    )
