from __future__ import annotations
import json
from pathlib import Path
from urllib.request import Request, urlopen
from civicos.core.evidence import make_receipt
from civicos.core.models import SourceRef

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
MAX_BYTES = 2_000_000

class SourceError(RuntimeError):
    pass

def get_source(source_id: str) -> dict:
    try:
        return REGISTRY["sources"][source_id]
    except KeyError as exc:
        raise SourceError(f"Unknown or non-allowlisted source: {source_id}") from exc

def source_ref(source_id: str, state: str = "verified_route") -> SourceRef:
    s = get_source(source_id)
    return SourceRef(source_id=source_id,title=s["title"],publisher=s["publisher"],url=s["url"],state=state,verified_at=s["verified_at"])

def fetch_official(source_id: str, timeout_seconds: int = 12):
    source = get_source(source_id)
    req = Request(source["url"],headers={"User-Agent":"CivicOS/0.1 (+evidence-to-action public-interest prototype)","Accept":"text/html,application/json,application/xml,text/plain,*/*;q=0.1"})
    try:
        with urlopen(req, timeout=timeout_seconds) as response:  # nosec: registry allowlist only
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise SourceError(f"Source exceeded {MAX_BYTES} bytes: {source_id}")
            receipt = make_receipt(source_id,body,content_type=response.headers.get("Content-Type", ""),status_code=int(getattr(response, "status", 200)))
            return receipt, body
    except Exception as exc:
        raise SourceError(f"Live fetch failed for {source_id}: {exc}") from exc
