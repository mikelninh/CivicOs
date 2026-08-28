from __future__ import annotations
import re
from civicos.connectors.official import source_ref
from civicos.core.models import ActionRecommendation, CaseResult, Claim

DATE_RE = re.compile(r"\b(\d{1,2}\.\d{1,2}\.\d{4})\b")
LAW_RE = re.compile(r"(§{1,2}\s*\d+[a-zA-Z]?(?:\s*Abs\.\s*\d+)?)")

def review_decision(text: str) -> CaseResult:
    dates = sorted(set(DATE_RE.findall(text)))
    laws = sorted(set(m.group(1) for m in LAW_RE.finditer(text)))
    has_reasoning = "begründ" in text.lower()
    has_remedy = "rechtsbehelf" in text.lower() or "widerspruch" in text.lower()
    claims = [Claim(claim_id="decision:reasoning-present",text=f"Reasoning language detected: {has_reasoning}.",status="supported",confidence=1.0),Claim(claim_id="decision:remedy-language-present",text=f"Legal-remedy language detected: {has_remedy}.",status="supported",confidence=1.0),Claim(claim_id="decision:dates",text=f"Dates extracted: {dates or ['none']}.",status="supported",confidence=1.0),Claim(claim_id="decision:cited-provisions",text=f"Provision-like citations extracted: {laws or ['none']}.",status="supported",confidence=1.0)]
    missing = []
    if not has_reasoning: missing.append("stated factual and legal reasons")
    if not has_remedy: missing.append("legal-remedy instruction or sector-specific deadline basis")
    if not dates: missing.append("decision/service/receipt dates")
    if not laws: missing.append("cited legal provisions")
    action = ActionRecommendation(action_id="prepare:decision-review",title="Prepare a review checklist before responding",why="A safe review separates what the authority decided, the facts it relied on, the rules it cited, the relevant dates, and what evidence is still missing.",official_route=str(source_ref("vwvfg").url),missing_evidence=missing,requires_human_approval=True,consequence="preparatory")
    return CaseResult(case_id="decision-review",vertical="decision-review",summary="Administrative decision text was structurally inspected; no legal-validity conclusion was automated.",claims=claims,sources=[source_ref("vwvfg"),source_ref("gesetze_im_internet")],actions=[action],uncertainties=["Sector-specific law, state law or special procedural rules may replace or supplement the general federal VwVfG.","CivicOS does not infer an appeal deadline from generic rules; the concrete remedy route and service date must be verified.","A draft response must be reviewed by the user or a qualified professional before external submission."],audit=[{"step":"decision_structure_extraction","date_count":len(dates),"citation_count":len(laws)}])
