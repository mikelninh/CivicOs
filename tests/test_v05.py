from civicos.core.models import EvidenceFact
from civicos.core.source_change import evaluate_source_change
from civicos.engine import run
from civicos.verticals.payment_reconciliation import reconcile_awards_and_payments


def _fact(value: int, receipt: str = "receipt:old") -> EvidenceFact:
    return EvidenceFact(
        fact_id="kiz:max-per-child",
        claim_id="benefit:kinderzuschlag",
        source_id="arbeitsagentur_kiz",
        receipt_id=receipt,
        label="Kinderzuschlag maximum per child/month",
        value=value,
    )


def test_source_fact_change_propagates_to_claims_and_golden_cases():
    impact = evaluate_source_change(
        "arbeitsagentur_kiz",
        previous_sha256="old",
        current_sha256="new",
        previous_facts=[_fact(297)],
        current_facts=[_fact(305, "receipt:new")],
    )
    assert impact.state == "fact_changed"
    assert "kiz:max-per-child" in impact.changed_fact_ids
    assert "benefit:kinderzuschlag" in impact.affected_claim_ids
    assert "citizen-benefits-gap" in impact.affected_golden_case_ids
    assert impact.regression_fixture["expected"]["human_review_required"] is True


def test_source_content_change_without_fact_delta_does_not_fake_fact_change():
    impact = evaluate_source_change(
        "arbeitsagentur_kiz",
        previous_sha256="old",
        current_sha256="new",
        previous_facts=[_fact(297)],
        current_facts=[_fact(297, "receipt:new")],
    )
    assert impact.state == "content_changed"
    assert not impact.changed_fact_ids
    assert impact.affected_golden_case_ids == ["citizen-benefits-gap"]


def test_benefits_run_exposes_official_calculator_plans_without_invented_result():
    result = run("benefits", {
        "location":"Berlin",
        "children":2,
        "child_ages":[5,9],
        "household_size":3,
        "monthly_household_income":2000,
        "monthly_rent":1100,
        "housing_costs":1100,
        "single_parent":True,
        "child_support_status":"irregular",
        "kindergeld_status":"received",
    })
    tools = {plan.benefit: plan for plan in result.calculators}
    assert tools["Wohngeld"].state == "temporarily_unavailable"
    assert tools["Kinderzuschlag"].state == "official_tool_only"
    assert tools["Kinderzuschlag"].deterministic_preview == {}
    assert any(source.source_id == "arbeitsagentur_kiz_lotse" for source in result.sources)


def test_payment_reconciliation_requires_reference_and_entity_match():
    award = {
        "award_id":"A-42", "vendor":"Nordlicht Daten GmbH", "value_eur":120000,
        "vendor_record":{"record_id":"vendor-1","name":"Nordlicht Daten GmbH","address":"Karl-Marx-Allee 88, 10243 Berlin","domain":"nordlicht-daten.de","directors":["Lea Winter"]},
    }
    payment = {
        "payment_id":"P-1", "award_id":"A-42", "recipient":"Nordlicht Daten GmbH", "amount_eur":60000,
        "recipient_record":{"record_id":"recipient-1","name":"Nordlicht Daten GmbH","address":"Karl-Marx-Allee 88, 10243 Berlin","domain":"nordlicht-daten.de","directors":["Lea Winter"]},
    }
    result = reconcile_awards_and_payments([award], [payment])
    assert result.graph["stages"][2]["confirmed_reconciliations"] == 1
    assert any(claim.claim_id.startswith("payment-reconciliation:") for claim in result.claims)


def test_same_amount_alone_never_confirms_payment_link():
    award = {
        "award_id":"A-42", "vendor":"North GmbH", "value_eur":50000,
        "vendor_record":{"record_id":"vendor-1","name":"North GmbH","address":"A Street 1, Berlin","domain":"north.example","directors":["A Person"]},
    }
    payment = {
        "payment_id":"P-9", "recipient":"Other GmbH", "amount_eur":50000,
        "recipient_record":{"record_id":"recipient-9","name":"Other GmbH","address":"B Street 2, Berlin","domain":"other.example","directors":["B Person"]},
    }
    result = reconcile_awards_and_payments([award], [payment])
    assert result.graph["stages"][2]["confirmed_reconciliations"] == 0
    assert "P-9" in result.graph["reconciliations"]["unmatched_payment_ids"]
