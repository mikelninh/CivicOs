from __future__ import annotations
from typing import Any
from civicos.connectors.official import source_ref
from civicos.core.models import ActionRecommendation, CaseResult, Claim

PROGRAMS = [
    {"id":"wohngeld","label":"Wohngeld","source":"berlin_wohngeld","when":lambda h: h.get("location") == "Berlin" and bool(h.get("monthly_rent")),"missing":["household_size","monthly_household_income","monthly_rent","housing_transfer_benefit_status"],"why":"Housing costs plus household income/size determine whether an official Wohngeld check is useful."},
    {"id":"kinderzuschlag","label":"Kinderzuschlag","source":"familienportal_kiz","when":lambda h: int(h.get("children",0)) > 0,"missing":["monthly_household_income","housing_costs","kindergeld_status","assets_status"],"why":"Families with children and limited income may need a Kinderzuschlag pre-check."},
    {"id":"elterngeld","label":"Elterngeld","source":"familienportal_elterngeld","when":lambda h: h.get("youngest_child_age_months") is not None and int(h["youngest_child_age_months"]) <= 36,"missing":["youngest_child_age_months","hours_worked_weekly","taxable_annual_income","pre_birth_income"],"why":"A recent birth can make Elterngeld or ElterngeldPlus worth checking against current official rules."},
    {"id":"unterhaltsvorschuss","label":"Unterhaltsvorschuss","source":"familienportal_unterhaltsvorschuss","when":lambda h: bool(h.get("single_parent")) and int(h.get("children",0)) > 0 and h.get("child_support_status") in {None,"none","irregular","below_advance"},"missing":["child_ages","child_support_status","cohabitation_with_other_parent","marital_status"],"why":"Single-parent households with missing or irregular child support should check the official advance route."},
    {"id":"bildung_teilhabe","label":"Bildung & Teilhabe","source":"berlin_but","when":lambda h: int(h.get("children",0)) > 0 and bool(set(h.get("benefits_received",[])) & {"Kinderzuschlag","Bürgergeld","Sozialgeld","Sozialhilfe","Wohngeld","AsylbLG"}),"missing":["child_ages","school_or_kita_status","benefits_received"],"why":"Children in households receiving qualifying benefits can have additional education and participation support."}
]

def analyse_benefits(household: dict[str, Any]) -> CaseResult:
    candidates = [p for p in PROGRAMS if p["when"](household)]
    claims, actions, sources, seen_sources = [], [], [], set()
    for p in candidates:
        missing = [field for field in p["missing"] if household.get(field) in (None,"",[])]
        claims.append(Claim(claim_id=f"benefit:{p['id']}",text=f"{p['label']} is worth checking; this is not an eligibility determination.",status="unresolved",confidence=max(0.35,0.76 - 0.05 * len(missing))))
        actions.append(ActionRecommendation(action_id=f"check:{p['id']}",title=f"Check {p['label']}",why=p["why"],official_route=str(source_ref(p["source"]).url),missing_evidence=missing,requires_human_approval=False,consequence="informational"))
        if p["source"] not in seen_sources:
            sources.append(source_ref(p["source"])); seen_sources.add(p["source"])
    if not actions:
        actions.append(ActionRecommendation(action_id="collect:minimal-household-facts",title="Add the minimum household facts",why="CivicOS cannot responsibly rank support checks without basic household, child, housing and income context.",missing_evidence=["location","children","household_size","monthly_household_income","monthly_rent"],requires_human_approval=False,consequence="informational"))
    return CaseResult(case_id="benefits-graph",vertical="benefits",summary=f"{len(candidates)} support route(s) are worth checking based on the facts provided.",claims=claims,sources=sources,actions=actions,uncertainties=["Candidate routes are hypotheses until current official rules and complete household facts are checked."],audit=[{"step":"benefit_candidate_ranking","candidate_count":len(candidates)}])
