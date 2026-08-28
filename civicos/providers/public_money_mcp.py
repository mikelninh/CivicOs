from __future__ import annotations
import importlib
from typing import Any

ALLOWED_TOOLS = {
    "get_budget",
    "compute_distribution",
    "detect_anomalies",
    "lookup_brh_findings",
    "compare_years",
    "compose_sankey_data",
}


class PublicMoneyProviderError(RuntimeError):
    pass


def provider_status() -> dict[str, Any]:
    try:
        importlib.import_module("pmm_mcp.server")
        available = True
    except Exception:
        available = False
    return {
        "provider": "Public Money MCP",
        "repository": "https://github.com/mikelninh/pmm-mcp",
        "available_in_process": available,
        "tools": sorted(ALLOWED_TOOLS),
        "coverage": "Bundeshaushalt snapshots + curated Bundesrechnungshof findings",
        "known_gap": "No recipient/payment-level public-finance database yet.",
    }


def call_tool(tool: str, **kwargs: Any) -> dict[str, Any]:
    if tool not in ALLOWED_TOOLS:
        raise PublicMoneyProviderError(f"Unsupported Public Money MCP tool: {tool}")
    try:
        module = importlib.import_module("pmm_mcp.server")
    except Exception as exc:
        raise PublicMoneyProviderError(
            "Public Money MCP is not installed in this CivicOS runtime. Install the optional provider or run it as a separate MCP service."
        ) from exc
    fn = getattr(module, tool, None)
    if not callable(fn):
        raise PublicMoneyProviderError(f"Provider tool is unavailable: {tool}")
    result = fn(**kwargs)
    if not isinstance(result, dict):
        raise PublicMoneyProviderError(f"Provider returned an unexpected response for {tool}")
    return result
