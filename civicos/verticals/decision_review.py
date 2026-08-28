from __future__ import annotations
import re
from civicos.adapters.law import verify_many
from civicos.connectors.official import source_ref
from civicos.core.models import ActionRecommendation, CaseResult, Claim

DATE_RE = re.compile(r"\b(\d{1,2}\.\d{1,2}\.\d{4})\b")
LAW_RE = re.compile(r"(§{1,2}\s*\d+[a-zA-Z]?(?:\s*Abs\.\s*\d+)?(?:\s+(?:VwVfG|BGB|WoGG|SGB\s*[IVX]+))?)")


def review_decision(text: str) -> CaseResult:
    dates = sorted(set(DATE_RE.findall(text)))
    citations = sorted(set(m.group(1).strip() for m in LAW_RE.finditer(text)))
    default_law = "VwVfG" if "VwVfG" in text else None
    citation_checks = verify_many(citations, default_law=default_law)
    resolved = [c for c in citation_checks if c["verification"] == "official_route_resolved"]
    unresolved = [c for c in citation_checks if c["verification"] != "official_route_resolved"]

    lower = text.lower()
    has_reasoning = "begründ" in lower
    has_remedy = "rechtsbehelf" in lower or "widerspruch" in lower or "klage" in lower

    claims = [
        Claim(claim_id="decision:reasoning-present", text=f"Reasoning language detected: {has_reasoning}.", status="supported", confidence=1.0),
        Claim(claim_id="decision:remedy-language-present", text=f"Legal-remedy language detected: {has_remedy}.", status="supported", confidence=1.0),
        Claim(claim_id="decision:dates", text=f"Dates extracted: {dates or ['none']}.", status="supported", confidence=1.0),
        Claim(
            claim_id="decision:cited-provisions", text=f"Provision-like citations extracted: {citations or ['none']}.",
            status="supported", confidence=1.0,
            details={"checks": citation_checks, "provider":"mikelninh/gitlaw", "resolved_count":len(resolved), "unresolved_count":len(unresolved)}
        )
    ]

    missing = []
    if not has_reasoning:
        missing.append("stated factual and legal reasons")
    if not has_remedy:
        missing.append("legal-remedy instruction or sector-specific deadline basis")
    if not dates:
        missing.append("decision/service/receipt dates")
    if not citations:
        missing.append("cited legal provisions")
    if unresolved:
        missing.append("GitLaw section-level lookup for unresolved/ambiguous citations")

    proof = [
        f"{len(dates)} date(s) extracted",
        f"{len(citations)} citation(s) extracted",
        f"{len(resolved)} official section route(s) deterministically resolved",
        "GitLaw provider boundary retained for broader current-law verification"
    ]
    action = ActionRecommendation(
        action_id="prepare:decision-review", title="Prepare a source-checked review checklist before responding",
        why="A safe review separates what the authority decided, the facts it relied on, the rules it cited, the relevant dates, and what evidence is still missing. Citations are now parsed through the GitLaw provider contract instead of treated as plain text.",
        official_route=str(source_ref("vwvfg").url), missing_evidence=missing,
        requires_human_approval=True, consequence="preparatory", priority=95, proof=proof
    )
    return CaseResult(
        case_id="decision-review", vertical="decision-review",
        summary=f"Decision structurally inspected; {len(citations)} citation(s) found and {len(resolved)} official route(s) resolved. No legal-validity conclusion was automated.",
        claims=claims, sources=[source_ref("vwvfg"), source_ref("gesetze_im_internet")], actions=[action],
        uncertainties=[
            "Sector-specific law, state law or special procedural rules may replace or supplement the general federal VwVfG.",
            "A resolved official section URL proves the citation can be located, not that it governs the concrete case.",
            "CivicOS does not infer an appeal deadline from generic rules; the concrete remedy route and service date must be verified.",
            "A draft response must be reviewed by the user or a qualified professional before external submission."
        ],
        audit=[{
            "step":"decision_structure_and_citation_verification_v2", "date_count":len(dates),
            "citation_count":len(citations), "resolved_official_routes":len(resolved),
            "gitlaw_lookup_required":len(unresolved)
        }]
    )
