from civicos.connectors.official import source_ref
from civicos.core.evidence import make_receipt
from civicos.core.live_evidence import refresh_case_sources
from civicos.core.models import CaseResult, Claim
from civicos.core.source_evidence import extract_live_facts
from civicos.verticals.decision_review import attach_document_evidence, review_decision
from civicos.verticals.public_money import analyse_awards


def test_live_fact_is_linked_to_claim(monkeypatch):
    result = CaseResult(
        case_id="kiz-test",
        vertical="benefits",
        summary="test",
        claims=[Claim(claim_id="benefit:kinderzuschlag", text="KiZ max signal", status="unresolved", confidence=0.5)],
        sources=[source_ref("arbeitsagentur_kiz")],
    )

    def fake_fetch(source_id: str):
        body = b"<html><body>Kinderzuschlag: bis zu 297 Euro pro Kind und Monat.</body></html>"
        return make_receipt(source_id, body, content_type="text/html"), body

    monkeypatch.setattr("civicos.core.live_evidence.fetch_official", fake_fetch)
    refreshed = refresh_case_sources(result)
    assert refreshed.freshness["all_sources_live"] is True
    assert refreshed.freshness["verified_fact_count"] == 1
    assert refreshed.evidence_facts[0].fact_id == "kiz:max-per-child"
    assert refreshed.evidence_facts[0].value == 297
    assert refreshed.evidence_excerpts
    assert refreshed.evidence_receipts[0].receipt_id in refreshed.claims[0].evidence_ids
    assert "kiz:max-per-child" in refreshed.claims[0].details["live_verified_facts"]


def test_live_fetch_does_not_verify_fact_when_pattern_missing():
    body = b"<html><body>Kinderzuschlag information without the declared amount.</body></html>"
    receipt = make_receipt("arbeitsagentur_kiz", body, content_type="text/html")
    excerpts, facts = extract_live_facts("arbeitsagentur_kiz", body, receipt.receipt_id)
    assert excerpts == []
    assert facts == []


def test_decision_review_builds_claim_graph_and_document_links():
    text = (
        "Wohngeldstelle Berlin\nBescheid vom 20.08.2026. "
        "Ihr Antrag wird abgelehnt. Begründung: Die Unterlagen sind nicht vollständig. "
        "§ 39 VwVfG. Rechtsbehelfsbelehrung."
    )
    result = review_decision(text)
    assert result.graph["type"] == "decision_review_chain_v4"
    assert any(node["id"] == "facts" and node["status"] == "extracted" for node in result.graph["nodes"])
    assert any("supports or contradicts" in item for item in result.actions[0].missing_evidence)
    linked = attach_document_evidence(result, "user-decision-document:abc123")
    decision_claims = [claim for claim in linked.claims if claim.claim_id.startswith("decision:")]
    assert decision_claims
    assert all("user-decision-document:abc123" in claim.evidence_ids for claim in decision_claims)


def test_public_money_graph_exposes_payment_bottleneck():
    awards = [
        {"vendor":"Nordlicht Daten GmbH", "vendor_record":{"record_id":"a","name":"Nordlicht Daten GmbH","address":"Karl-Marx-Allee 88, 10243 Berlin","domain":"nordlicht.de","directors":["Lea Winter"]}},
        {"vendor":"Nordlicht Daten", "vendor_record":{"record_id":"b","name":"Nordlicht Daten","address":"Karl Marx Allee 88 10243 Berlin","domain":"www.nordlicht.de","directors":["L. Winter"]}},
    ]
    result = analyse_awards(awards)
    assert result.graph["type"] == "public_money_chain_v4"
    payment = next(stage for stage in result.graph["stages"] if stage["id"] == "payment")
    assert payment["status"] == "missing"
    assert result.graph["evidence_completeness"]["bottleneck"] == "payment"
    assert result.actions[0].action_id == "close:payment-gap"
    combined = " ".join([result.summary, *[claim.text for claim in result.claims], *result.uncertainties]).lower()
    assert "finding of corruption" in combined or "not findings of corruption" in combined
