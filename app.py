from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from civicos.engine import run
from civicos.connectors.official import REGISTRY
from civicos.core.providers import PROVIDERS

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="CivicOS", version="0.1.0", description="Evidence-to-action civic infrastructure")

class RunRequest(BaseModel):
    vertical: str
    payload: dict | list | str

@app.get("/", response_class=HTMLResponse)
def home():
    return (ROOT / "web" / "index.html").read_text(encoding="utf-8")

@app.get("/health")
def health():
    return {"ok": True, "product": "CivicOS", "version": "0.1.0"}

@app.get("/sources")
def sources():
    return {"sources": REGISTRY["sources"]}

@app.get("/providers")
def providers():
    return PROVIDERS

@app.post("/run")
def run_case(req: RunRequest):
    try:
        return run(req.vertical, req.payload).model_dump(mode="json")
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
