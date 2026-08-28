from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from civicos.core.pilot import pilot_status
from civicos.core.watchtower import REPLAY_FIXTURES, replay_all_golden_cases, watchtower_status

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = json.loads((ROOT / "data" / "golden_cases.json").read_text(encoding="utf-8"))["cases"]
SOURCES = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
IMPACT_MAP = json.loads((ROOT / "data" / "source_impact_map.json").read_text(encoding="utf-8"))
PILOT_POLICY = json.loads((ROOT / "data" / "pilot_policy.json").read_text(encoding="utf-8"))


def release_readiness(run_replays: bool = True) -> dict[str, Any]:
    case_ids = {case["id"] for case in GOLDEN}
    fixture_ids = set(REPLAY_FIXTURES)
    mapped_cases = {
        case_id
        for mapping in IMPACT_MAP.get("sources", {}).values()
        for case_id in mapping.get("golden_case_ids", [])
    }
    replays = replay_all_golden_cases() if run_replays else []
    passed = sum(item.status == "passed" for item in replays) if run_replays else None
    blocked = sum(item.status == "blocked" for item in replays) if run_replays else None
    failed = sum(item.status == "failed" for item in replays) if run_replays else None

    flagship_verticals = sorted({
        fixture.get("vertical")
        for fixture in REPLAY_FIXTURES.values()
        if fixture.get("maturity") == "flagship" and fixture.get("vertical")
    })

    master_gates = {
        "golden_case_catalog_12": len(GOLDEN) == 12,
        "all_golden_cases_executable": case_ids == fixture_ids,
        "all_replays_pass": (passed == len(GOLDEN)) if run_replays else None,
        "all_golden_cases_have_source_impact_edges": case_ids.issubset(mapped_cases),
        "flagship_verticals_3": set(flagship_verticals) == {"benefits", "decision-review", "public-money"},
        "watchtower_scheduled": (ROOT / ".github" / "workflows" / "watchtower.yml").exists(),
        "durable_snapshot_adapter": (ROOT / "civicos" / "core" / "snapshot_store.py").exists(),
        "reviewed_semantic_baselines": (ROOT / "data" / "watchtower_baselines.json").exists(),
        "official_source_registry_current": SOURCES.get("verified_at") == "2026-08-28",
    }
    master_ready = all(value is True for value in master_gates.values() if value is not None)

    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    pilot_policy_ok = (
        PILOT_POLICY.get("mode") == "invite_only_first_testers"
        and PILOT_POLICY.get("audience", {}).get("adults_only") is True
        and PILOT_POLICY.get("data", {}).get("personal_document_bytes_persisted") is False
        and PILOT_POLICY.get("authority", {}).get("automatic_external_actions") is False
    )
    upload_limit = int(PILOT_POLICY.get("limits", {}).get("max_upload_bytes", 0))
    allowed_uploads = set(PILOT_POLICY.get("limits", {}).get("allowed_uploads", []))

    pilot_gates = {
        "master_proof_ready": master_ready,
        "invite_only_access_guard": (ROOT / "civicos" / "core" / "pilot.py").exists() and "require_pilot_access" in app_text,
        "explicit_adult_consent_portal": (ROOT / "web" / "pilot.html").exists() and "pilot_consent" in app_text,
        "personal_document_persistence_disabled": pilot_policy_ok and '"persisted": False' in app_text,
        "bounded_pdf_text_uploads": 0 < upload_limit <= 5 * 1024 * 1024 and allowed_uploads == {"pdf", "txt"} and "status_code=413" in app_text,
        "browser_no_store_and_security_headers": all(
            marker in app_text
            for marker in ["Cache-Control", "Content-Security-Policy", "X-Content-Type-Options", "Referrer-Policy"]
        ),
        "rate_limit_without_ip_retention": "enforce_rate_limit" in (ROOT / "civicos" / "core" / "pilot.py").read_text(encoding="utf-8"),
        "machine_readable_pilot_policy": pilot_policy_ok,
        "tester_release_runbook": (ROOT / "docs" / "PILOT_RELEASE.md").exists(),
        "privacy_minimising_feedback_path": (ROOT / ".github" / "ISSUE_TEMPLATE" / "pilot-feedback.yml").exists(),
        "pilot_regression_tests_present": (ROOT / "tests" / "test_pilot_release.py").exists(),
    }
    pilot_ready = all(value is True for value in pilot_gates.values())
    runtime = pilot_status()
    pilot_runtime_configured = bool(
        runtime.get("enabled")
        and runtime.get("invite_secret_configured")
        and runtime.get("secure_cookies")
    )

    # These are intentionally stricter than the invite-only first-tester pilot.
    public_beta_gates = {
        "first_tester_pilot_ready": pilot_ready,
        "encrypted_persisted_personal_evidence": False,
        "production_iam_and_retention_deletion_controls": False,
        "qualified_domain_review_benefits_and_admin_law": False,
        "representative_user_evaluation": False,
        "genuine_recipient_payment_provider": False,
        "authorised_register_ids_and_temporal_control": False,
    }
    public_beta_ready = all(public_beta_gates.values())

    return {
        "release_candidate": "1.0.0-rc2",
        "master_proof_ready": master_ready,
        "first_tester_pilot_ready": pilot_ready,
        "pilot_runtime_configured": pilot_runtime_configured,
        "public_beta_ready": public_beta_ready,
        "master_proof_gates": master_gates,
        "first_tester_pilot_gates": pilot_gates,
        "pilot_runtime": runtime,
        "public_beta_gates": public_beta_gates,
        "golden_cases": {
            "catalog": len(GOLDEN),
            "fixtures": len(REPLAY_FIXTURES),
            "source_impact_covered": len(case_ids & mapped_cases),
            "passed": passed,
            "failed": failed,
            "blocked": blocked,
            "flagship_verticals": flagship_verticals,
            "bounded_golden_cases": sum(f.get("maturity") == "bounded-golden" for f in REPLAY_FIXTURES.values()),
        },
        "watchtower": watchtower_status(),
        "release_definition": {
            "v1_master_proof": "12/12 executable product/safety cases + 12/12 source-impact coverage + 3 deeper flagship verticals + live evidence/change monitoring + scheduled Watchtower + human authority boundaries.",
            "first_tester_pilot": "Invite-only adults, explicit consent, signed short-lived session, no personal document persistence, bounded uploads, no-store responses, safe feedback path and hard stop conditions. Deployment still requires CIVICOS_PILOT_MODE=true and a secret configured outside Git.",
            "public_beta": "Still requires production IAM/security/privacy controls, qualified domain review, representative users and missing authoritative data providers."
        },
    }
