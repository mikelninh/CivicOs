from datetime import datetime, timezone

from civicos.core.models import EvidenceFact, EvidenceReceipt
from civicos.core.readiness import release_readiness
from civicos.core.snapshot_store import SnapshotStore
from civicos.core.watchtower import replay_all_golden_cases, watchtower_status
from civicos.providers.judge_mcp import execute_judge
from civicos.engine import run


def test_all_12_golden_cases_are_executable_and_pass_contract():
    replays = replay_all_golden_cases()
    assert len(replays) == 12
    assert all(replay.status == "passed" for replay in replays)


def test_watchtower_distinguishes_three_flagship_verticals_from_bounded_cases():
    status = watchtower_status()
    assert status["executable_count"] == 12
    assert status["maturity"]["flagship"] == 5
    assert status["maturity"]["bounded-golden"] == 7


def test_release_gate_can_be_master_proof_ready_without_claiming_public_beta():
    readiness = release_readiness()
    assert readiness["master_proof_ready"] is True
    assert readiness["public_beta_ready"] is False
    assert readiness["golden_cases"]["passed"] == 12
    assert readiness["golden_cases"]["flagship_verticals"] == ["benefits", "decision-review", "public-money"]


def test_snapshot_store_roundtrip(tmp_path):
    store = SnapshotStore(tmp_path / "state.sqlite3")
    receipt = EvidenceReceipt(
        receipt_id="receipt:test",
        source_id="arbeitsagentur_kiz",
        fetched_at=datetime.now(timezone.utc),
        sha256="abc123",
        bytes_read=10,
    )
    fact = EvidenceFact(
        fact_id="kiz:max-per-child",
        claim_id="benefit:kinderzuschlag",
        source_id="arbeitsagentur_kiz",
        receipt_id="receipt:test",
        label="Kinderzuschlag maximum per child/month",
        value=297,
    )
    store.save(receipt, [fact], {"reviewed": False})
    latest = store.latest("arbeitsagentur_kiz")
    assert latest is not None
    assert latest.sha256 == "abc123"
    assert latest.facts[0]["value"] == 297
    assert store.count("arbeitsagentur_kiz") == 1


def test_judge_execution_is_disabled_by_default_and_never_publishes():
    result = run("benefits", {"location":"Berlin","children":0,"household_size":1,"monthly_household_income":1800,"monthly_rent":800,"housing_transfer_benefit_status":"none"})
    judged = execute_judge(result, enabled=False)
    assert judged["executed"] is False
    assert judged["request"]["execution"] == "request_ready_not_automatically_invoked"
