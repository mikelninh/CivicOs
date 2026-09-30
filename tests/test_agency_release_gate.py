from civicos.core.readiness import agency_release_gate


def test_agency_release_adapter_preserves_civicos_truth_boundaries():
    gate = agency_release_gate()
    assert gate["schema"] == "openaction.release-gate.adapter.v1"
    assert gate["project"] == "CivicOS"
    by_stage = {item["stage"]: item for item in gate["gates"]}
    assert set(by_stage) == {"R0", "R1", "R2", "R3", "R4"}
    assert by_stage["R1"]["status"] == "pass"
    assert by_stage["R2"]["status"] == "pass"
    # CI intentionally has no pilot secret, so runtime remains a human deployment review.
    assert by_stage["R3"]["status"] == "review"
    # Public beta must not be inferred from a green invite-only pilot build.
    assert by_stage["R4"]["status"] == "review"
    assert gate["verdict"] == "REVIEW"
    assert by_stage["R4"]["owner"] == "external"
