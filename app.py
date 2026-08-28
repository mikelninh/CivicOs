from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from civicos.engine import run
from civicos.connectors.official import REGISTRY

app = FastAPI(title="CivicOS", version="0.1.0", description="Evidence-to-action civic infrastructure")

class RunRequest(BaseModel):
    vertical: str
    payload: dict | list | str

@app.get("/health")
def health(): return {"ok": True, "product": "CivicOS", "version": "0.1.0"}

@app.get("/sources")
def sources(): return {"sources": REGISTRY["sources"]}

@app.post("/run")
def run_case(req: RunRequest):
    try: return run(req.vertical, req.payload).model_dump(mode="json")
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
