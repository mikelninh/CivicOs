from __future__ import annotations
import re
from civicos.adapters.law import verify_many
from civicos.connectors.official import source_ref
from civicos.core.models import ActionRecommendation, CaseResult, Claim

DATE_RE = re.compile(r"\b(\d{1,2}\.\d{1,2}\.\d{4})\b")
LAW_RE = re.compile(r"(§{1,2}\s*\d+[a-zA-Z]?(?:\s*Abs\.\s*\d+)?(?:\s+(?:VwVfG|BGB|WoGG|SGB\s*[IVX]+))?)")
AUTHORITY_RE = re.compile(r"\b(Bezirksamt\s+[A-ZÄÖÜ][\wÄÖÜäöüß\- ]+|Jobcenter\s+[A-ZÄÖÜ][\wÄÖÜäöüß\- ]+|Familienkasse(?:\s+[\wÄÖÜäöüß\- ]+)?|Wohngeldstelle(?:\s+[\wÄÖÜäöüß\- ]+)?|Senatsverwaltung(?:\s+für\s+[\wÄÖÜäöüß\- ]+)?)", re.IGNORECASE)


def _decision_outcome(text: str) -> str | None:
    lower = text.lower()
    if any(term in lower for term in ("wird abgelehnt", "wird zurückgewiesen", "wird versagt")):
        return "rejected"
    if any(term in lower for term in ("wird bewilligt", "wird stattgegeben", "wird gewährt")):
        return "granted"
    if "aufgehoben" in lower:
        return "revoked/annulled"
    return None


def _factual_basis_signals(text: str) -> list[str]:
    normalized = " ".join(text.split())
    signals: list[str] = []
    for pattern in (
        r"[^.]{0,140}nicht vollständig[^.]{0,140}",
        r"[^.]{0,140}fehlt(?:en|e|)[^.]{0,140}",
        r"[^.]{0,140}nicht nachgewiesen[^.]{0,140}",
        r"[^.]{0,140}nicht erfüllt[^.]{0,140}",
    ):
        for match in re.finditer(pattern, normalized, flags=re.IGNORECASE):
            value = match.group(0).strip(" ;:")
            if value and value not in signals:
                signals.append(value)
            if len(signals) >= 5:
                return signals
    return signals


def attach_document_evidence(result: CaseResult, receipt_id: str) -> CaseResult:
    """Link structural claims derived from the uploaded decision to its exact hash receipt."""
    claims = []
    linked = 0
    for claim in result.claims:
        if claim.claim_id.startswith("decision:"):
            evidence_ids = list(dict.fromkeys(claim.evidence_ids + [receipt_id]))
            details = dict(claim.details)
            details["derived_from_user_document_receipt"] = receipt_id
            claims.append(claim.model_copy(update={"evidence_ids": evidence_ids, "details": details}))
            linked += 1
        else:
            claims.append(claim)
    return result.model_copy(update={
        "claims": claims,
        "audit": list(result.audit) + [{"step":"attach_user_document_evidence_v4","receipt_id":receipt_id,"claim_count":linked}],
    })


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
    outcome = _decision_outcome(text)
    authority_match = AUTHORITY_RE.search(text)
    authority = authority_match.group(1).strip() if authority_match else None
    factual_signals = _factual_basis_signals(text)

    claims = [
        Claim(claim_id="decision:outcome", text=f"Decision outcome detected: {outcome or 'unclear'}.", status="supported" if outcome else "unresolved", confidence=0.95 if outcome else 0.35, details={"outcome":outcome}),
        Claim(claim_id="decision:authority", text=f"Authority detected: {authority or 'not identified'}.", status="supported" if authority else "unresolved", confidence=0.9 if authority else 0.25, details={"authority":authority}),
        Claim(claim_id="decision:reasoning-present", text=f"Reasoning language detected: {has_reasoning}.", status="supported", confidence=1.0),
        Claim(claim_id="decision:factual-basis", text=f"Factual-basis signals extracted: {factual_signals or ['none']}.", status="supported" if factual_signals else "unresolved", confidence=0.9 if factual_signals else 0.3, details={"signals":factual_signals,"needs_independent_evidence":bool(factual_signals)}),
        Claim(claim_id="decision:remedy-language-present", text=f"Legal-remedy language detected: {has_remedy}.", status="supported", confidence=1.0),
        Claim(claim_id="decision:dates", text=f"Dates extracted: {dates or ['none']}.", status="supported", confidence=1.0),
        Claim(
            claim_id="decision:cited-provisions", text=f"Provision-like citations extracted: {citations or ['none']}.",
            status="supported", confidence=1.0,
            details={"checks": citation_checks, "provider":"mikelninh/gitlaw", "resolved_count":len(resolved), "unresolved_count":len(unresolved), "applicability_verified":False}
        )
    ]

    missing = []
    if not authority:
        missing.append("exact issuing authority / service")
    if not outcome:
        missing.append("clear operative decision / outcome")
    if not has_reasoning:
        missing.append("stated factual and legal reasons")
    if factual_signals:
        missing.append("evidence that supports or contradicts each factual basis asserted by the authority")
    else:
        missing.append("specific factual basis relied on by the authority")
    if not has_remedy:
        missing.append("legal-remedy instruction or sector-specific deadline basis")
    if not dates:
        missing.append("decision/service/receipt dates")
    if not citations:
        missing.append("cited legal provisions")
    if unresolved:
        missing.append("GitLaw section-level lookup for unresolved/ambiguous citations")

    proof = [
        f"outcome: {outcome or 'unclear'}",
        f"authority: {authority or 'not identified'}",
        f"{len(factual_signals)} factual-basis signal(s)",
        f"{len(dates)} date(s) extracted",
        f"{len(citations)} citation(s) extracted",
        f"{len(resolved)} official section route(s) deterministically resolved",
    ]
    action = ActionRecommendation(
        action_id="prepare:decision-review", title="Close the highest-impact evidence gap before responding",
        why="CivicOS separates the operative decision, issuing authority, factual basis, cited rules, dates and remedy information. The safest next move is to verify the first missing link rather than drafting around an unverified assumption.",
        official_route=str(source_ref("vwvfg").url), missing_evidence=missing,
        requires_human_approval=True, consequence="preparatory", priority=96, proof=proof
    )

    graph = {
        "type":"decision_review_chain_v4",
        "nodes":[
            {"id":"decision","type":"Decision","status":"known" if outcome else "incomplete","value":outcome},
            {"id":"authority","type":"Authority","status":"known" if authority else "missing","value":authority},
            {"id":"facts","type":"FactualBasis","status":"extracted" if factual_signals else "missing","count":len(factual_signals)},
            {"id":"rules","type":"Rules","status":"partially_verified" if resolved else "unresolved","resolved":len(resolved),"total":len(citations)},
            {"id":"dates","type":"Dates","status":"extracted" if dates else "missing","count":len(dates)},
            {"id":"remedy","type":"Remedy","status":"language_present" if has_remedy else "missing"},
            {"id":"response","type":"Action","status":"human_review_required"},
        ],
        "edges":[
            {"from":"authority","to":"decision","relation":"ISSUED"},
            {"from":"decision","to":"facts","relation":"RELIES_ON"},
            {"from":"decision","to":"rules","relation":"CITES"},
            {"from":"decision","to":"dates","relation":"HAS_DATES"},
            {"from":"decision","to":"remedy","relation":"HAS_REMEDY_PATH"},
            {"from":"decision","to":"response","relation":"CAN_BE_REVIEWED_BY"},
        ],
    }

    return CaseResult(
        case_id="decision-review", vertical="decision-review",
        summary=f"Decision decomposed into outcome, authority, facts, rules, dates and remedy path; {len(missing)} evidence gap(s) remain. No legal-validity conclusion was automated.",
        claims=claims, sources=[source_ref("vwvfg"), source_ref("gesetze_im_internet")], actions=[action], graph=graph,
        uncertainties=[
            "Sector-specific law, state law or special procedural rules may replace or supplement the general federal VwVfG.",
            "A resolved official section URL proves the citation can be located, not that it governs the concrete case.",
            "Factual assertions in the decision are claims by the authority until supporting/counter-evidence is checked.",
            "CivicOS does not infer an appeal deadline from generic rules; the concrete remedy route and service date must be verified.",
            "A draft response must be reviewed by the user or a qualified professional before external submission."
        ],
        audit=[{
            "step":"decision_claim_graph_v4", "outcome":outcome, "authority":authority, "factual_basis_count":len(factual_signals),
            "date_count":len(dates), "citation_count":len(citations), "resolved_official_routes":len(resolved),
            "gitlaw_lookup_required":len(unresolved), "missing_evidence_count":len(missing)
        }]
    )
