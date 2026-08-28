from __future__ import annotations
from typing import Any
from civicos.connectors.official import source_ref
from civicos.core.models import CalculatorPlan


def _present(payload: dict[str, Any], fields: list[str]) -> tuple[list[str], list[str]]:
    supplied, missing = [], []
    for field in fields:
        if payload.get(field) in (None, "", []):
            missing.append(field)
        else:
            supplied.append(field)
    return supplied, missing


def build_calculator_plans(household: dict[str, Any]) -> list[CalculatorPlan]:
    """Prepare deterministic input/readiness plans for official tools.

    CivicOS does not automate browser submission here and never promotes its own
    heuristic to an official entitlement result. The plan tells the user which
    authoritative tool to use, whether the minimum known inputs are present, and
    which bounded preview CivicOS itself can safely compute.
    """
    plans: list[CalculatorPlan] = []

    if household.get("location") == "Berlin":
        supplied, missing = _present(household, ["household_size", "monthly_household_income", "monthly_rent"])
        plans.append(CalculatorPlan(
            benefit="Wohngeld",
            tool_name="Berlin Wohngeldrechner / federal fallback",
            official_route=str(source_ref("berlin_wohngeldrechner").url),
            state="temporarily_unavailable" if not missing else "missing_inputs",
            supplied_inputs=supplied,
            missing_inputs=missing,
            result_scope="official non-binding eligibility/amount orientation outside CivicOS",
            note="The Berlin source currently reports that its calculator is under technical revision and points users to the federal calculator. CivicOS prepares inputs but does not invent a substitute amount.",
            deterministic_preview={"rent_to_income_ratio": round(float(household.get("monthly_rent", 0)) / float(household.get("monthly_household_income", 1)), 3) if household.get("monthly_rent") and household.get("monthly_household_income") else None},
        ))

    if int(household.get("children", 0) or 0) > 0:
        supplied, missing = _present(household, ["children", "monthly_household_income", "housing_costs", "kindergeld_status"])
        plans.append(CalculatorPlan(
            benefit="Kinderzuschlag",
            tool_name="KiZ-Lotse",
            official_route=str(source_ref("arbeitsagentur_kiz_lotse").url),
            state="official_tool_only" if not missing else "missing_inputs",
            supplied_inputs=supplied,
            missing_inputs=missing,
            result_scope="official pre-check of whether entitlement could exist; not payment amount",
            note="The Bundesagentur für Arbeit states that the KiZ-Lotse does not calculate the amount of Kinderzuschlag.",
        ))

    if household.get("youngest_child_age_months") is not None:
        supplied, missing = _present(household, ["pre_birth_income", "youngest_child_age_months"])
        plans.append(CalculatorPlan(
            benefit="Elterngeld",
            tool_name="Elterngeldrechner",
            official_route=str(source_ref("familienportal_elterngeld_calculator").url),
            state="ready" if not missing else "missing_inputs",
            supplied_inputs=supplied,
            missing_inputs=missing,
            result_scope="official non-binding estimate and planning result",
            note="The Familienportal states that the calculator result is orientation; the Elterngeldstelle determines the actual amount.",
        ))

    if bool(household.get("single_parent")) and int(household.get("children", 0) or 0) > 0:
        supplied, missing = _present(household, ["child_ages", "child_support_status"])
        ages = [int(x) for x in household.get("child_ages", []) if isinstance(x, (int, float))]
        plans.append(CalculatorPlan(
            benefit="Unterhaltsvorschuss",
            tool_name="CivicOS bounded age-band preview + official application route",
            official_route=str(source_ref("familienportal_unterhaltsvorschuss").url),
            state="guidance_only" if not missing else "missing_inputs",
            supplied_inputs=supplied,
            missing_inputs=missing,
            result_scope="bounded current age-band preview before reductions/eligibility checks",
            note="No entitlement conclusion is produced. Reductions and additional conditions remain outside the preview.",
            deterministic_preview={"child_ages": ages},
        ))

    return plans
