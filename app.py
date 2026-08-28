from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from civicos.engine import run
from civicos.connectors.official import REGISTRY, SourceError, fetch_official
from civicos.core.evidence import make_receipt
from civicos.core.evidence_vault import EvidenceVault
from civicos.core.live_evidence import refresh_case_sources
from civicos.core.models import EvidenceFact
from civicos.core.pilot import (
    consent_digest,
    pilot_status,
    require_pilot_access,
    session_digest,
    settings as pilot_settings,
    valid_invite,
)
from civicos.core.providers import PROVIDERS
from civicos.core.readiness import release_readiness
from civicos.core.source_change import evaluate_source_change
from civicos.core.source_evidence import extract_live_facts
from civicos.core.watchtower import evaluate_watchtower, watchtower_status
from civicos.providers.pruefpilot import ingest_decision_document
from civicos.verticals.decision_review import attach_document_evidence, review_decision

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="CivicOS", version="1.0.0-rc2", description="Evidence-to-action civic infrastructure")


class RunRequest(BaseModel):
    vertical: str
    payload: dict | list | str
    refresh_sources: bool = False
    persist_public_evidence: bool = False


class SourceCompareRequest(BaseModel):
    previous_sha256: str | None = None
    previous_facts: list[dict] = Field(default_factory=list)
    monitor_metadata: dict = Field(default_factory=dict)


@app.middleware("http")
async def pilot_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; "
        "base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
    )
    return response


@app.get("/", response_class=HTMLResponse)
def home():
    return (ROOT / "web" / "home_v1.html").read_text(encoding="utf-8")


@app.get("/pilot", response_class=HTMLResponse)
def pilot_page():
    return (ROOT / "web" / "pilot.html").read_text(encoding="utf-8")


@app.post("/pilot/access")
def pilot_access(code: str = Form(...), consent: str | None = Form(None)):
    cfg = pilot_settings()
    if cfg.enabled:
        if not cfg.token_configured:
            raise HTTPException(status_code=503, detail="Pilot is not configured yet.")
        if not valid_invite(code):
            raise HTTPException(status_code=401, detail="Invalid CivicOS pilot invite code.")
        if consent != "accepted":
            raise HTTPException(status_code=400, detail="Please accept the pilot conditions before continuing.")

    response = RedirectResponse(url="/lab", status_code=303)
    if cfg.enabled:
        cookie_args = {
            "httponly": True,
            "secure": cfg.secure_cookies,
            "samesite": "strict",
            "max_age": 8 * 60 * 60,
            "path": "/",
        }
        response.set_cookie("civicos_pilot_session", session_digest(), **cookie_args)
        response.set_cookie("civicos_pilot_consent", consent_digest(), **cookie_args)
    return response


@app.post("/pilot/logout")
def pilot_logout():
    response = RedirectResponse(url="/pilot", status_code=303)
    response.delete_cookie("civicos_pilot_session", path="/")
    response.delete_cookie("civicos_pilot_consent", path="/")
    return response


@app.get("/pilot/status")
def get_pilot_status():
    return pilot_status()


@app.get("/lab", response_class=HTMLResponse)
def lab():
    return (ROOT / "web" / "index.html").read_text(encoding="utf-8")


@app.get("/watchtower", response_class=HTMLResponse)
def watchtower_page():
    return (ROOT / "web" / "watchtower.html").read_text(encoding="utf-8")


@app.get("/readiness/ui", response_class=HTMLResponse)
def readiness_page():
    return (ROOT / "web" / "readiness.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    return {
        "ok": True,
        "product": "CivicOS",
        "version": "1.0.0-rc2",
        "north_star": "Given what is known right now, what is the most useful thing I can do next — and why?",
        "evidence_contract": "source -> receipt -> fact delta -> affected claim -> golden-case replay -> quality gate -> alert decision",
        "pilot": pilot_status(),
    }


@app.get("/readiness")
def readiness(run_replays: bool = True):
    return release_readiness(run_replays=run_replays)


@app.get("/sources")
def sources():
    return {"sources": REGISTRY["sources"], "verified_at": REGISTRY.get("verified_at")}


@app.get("/providers")
def providers():
    return PROVIDERS


@app.get("/watchtower/status")
def get_watchtower_status():
    return watchtower_status()


@app.post("/sources/{source_id}/fetch", dependencies=[Depends(require_pilot_access)])
def fetch_source(source_id: str, persist: bool = False):
    try:
        receipt, body = fetch_official(source_id)
        if persist:
            vault = EvidenceVault.from_env()
            receipt = (
                vault.store_public_source(receipt, body)
                if vault.enabled
                else receipt.model_copy(update={"metadata": {"persistence_warning": "CIVICOS_EVIDENCE_DIR is not configured; receipt remains in memory only"}})
            )
        excerpts, facts = extract_live_facts(source_id, body, receipt.receipt_id)
        return {
            "source": source_id,
            "receipt": receipt.model_dump(mode="json"),
            "verified_facts": [fact.model_dump(mode="json") for fact in facts],
            "evidence_excerpts": [excerpt.model_dump(mode="json") for excerpt in excerpts],
            "raw_returned": False,
        }
    except SourceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _compare(source_id: str, req: SourceCompareRequest):
    receipt, body = fetch_official(source_id)
    excerpts, facts = extract_live_facts(source_id, body, receipt.receipt_id)
    previous = [EvidenceFact.model_validate(item) for item in req.previous_facts]
    impact = evaluate_source_change(
        source_id,
        previous_sha256=req.previous_sha256,
        current_sha256=receipt.sha256,
        previous_facts=previous,
        current_facts=facts,
    )
    return receipt, excerpts, facts, impact


@app.post("/sources/{source_id}/compare", dependencies=[Depends(require_pilot_access)])
def compare_source(source_id: str, req: SourceCompareRequest):
    try:
        receipt, excerpts, facts, impact = _compare(source_id, req)
        return {
            "receipt": receipt.model_dump(mode="json"),
            "current_facts": [fact.model_dump(mode="json") for fact in facts],
            "evidence_excerpts": [excerpt.model_dump(mode="json") for excerpt in excerpts],
            "impact": impact.model_dump(mode="json"),
            "raw_returned": False,
        }
    except SourceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/watchtower/{source_id}", dependencies=[Depends(require_pilot_access)])
def run_watchtower(source_id: str, req: SourceCompareRequest):
    try:
        receipt, excerpts, facts, impact = _compare(source_id, req)
        report = evaluate_watchtower(impact, monitor_metadata=req.monitor_metadata)
        return {
            "monitor": req.monitor_metadata,
            "receipt": receipt.model_dump(mode="json"),
            "current_facts": [fact.model_dump(mode="json") for fact in facts],
            "evidence_excerpts": [excerpt.model_dump(mode="json") for excerpt in excerpts],
            "impact": impact.model_dump(mode="json"),
            "watchtower": report.model_dump(mode="json"),
            "raw_returned": False,
        }
    except SourceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/run", dependencies=[Depends(require_pilot_access)])
def run_case(req: RunRequest):
    try:
        result = run(req.vertical, req.payload)
        if req.refresh_sources:
            result = refresh_case_sources(result, persist_public_evidence=req.persist_public_evidence)
        return result.model_dump(mode="json")
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/decision-review/upload", dependencies=[Depends(require_pilot_access)])
async def upload_decision(file: UploadFile = File(...), refresh_sources: bool = False):
    cfg = pilot_settings()
    suffix = Path(file.filename or "").suffix.lower()
    allowed_types = {"application/pdf", "text/plain", "application/octet-stream"}
    if suffix not in {".pdf", ".txt"} and (file.content_type or "") not in allowed_types:
        raise HTTPException(status_code=415, detail="Pilot accepts PDF or plain-text decisions only.")

    content = await file.read(cfg.max_upload_bytes + 1)
    if len(content) > cfg.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Document is too large for the pilot. Maximum is {cfg.max_upload_bytes // (1024 * 1024)} MB.",
        )

    try:
        intake = ingest_decision_document(file.filename or "decision.pdf", content, file.content_type or "")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if intake.status == "quarantined":
        return {
            "blocked": True,
            "reason": "Uploaded document contains instruction-like or script-like content and was quarantined as untrusted data.",
            "intake": intake.to_dict(),
            "case": None,
        }

    result = review_decision(intake.text)
    user_receipt = make_receipt(
        "user-decision-document",
        content,
        content_type=file.content_type or "application/octet-stream",
        status_code=200,
    ).model_copy(
        update={
            "metadata": {
                "filename": intake.filename,
                "page_count": intake.page_count,
                "provider": intake.provider,
                "privacy": "hash-and-process-in-memory; uploaded bytes are not persisted by the CivicOS invite-only pilot",
                "trust_level": "user_evidence_untrusted_content",
            }
        }
    )
    result = result.model_copy(
        update={
            "evidence_receipts": [user_receipt],
            "audit": list(result.audit)
            + [
                {
                    "step": "pruefpilot_document_intake_pilot_rc2",
                    "filename": intake.filename,
                    "sha256": intake.sha256,
                    "bytes": intake.bytes_read,
                    "page_count": intake.page_count,
                    "persisted": False,
                }
            ],
        }
    )
    result = attach_document_evidence(result, user_receipt.receipt_id)
    if refresh_sources:
        result = refresh_case_sources(result)
    return {"blocked": False, "intake": intake.to_dict(), "case": result.model_dump(mode="json")}
