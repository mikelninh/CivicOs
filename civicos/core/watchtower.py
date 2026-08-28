from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from civicos.core.golden_scenarios import run_golden_scenario
from civicos.core.models import GoldenCaseReplay, SourceChangeImpact, WatchtowerReport
from civicos.engine import run
from civicos.providers.judge_mcp import build_judge_request, provider_status as judge_status

ROOT = Path(__file__).resolve().parents[2]
REPLAY_DATA = json.loads((ROOT / "data" / "golden_replay_fixtures.json").read_text(encoding="utf-8"))
REPLAY_FIXTURES = REPLAY_DATA["fixtures"]


def _deterministic_checks(result) -> dict[str, bool]:
    return {
        "has_sources": bool(result.sources),
        "has_next_action": bool(result.actions),
        "uncertainty_visible": bool(result.uncertainties),
        "claim_ids_unique": len({claim.claim_id for claim in result.claims}) == len(result.claims),
        "external_actions_require_approval": all(
            action.requires_human_approval
            for action in result.actions
            if action.consequence == "external"
        ),
        "audit_visible": bool(result.audit),
    }


def replay_golden_case(case_id: str) -> GoldenCaseReplay:
    fixture = REPLAY_FIXTURES.get(case_id)
    if not fixture:
        return GoldenCaseReplay(
            case_id=case_id,
            status="blocked",
            note="No executable golden-case fixture exists. Watchtower refuses to fake a replay result.",
            judge_request={},
        )

    runner = fixture.get("runner", "engine")
    maturity = fixture.get("maturity", "unknown")
    try:
        if runner == "scenario":
            result = run_golden_scenario(case_id, fixture["payload"])
            vertical = result.vertical
        else:
            vertical = fixture["vertical"]
            result = run(vertical, fixture["payload"])
    except Exception as exc:
        return GoldenCaseReplay(
            case_id=case_id,
            vertical=fixture.get("vertical") or fixture.get("domain"),
            status="failed",
            result_summary=f"Replay raised {type(exc).__name__}: {exc}",
            deterministic_checks={},
            failed_checks=["execution"],
            judge_request={},
            note=f"maturity={maturity}; execution failed; do not publish an update.",
        )

    checks = _deterministic_checks(result)
    failed = [name for name, passed in checks.items() if not passed]
    status = "passed" if not failed else "failed"
    return GoldenCaseReplay(
        case_id=case_id,
        vertical=vertical,
        status=status,
        result_summary=result.summary,
        deterministic_checks=checks,
        failed_checks=failed,
        judge_request=build_judge_request(result),
        note=(
            f"maturity={maturity}; deterministic CivicOS contract passed; Judge MCP request is prepared as an optional second quality gate."
            if status == "passed"
            else f"maturity={maturity}; deterministic contract failed; do not publish an update."
        ),
    )


def replay_all_golden_cases() -> list[GoldenCaseReplay]:
    return [replay_golden_case(case_id) for case_id in sorted(REPLAY_FIXTURES)]


def evaluate_watchtower(impact: SourceChangeImpact, *, monitor_metadata: dict[str, Any] | None = None) -> WatchtowerReport:
    """Turn source change impact into a noise-suppressed replay/alert decision."""
    semantic = bool(impact.added_fact_ids or impact.removed_fact_ids or impact.changed_fact_ids)
    provider_chain = [
        "mikelninh/citizen-agents (monitor/event provider)",
        "CivicOS source receipt + fact-delta engine",
        "CivicOS golden-case deterministic replay",
        "mikelninh/judge-mcp (optional calibrated quality gate)",
        "human review / publication gate",
    ]

    if not semantic:
        return WatchtowerReport(
            source_id=impact.source_id,
            change_state=impact.state,
            semantic_change=False,
            alert_decision="suppressed",
            notify_reason="Source bytes changed without a declared fact delta, or no change occurred. Watchtower suppresses this as monitoring noise.",
            affected_claim_ids=impact.affected_claim_ids,
            affected_golden_case_ids=impact.affected_golden_case_ids,
            replays=[],
            provider_chain=provider_chain,
            human_review_required=False,
        )

    replays = [replay_golden_case(case_id) for case_id in impact.affected_golden_case_ids]
    passed = sum(replay.status == "passed" for replay in replays)
    failed = sum(replay.status == "failed" for replay in replays)
    blocked = sum(replay.status == "blocked" for replay in replays)

    if failed or blocked:
        decision = "review"
        reason = (
            f"Meaningful fact change detected, but replay coverage is incomplete or failing: "
            f"{passed} passed, {failed} failed, {blocked} blocked. Human review is required before guidance is updated."
        )
    else:
        decision = "notify"
        reason = (
            f"Meaningful fact change detected and all {passed} affected executable golden case(s) passed deterministic replay. "
            "Notify a reviewer/user of the material change; Judge MCP may be used as an additional quality gate."
        )

    human_review = bool(impact.changed_fact_ids or impact.removed_fact_ids or failed or blocked)
    return WatchtowerReport(
        source_id=impact.source_id,
        change_state=impact.state,
        semantic_change=True,
        alert_decision=decision,
        notify_reason=reason,
        affected_claim_ids=impact.affected_claim_ids,
        affected_golden_case_ids=impact.affected_golden_case_ids,
        replays=replays,
        passed=passed,
        failed=failed,
        blocked=blocked,
        provider_chain=provider_chain,
        human_review_required=human_review,
    )


def watchtower_status() -> dict[str, Any]:
    maturity = {"flagship": 0, "bounded-golden": 0, "other": 0}
    for fixture in REPLAY_FIXTURES.values():
        label = fixture.get("maturity", "other")
        maturity[label if label in maturity else "other"] += 1
    return {
        "version": "1.0.0-rc1",
        "mode": "scheduled-capable Watchtower; repo baselines + optional durable runtime snapshot store",
        "citizen_agents": {
            "provider": "mikelninh/citizen-agents",
            "contract": "cited/logged public-source monitoring event -> explicit previous snapshot -> CivicOS compare"
        },
        "judge_mcp": judge_status(),
        "executable_golden_cases": sorted(REPLAY_FIXTURES),
        "executable_count": len(REPLAY_FIXTURES),
        "maturity": maturity,
        "alert_policy": "suppress content-only noise; notify only on declared fact deltas; review if replay fails or coverage is blocked",
    }
