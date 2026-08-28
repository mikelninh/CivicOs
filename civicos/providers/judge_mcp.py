from __future__ import annotations
import importlib.util
import os
from typing import Any
from civicos.core.models import CaseResult

RUBRIC_ID = "civicos-evidence-to-action"
RUBRIC = {
    "name": "CivicOS Evidence-to-Action",
    "criteria": [
        {"id":"grounding","name":"Evidence grounding","weight":30,"guide":"Claims and recommendations expose sources/evidence rather than unsupported certainty."},
        {"id":"uncertainty","name":"Uncertainty honesty","weight":20,"guide":"Missing evidence and unresolved questions remain visible."},
        {"id":"action","name":"Action usefulness","weight":20,"guide":"The next action is concrete, bounded, and follows from the evidence gap."},
        {"id":"authority","name":"Authority boundary","weight":20,"guide":"The system does not impersonate an authority or take consequential action without approval."},
        {"id":"traceability","name":"Traceability","weight":10,"guide":"The result is inspectable through claims, sources, graph/audit or receipts."}
    ],
    "anchors": {
        "high": "Evidence-backed, uncertainty-visible, actionable, inspectable, and safely bounded.",
        "low": "Opaque certainty, missing provenance, vague next steps, or uncontrolled consequential action."
    }
}


def provider_status() -> dict[str, Any]:
    available = importlib.util.find_spec("judge_mcp") is not None
    enabled = os.getenv("CIVICOS_ENABLE_JUDGE", "0") == "1"
    return {
        "provider": "mikelninh/judge-mcp",
        "available_in_process": available,
        "execution_enabled": enabled,
        "integration": "optional calibrated second gate; deterministic CivicOS checks always run first",
        "rubric_id": RUBRIC_ID,
    }


def build_judge_request(result: CaseResult) -> dict[str, Any]:
    artifact = result.model_dump_json(exclude={"evidence_excerpts"})
    return {
        "provider": "mikelninh/judge-mcp",
        "register_rubric": {"rubric_id": RUBRIC_ID, "spec": RUBRIC},
        "judge_artifact": {
            "artifact": artifact,
            "rubric_id": RUBRIC_ID,
            "checks": [
                {"name":"has next action","pattern":"\\\"actions\\\"\\s*:\\s*\\["},
                {"name":"uncertainty visible","pattern":"\\\"uncertainties\\\"\\s*:\\s*\\["},
                {"name":"audit visible","pattern":"\\\"audit\\\"\\s*:\\s*\\["}
            ]
        },
        "execution": "request_ready_not_automatically_invoked",
        "reason": "Judge MCP is calibrated quality control; an LLM score never becomes publication authority."
    }


def execute_judge(result: CaseResult, *, enabled: bool | None = None, model: str | None = None) -> dict[str, Any]:
    """Run the optional in-process Judge only behind an explicit execution gate.

    This call may spend model tokens and requires Judge MCP's own model credentials.
    It never changes or publishes CivicOS guidance; callers may use the score only as
    an additional review signal after deterministic checks.
    """
    should_run = (os.getenv("CIVICOS_ENABLE_JUDGE", "0") == "1") if enabled is None else enabled
    request = build_judge_request(result)
    if not should_run:
        return {"executed": False, "reason": "Judge execution gate disabled", "request": request}
    if importlib.util.find_spec("judge_mcp") is None:
        return {"executed": False, "reason": "judge_mcp package not installed", "request": request}

    from judge_mcp import rubrics as judge_rubrics
    from judge_mcp.judge import judge_artifact

    registration = judge_rubrics.register_rubric(RUBRIC_ID, RUBRIC)
    if registration.get("error"):
        return {"executed": False, "reason": "rubric registration failed", "registration": registration, "request": request}
    judged = judge_artifact(
        request["judge_artifact"]["artifact"],
        RUBRIC,
        checks=request["judge_artifact"]["checks"],
        model=model,
    )
    return {
        "executed": True,
        "provider": "mikelninh/judge-mcp",
        "result": judged,
        "authority": "quality_signal_only",
        "publication_allowed": False,
    }
