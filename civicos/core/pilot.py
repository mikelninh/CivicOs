from __future__ import annotations

import hashlib
import hmac
import os
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any

from fastapi import HTTPException, Request

PILOT_CONSENT_VERSION = "2026-08-28"
DEFAULT_MAX_UPLOAD_BYTES = 5 * 1024 * 1024
DEFAULT_RATE_LIMIT_PER_MINUTE = 30


@dataclass(frozen=True)
class PilotSettings:
    enabled: bool
    token_configured: bool
    max_upload_bytes: int
    rate_limit_per_minute: int
    consent_version: str = PILOT_CONSENT_VERSION
    personal_evidence_persistence: bool = False


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def settings() -> PilotSettings:
    token = os.getenv("CIVICOS_PILOT_TOKEN", "")
    return PilotSettings(
        enabled=_truthy(os.getenv("CIVICOS_PILOT_MODE")),
        token_configured=bool(token),
        max_upload_bytes=max(1024, int(os.getenv("CIVICOS_MAX_UPLOAD_BYTES", DEFAULT_MAX_UPLOAD_BYTES))),
        rate_limit_per_minute=max(1, int(os.getenv("CIVICOS_PILOT_RATE_LIMIT_PER_MINUTE", DEFAULT_RATE_LIMIT_PER_MINUTE))),
    )


def _pilot_token() -> str:
    return os.getenv("CIVICOS_PILOT_TOKEN", "")


def session_digest(token: str | None = None) -> str:
    secret = (token if token is not None else _pilot_token()).encode("utf-8")
    if not secret:
        return ""
    return hmac.new(secret, b"civicos-pilot-session-v1", hashlib.sha256).hexdigest()


def consent_digest(token: str | None = None, version: str = PILOT_CONSENT_VERSION) -> str:
    secret = (token if token is not None else _pilot_token()).encode("utf-8")
    if not secret:
        return ""
    return hmac.new(secret, f"civicos-pilot-consent:{version}".encode("utf-8"), hashlib.sha256).hexdigest()


def valid_invite(code: str) -> bool:
    expected = _pilot_token()
    return bool(expected) and hmac.compare_digest(code, expected)


def _has_session(request: Request) -> bool:
    supplied_header = request.headers.get("X-CivicOS-Pilot-Token", "")
    if supplied_header and valid_invite(supplied_header):
        return True
    cookie = request.cookies.get("civicos_pilot_session", "")
    expected = session_digest()
    return bool(expected) and hmac.compare_digest(cookie, expected)


def _has_consent(request: Request) -> bool:
    supplied_header = request.headers.get("X-CivicOS-Pilot-Consent", "").strip().lower()
    if supplied_header in {"accepted", "true", "1", PILOT_CONSENT_VERSION.lower()}:
        return True
    cookie = request.cookies.get("civicos_pilot_consent", "")
    expected = consent_digest()
    return bool(expected) and hmac.compare_digest(cookie, expected)


_rate_lock = Lock()
_rate_windows: dict[str, tuple[int, int]] = {}


def _rate_key(request: Request) -> str:
    # Deliberately avoids retaining IP addresses or user-agent strings.
    if request.cookies.get("civicos_pilot_session"):
        return request.cookies["civicos_pilot_session"][:24]
    token = request.headers.get("X-CivicOS-Pilot-Token", "")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:24] if token else "anonymous"


def enforce_rate_limit(request: Request) -> None:
    cfg = settings()
    if not cfg.enabled:
        return
    minute = int(time.time() // 60)
    key = _rate_key(request)
    with _rate_lock:
        window, count = _rate_windows.get(key, (minute, 0))
        if window != minute:
            window, count = minute, 0
        count += 1
        _rate_windows[key] = (window, count)
        if count > cfg.rate_limit_per_minute:
            raise HTTPException(status_code=429, detail="Pilot request limit reached. Please retry shortly.")


def require_pilot_access(request: Request) -> None:
    cfg = settings()
    if not cfg.enabled:
        return
    if not cfg.token_configured:
        raise HTTPException(status_code=503, detail="Pilot mode is enabled but no invite secret is configured.")
    if not _has_session(request):
        raise HTTPException(status_code=401, detail="Invite-only CivicOS pilot. Open /pilot and enter your invite code.")
    if not _has_consent(request):
        raise HTTPException(status_code=428, detail="Pilot consent is required before running personal or consequential workflows.")
    enforce_rate_limit(request)


def pilot_status() -> dict[str, Any]:
    cfg = settings()
    return {
        "mode": "invite_only_first_testers",
        "enabled": cfg.enabled,
        "invite_secret_configured": cfg.token_configured,
        "consent_version": cfg.consent_version,
        "max_upload_bytes": cfg.max_upload_bytes,
        "rate_limit_per_minute": cfg.rate_limit_per_minute,
        "personal_evidence_persistence": False,
        "document_processing": "in_memory_only",
        "request_body_logging": "not implemented by CivicOS application",
        "recommended_tester_scope": "adults only; redact identifiers where possible; do not upload health, criminal, authentication, or financial-account secrets",
        "not_claimed": ["GDPR compliance certification", "production IAM", "legal advice", "authority decision"],
    }
