from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from civicos.engine import run
from civicos.connectors.official import REGISTRY, SourceError, fetch_official
from civicos.core.evidence import make_receipt
from civicos.core.evidence_vault import EvidenceVault
from civicos.core.live_evidence import refresh_case_sources
from civicos.core.models import EvidenceFact
from civicos.core.providers import PROVIDERS
from civicos.core.source_change import evaluate_source_change
from civicos.core.source_evidence import extract_live_facts
from civicos.providers.pruefpilot import ingest_decision_document
from civicos.verticals.decision_review import attach_document_evidence, review_decision

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="CivicOS", version="0.5.0", description="Evidence-to-action civic infrastructure")


class RunRequest(BaseModel):
    vertical: str
    payload: dict | list | str
    refresh_sources: bool = False
    persist_public_evidence: bool = False


class SourceCompareRequest(BaseModel):
    previous_sha256: str | None = None
    previous_facts: list[dict] = []


@app.get("/", response_class=HTMLResponse)
def home():
    return (ROOT / "web" / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    return {
        "ok": True,
        "product": "CivicOS",
        "version": "0.5.0",
        "north_star": "Given what is known right now, what is the most useful thing I can do next — and why?",
        "evidence_contract": "source -> receipt -> verified fact -> claim -> change impact -> regression case -> next action",
    }


@app.get("/sources")
def sources():
    return {"sources": REGISTRY["sources"], "verified_at": REGISTRY.get("verified_at")}


@app.get("/providers")
def providers():
    return PROVIDERS


@app.post("/sources/{source_id}/fetch")
def fetch_source(source_id: str, persist: bool = False):
    try:
        receipt, body = fetch_official(source_id)
        if persist:
            vault = EvidenceVault.from_env()
            receipt = vault.store_public_source(receipt, body) if vault.enabled else receipt.model_copy(update={"metadata":{"persistence_warning":"CIVICOS_EVIDENCE_DIR is not configured; receipt remains in memory only"}})
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


@app.post("/sources/{source_id}/compare")
def compare_source(source_id: str, req: SourceCompareRequest):
    """Live-fetch a source and report which claims/golden cases need re-checking.

    The caller supplies the previous receipt hash/facts from its own evidence store.
    CivicOS does not invent history when no previous snapshot exists.
    """
    try:
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
        return {
            "receipt": receipt.model_dump(mode="json"),
            "current_facts": [fact.model_dump(mode="json") for fact in facts],
            "evidence_excerpts": [excerpt.model_dump(mode="json") for excerpt in excerpts],
            "impact": impact.model_dump(mode="json"),
            "raw_returned": False,
        }
    except SourceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/run")
def run_case(req: RunRequest):
    try:
        result = run(req.vertical, req.payload)
        if req.refresh_sources:
            result = refresh_case_sources(result, persist_public_evidence=req.persist_public_evidence)
        return result.model_dump(mode="json")
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/decision-review/upload")
async def upload_decision(file: UploadFile = File(...), refresh_sources: bool = False):
    content = await file.read()
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
    ).model_copy(update={
        "metadata": {
            "filename": intake.filename,
            "page_count": intake.page_count,
            "provider": intake.provider,
            "privacy": "hash-and-process-in-memory; uploaded bytes are not persisted by CivicOS v0.5",
            "trust_level": "user_evidence_untrusted_content",
        }
    })
    result = result.model_copy(update={
        "evidence_receipts": [user_receipt],
        "audit": list(result.audit) + [{
            "step": "pruefpilot_document_intake_v5",
            "filename": intake.filename,
            "sha256": intake.sha256,
            "bytes": intake.bytes_read,
            "page_count": intake.page_count,
            "persisted": False,
        }],
    })
    result = attach_document_evidence(result, user_receipt.receipt_id)
    if refresh_sources:
        result = refresh_case_sources(result)
    return {"blocked": False, "intake": intake.to_dict(), "case": result.model_dump(mode="json")}
