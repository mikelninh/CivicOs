from __future__ import annotations
from collections import Counter
from typing import Any
import re
from civicos.connectors.official import source_ref
from civicos.core.models import ActionRecommendation, CaseResult, Claim

def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower().replace("gmbh","").replace("ag","").replace("ug",""))

def analyse_awards(awards: list[dict[str, Any]]) -> CaseResult:
    by_vendor = Counter(_norm(str(row.get("vendor",""))) for row in awards if row.get("vendor"))
    repeated = [(v,c) for v,c in by_vendor.most_common() if c > 1]
    claims = [Claim(claim_id=f"pattern:{vendor}",text=f"Normalised vendor '{vendor}' appears in {count} supplied award records.",status="supported",confidence=1.0) for vendor,count in repeated]
    if repeated:
        action = ActionRecommendation(action_id="verify:repeat-awards",title="Verify the repeated-award pattern against primary notices",why="Repeated awards are an observable pattern, but context and entity identity must be verified before drawing any inference.",official_route=str(source_ref("berlin_procurement_awards").url),missing_evidence=["primary award notices","stable organisation identifiers","procedure context","award values if absent"],requires_human_approval=False,consequence="informational")
    else:
        action = ActionRecommendation(action_id="ingest:award-records",title="Load award records from the official publication route",why="There is not enough supplied evidence to test concentration or relationship patterns.",official_route=str(source_ref("berlin_procurement_awards").url),missing_evidence=["award records"],requires_human_approval=False,consequence="informational")
    return CaseResult(case_id="public-money-graph",vertical="public-money",summary=f"Analysed {len(awards)} supplied award records; {len(repeated)} normalised vendor(s) repeat.",claims=claims,sources=[source_ref("berlin_procurement_awards"),source_ref("bundeshaushalt"),source_ref("bundesrechnungshof"),source_ref("unternehmensregister")],actions=[action],uncertainties=["Name normalisation is not legal-entity resolution.","Repeated awards, shared addresses or other links are leads, not evidence of corruption or misconduct.","Recipient-level payment evidence is distinct from budget appropriations and award notices."],audit=[{"step":"award_pattern_analysis","rows":len(awards),"repeated_vendors":len(repeated)}])
