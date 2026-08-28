from fastapi.testclient import TestClient

from app import app
from civicos.core.readiness import release_readiness


def _pilot_env(monkeypatch, *, max_bytes: int = 5 * 1024 * 1024):
    monkeypatch.setenv("CIVICOS_PILOT_MODE", "true")
    monkeypatch.setenv("CIVICOS_PILOT_TOKEN", "test-invite-secret")
    monkeypatch.setenv("CIVICOS_PILOT_SECURE_COOKIES", "false")
    monkeypatch.setenv("CIVICOS_MAX_UPLOAD_BYTES", str(max_bytes))
    monkeypatch.setenv("CIVICOS_PILOT_RATE_LIMIT_PER_MINUTE", "30")


def _headers():
    return {
        "X-CivicOS-Pilot-Token": "test-invite-secret",
        "X-CivicOS-Pilot-Consent": "accepted",
    }


def _benefits_body():
    return {
        "vertical": "benefits",
        "payload": {
            "location": "Berlin",
            "children": 0,
            "household_size": 1,
            "monthly_household_income": 1800,
            "monthly_rent": 800,
            "housing_transfer_benefit_status": "none",
        },
    }


def test_pilot_blocks_write_without_invite(monkeypatch):
    _pilot_env(monkeypatch)
    with TestClient(app) as client:
        response = client.post("/run", json=_benefits_body())
    assert response.status_code == 401


def test_pilot_requires_consent_even_with_valid_invite(monkeypatch):
    _pilot_env(monkeypatch)
    with TestClient(app) as client:
        response = client.post(
            "/run",
            json=_benefits_body(),
            headers={"X-CivicOS-Pilot-Token": "test-invite-secret"},
        )
    assert response.status_code == 428


def test_pilot_header_access_can_run_bounded_workflow(monkeypatch):
    _pilot_env(monkeypatch)
    with TestClient(app) as client:
        response = client.post("/run", json=_benefits_body(), headers=_headers())
    assert response.status_code == 200
    assert response.json()["actions"]


def test_pilot_portal_sets_signed_http_only_session_and_consent(monkeypatch):
    _pilot_env(monkeypatch)
    with TestClient(app) as client:
        access = client.post(
            "/pilot/access",
            data={"code": "test-invite-secret", "consent": "accepted"},
            follow_redirects=False,
        )
        assert access.status_code == 303
        cookies = access.headers.get_list("set-cookie")
        assert any("civicos_pilot_session=" in item and "HttpOnly" in item and "SameSite=strict" in item for item in cookies)
        assert any("civicos_pilot_consent=" in item and "HttpOnly" in item for item in cookies)
        run = client.post("/run", json=_benefits_body())
    assert run.status_code == 200


def test_pilot_upload_size_is_hard_bounded(monkeypatch):
    _pilot_env(monkeypatch, max_bytes=1024)
    with TestClient(app) as client:
        response = client.post(
            "/decision-review/upload",
            files={"file": ("decision.txt", b"x" * 1025, "text/plain")},
            headers=_headers(),
        )
    assert response.status_code == 413


def test_pilot_rejects_unexpected_upload_types(monkeypatch):
    _pilot_env(monkeypatch)
    with TestClient(app) as client:
        response = client.post(
            "/decision-review/upload",
            files={"file": ("photo.jpg", b"not-an-image", "image/jpeg")},
            headers=_headers(),
        )
    assert response.status_code == 415


def test_pilot_decision_upload_does_not_persist_document_bytes(monkeypatch):
    _pilot_env(monkeypatch)
    decision = (
        "Wohngeldstelle Berlin\nBescheid vom 20.08.2026\nIhr Antrag wird abgelehnt.\n"
        "Begründung: Die eingereichten Unterlagen seien nicht vollständig.\n"
        "Rechtsbehelfsbelehrung: Bitte beachten Sie die im Originalbescheid genannte Frist."
    ).encode("utf-8")
    with TestClient(app) as client:
        response = client.post(
            "/decision-review/upload",
            files={"file": ("decision.txt", decision, "text/plain")},
            headers=_headers(),
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["blocked"] is False
    audit = payload["case"]["audit"]
    intake_steps = [step for step in audit if step.get("step") == "pruefpilot_document_intake_pilot_rc2"]
    assert intake_steps and intake_steps[0]["persisted"] is False


def test_responses_include_no_store_and_browser_security_headers(monkeypatch):
    _pilot_env(monkeypatch)
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["cache-control"].startswith("no-store")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_first_tester_release_gate_is_ready_without_claiming_public_beta(monkeypatch):
    monkeypatch.delenv("CIVICOS_PILOT_MODE", raising=False)
    monkeypatch.delenv("CIVICOS_PILOT_TOKEN", raising=False)
    readiness = release_readiness()
    assert readiness["master_proof_ready"] is True
    assert readiness["first_tester_pilot_ready"] is True
    assert readiness["pilot_runtime_configured"] is False
    assert readiness["public_beta_ready"] is False
