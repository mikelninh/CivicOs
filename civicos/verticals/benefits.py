from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from civicos.connectors.official import source_ref
from civicos.core.models import ActionRecommendation, CaseResult, Claim

ROOT = Path(__file__).resolve().parents[2]
RULE_PACK = json.loads((ROOT / "data" / "benefit_rules_2026.json").read_text(encoding="utf-8"))
RULES = RULE_PACK["rules"]

QUALIFYING_BUT = {"Kinderzuschlag", "Bürgergeld", "Sozialgeld", "Sozialhilfe", "Wohngeld", "AsylbLG"}
HOUSING_TRANSFER_EXCLUSIONS = {"buergergeld", "bürgergeld", "grundsicherung", "sozialhilfe", "hilfe_zum_lebensunterhalt", "youth_welfare_housing"}


def _missing(h: dict[str, Any], fields: list[str]) -> list[str]:
    return [field for field in fields if h.get(field) in (None, "", [])]


def _rent_burden(h: dict[str, Any]) -> float | None:
    income, rent = h.get("monthly_household_income"), h.get("monthly_rent") or h.get("housing_costs")
    if isinstance(income, (int, float)) and income > 0 and isinstance(rent, (int, float)):
        return round(float(rent) / float(income), 3)
    return None


def _uv_estimate(child_ages: list[int]) -> int:
    amounts = RULES["unterhaltsvorschuss"]["monthly_eur_by_age"]
    total = 0
    for age in child_ages:
        if age <= 5:
            total += amounts["0-5"]
        elif age <= 11:
            total += amounts["6-11"]
        elif age <= 17:
            total += amounts["12-17"]
    return total


def analyse_benefits(household: dict[str, Any]) -> CaseResult:
    claims: list[Claim] = []
    actions: list[ActionRecommendation] = []
    sources, seen_sources = [], set()
    burden = _rent_burden(household)
    children = int(household.get("children", 0) or 0)
    benefits_received = set(household.get("benefits_received", []))

    def add_sources(*ids: str) -> None:
        for source_id in ids:
            if source_id not in seen_sources:
                sources.append(source_ref(source_id)); seen_sources.add(source_id)

    # Wohngeld: rank strongly when housing burden is meaningful, but surface known transfer-benefit exclusions.
    if household.get("location") == "Berlin" and (household.get("monthly_rent") or household.get("housing_costs")):
        missing = _missing(household, ["household_size", "monthly_household_income", "monthly_rent", "housing_transfer_benefit_status"])
        transfer_status = str(household.get("housing_transfer_benefit_status", "none")).lower()
        excluded_signal = transfer_status in HOUSING_TRANSFER_EXCLUSIONS
        priority = 82 + (8 if burden is not None and burden >= 0.35 else 0) - 6 * len(missing) - (35 if excluded_signal else 0)
        claims.append(Claim(
            claim_id="benefit:wohngeld",
            text="Wohngeld is worth an official check based on Berlin residence and housing costs." if not excluded_signal else "The supplied transfer-benefit status may exclude Wohngeld because housing costs may already be covered; verify the exact status.",
            status="unresolved", confidence=max(0.35, min(0.9, priority / 100)),
            details={"rent_to_income_ratio": burden, "possible_exclusion_signal": excluded_signal}
        ))
        actions.append(ActionRecommendation(
            action_id="check:wohngeld", title="Check Wohngeld first" if priority >= 80 else "Verify Wohngeld eligibility",
            why="Berlin's official service says household size, eligible rent and household income drive the calculation; certain transfer benefits can exclude Wohngeld.",
            official_route=str(source_ref("berlin_wohngeld").url), missing_evidence=missing,
            requires_human_approval=False, consequence="informational", priority=max(0, min(100, priority)),
            proof=["Berlin residence", f"rent/income ratio: {burden}" if burden is not None else "housing costs supplied", "official Wohngeld calculator route"]
        ))
        add_sources("berlin_wohngeld")

    # Kinderzuschlag: current maximum is useful for prioritisation, never treated as expected payout.
    if children > 0:
        missing = _missing(household, ["monthly_household_income", "housing_costs", "kindergeld_status", "assets_status"])
        kindergeld = str(household.get("kindergeld_status", "")).lower() in {"received", "yes", "true"}
        priority = 76 + (8 if kindergeld else 0) - 5 * len(missing)
        max_total = RULES["kinderzuschlag"]["max_monthly_per_child_eur"] * children
        claims.append(Claim(
            claim_id="benefit:kinderzuschlag",
            text="Kinderzuschlag is worth checking; current official guidance states a maximum of €297 per child per month, but the actual amount is case-specific.",
            status="unresolved", confidence=max(0.35, min(0.9, priority / 100)),
            details={"children": children, "current_max_per_child_eur": 297, "max_total_if_fully_eligible_eur": max_total}
        ))
        actions.append(ActionRecommendation(
            action_id="check:kinderzuschlag", title="Run the official Kinderzuschlag check",
            why="Children plus household income/housing costs make KiZ a high-value check; the official amount is calculated per child and depends on household circumstances.",
            official_route=str(source_ref("familienportal_kiz").url), missing_evidence=missing,
            requires_human_approval=False, consequence="informational", priority=max(0, min(100, priority)),
            estimated_support=f"up to €{max_total}/month across {children} child(ren), not an entitlement estimate",
            proof=["children in household", "current official maximum €297/child/month", "official eligibility/application route"]
        ))
        add_sources("familienportal_kiz", "arbeitsagentur_kiz")

    # Unterhaltsvorschuss: one of the most actionable checks for single parents with missing/irregular support.
    if bool(household.get("single_parent")) and children > 0 and household.get("child_support_status") in {None, "none", "irregular", "below_advance"}:
        missing = _missing(household, ["child_ages", "child_support_status", "cohabitation_with_other_parent", "marital_status"])
        ages = [int(x) for x in household.get("child_ages", []) if isinstance(x, (int, float))]
        max_total = _uv_estimate(ages) if ages else 0
        priority = 90 - 5 * len(missing)
        actions.append(ActionRecommendation(
            action_id="check:unterhaltsvorschuss", title="Check Unterhaltsvorschuss",
            why="Single-parent households where child support is missing or irregular have a direct official route worth checking promptly.",
            official_route=str(source_ref("familienportal_unterhaltsvorschuss").url), missing_evidence=missing,
            requires_human_approval=False, consequence="informational", priority=max(0, min(100, priority)),
            estimated_support=(f"up to €{max_total}/month across supplied child ages before reductions" if max_total else "official age-based amount requires child ages"),
            proof=["single-parent signal", f"child support status: {household.get('child_support_status')}", "official age-based amounts"]
        ))
        claims.append(Claim(claim_id="benefit:unterhaltsvorschuss", text="Unterhaltsvorschuss is a high-priority official check given the supplied single-parent and child-support facts.", status="unresolved", confidence=max(0.4, min(0.92, priority / 100)), details={"age_based_max_total_eur": max_total or None}))
        add_sources("familienportal_unterhaltsvorschuss")

    # Elterngeld: only surface when a child is within the current possible benefit window.
    youngest = household.get("youngest_child_age_months")
    if youngest is not None and int(youngest) <= 32:
        missing = _missing(household, ["youngest_child_age_months", "hours_worked_weekly", "taxable_annual_income", "pre_birth_income"])
        hours = household.get("hours_worked_weekly")
        taxable = household.get("taxable_annual_income")
        hours_block = isinstance(hours, (int, float)) and hours > RULES["elterngeld"]["max_weekly_work_hours"]
        income_block = isinstance(taxable, (int, float)) and taxable > RULES["elterngeld"]["taxable_income_ceiling_eur"]
        priority = 78 - 5 * len(missing) - (45 if hours_block or income_block else 0)
        claims.append(Claim(
            claim_id="benefit:elterngeld", text="Elterngeld is within the possible age window, but current work-hours and taxable-income conditions must be checked.",
            status="unresolved", confidence=max(0.3, min(0.88, priority / 100)),
            details={"hours_over_current_limit": hours_block, "income_over_current_ceiling": income_block, "youngest_child_age_months": youngest}
        ))
        actions.append(ActionRecommendation(
            action_id="check:elterngeld", title="Check Elterngeld / ElterngeldPlus",
            why="Current official rules include a 32-hour weekly-work condition and a €175,000 taxable-income ceiling for births from 1 April 2025; exact amount depends on income and benefit variant.",
            official_route=str(source_ref("familienportal_elterngeld").url), missing_evidence=missing,
            requires_human_approval=False, consequence="informational", priority=max(0, min(100, priority)),
            estimated_support="Basiselterngeld €300–€1,800/month; ElterngeldPlus €150–€900/month before case-specific calculation",
            proof=["child age within possible current benefit window", "current 32-hour work condition", "current €175k taxable-income ceiling"]
        ))
        add_sources("familienportal_elterngeld", "familienportal_elterngeld_amount", "familienportal_elterngeld_eligibility")

    # Bildung & Teilhabe: direct if already on a qualifying benefit; otherwise show downstream unlock from KiZ/Wohngeld.
    qualifies_now = bool(benefits_received & QUALIFYING_BUT)
    downstream = children > 0 and any(a.action_id in {"check:kinderzuschlag", "check:wohngeld"} for a in actions)
    if children > 0 and (qualifies_now or downstream):
        missing = _missing(household, ["child_ages", "school_or_kita_status", "benefits_received"])
        priority = 74 if qualifies_now else 54
        actions.append(ActionRecommendation(
            action_id="check:bildung-teilhabe", title="Check Bildung & Teilhabe" if qualifies_now else "If KiZ/Wohngeld is granted, unlock Bildung & Teilhabe",
            why="Berlin links education/participation support to qualifying benefits. For Wohngeld/KiZ recipients, an application route is provided.",
            official_route=str(source_ref("berlin_but_service").url), missing_evidence=missing,
            requires_human_approval=False, consequence="informational", priority=priority,
            estimated_support="includes school meals, activities and €195 school-supplies support under current Berlin guidance",
            proof=["children in household", "qualifying benefit or downstream KiZ/Wohngeld route", "official Berlin service route"]
        ))
        add_sources("berlin_but", "berlin_but_service")

    actions.sort(key=lambda action: action.priority, reverse=True)
    if not actions:
        actions.append(ActionRecommendation(
            action_id="collect:minimal-household-facts", title="Add the minimum household facts",
            why="CivicOS cannot responsibly rank support checks without basic household, child, housing and income context.",
            missing_evidence=["location", "children", "household_size", "monthly_household_income", "monthly_rent"],
            requires_human_approval=False, consequence="informational", priority=100
        ))

    return CaseResult(
        case_id="benefits-graph", vertical="benefits",
        summary=f"{len(actions)} next-step route(s) ranked from the supplied facts; top action: {actions[0].title}.",
        claims=claims, sources=sources, actions=actions,
        uncertainties=[
            "Rankings are triage, not entitlement decisions or guaranteed payment estimates.",
            f"Numeric rule snapshot was verified on {RULE_PACK['version']}; current runs should refresh official sources before consequential use.",
            "Exact Wohngeld and Kinderzuschlag calculations should use current official calculators/rules rather than heuristic inference."
        ],
        audit=[{"step":"benefit_candidate_ranking_v2","action_count":len(actions),"rent_to_income_ratio":burden,"rule_pack":RULE_PACK["version"]}]
    )
