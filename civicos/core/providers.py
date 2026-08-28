from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROVIDERS = json.loads((ROOT / "data" / "providers.json").read_text(encoding="utf-8"))

def provider_for(capability: str) -> list[dict]:
    matches = []
    for provider_id, provider in PROVIDERS["providers"].items():
        if capability in provider["capabilities"]:
            matches.append({"provider_id": provider_id, **provider})
    return matches

def composition_status(required_capabilities: list[str]) -> dict:
    missing = [cap for cap in required_capabilities if not provider_for(cap)]
    return {"required":required_capabilities,"covered":[cap for cap in required_capabilities if cap not in missing],"missing":missing,"coverage":1 - (len(missing)/len(required_capabilities) if required_capabilities else 0)}
