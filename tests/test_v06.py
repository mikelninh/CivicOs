from civicos.core.models import EvidenceFact
from civicos.core.source_change import evaluate_source_change
from civicos.core.watchtower import evaluate_watchtower, replay_golden_case, watchtower_status


def _fact(value: int, receipt: str) -> EvidenceFact:
    return EvidenceFact(
        fact_id="kiz:max-per-child",
        claim_id="benefit:kinderzuschlag",
        source_id="arbeitsagentur_kiz",
        receipt_id=receipt,
        label="Kinderzuschlag maximum per child/month",
        value=value,
    )


def test_watchtower_suppresses_content_only_noise():
    impact = evaluate_source_change(
        "arbeitsagentur_kiz",
        previous_sha256="old",
        current_sha256="new",
        previous_facts=[_fact(297, "old")],
        current_facts=[_fact(297, "new")],
    )
    report = evaluate_watchtower(impact)
    assert impact.state == "content_changed"
    assert report.alert_decision == "suppressed"
    assert report.semantic_change is False
    assert report.replays == []


def test_watchtower_replays_affected_case_on_fact_change():
    impact = evaluate_source_change(
        "arbeitsagentur_kiz",
        previous_sha256="old",
        current_sha256="new",
        previous_facts=[_fact(297, "old")],
        current_facts=[_fact(305, "new")],
    )
    report = evaluate_watchtower(impact)
    assert report.semantic_change is True
    assert report.alert_decision == "notify"
    assert report.passed == 1
    assert report.failed == 0
    assert report.blocked == 0
    assert report.human_review_required is True
    replay = report.replays[0]
    assert replay.case_id == "citizen-benefits-gap"
    assert replay.status == "passed"
    assert replay.deterministic_checks["external_actions_require_approval"] is True
    assert replay.judge_request["provider"] == "mikelninh/judge-mcp"
    assert replay.judge_request["execution"] == "request_ready_not_automatically_invoked"


def test_unknown_golden_case_is_blocked_not_fake_passed():
    replay = replay_golden_case("not-a-real-golden-case")
    assert replay.status == "blocked"
    assert "refuses to fake" in replay.note


def test_watchtower_status_exposes_provider_boundaries_and_closed_coverage_gap():
    status = watchtower_status()
    assert status["version"] == "1.0.0-rc1"
    assert status["citizen_agents"]["provider"] == "mikelninh/citizen-agents"
    assert status["judge_mcp"]["provider"] == "mikelninh/judge-mcp"
    assert status["executable_count"] == 12
    assert "citizen-benefits-gap" in status["executable_golden_cases"]
    assert "operator-policy-change-impact" in status["executable_golden_cases"]
