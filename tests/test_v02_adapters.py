import json
from pathlib import Path

from civicos.adapters.entity_resolution import resolve_pair
from civicos.adapters.law import verify_citation
from civicos.verticals.benefits import analyse_benefits
from civicos.verticals.decision_review import review_decision
from civicos.verticals.public_money import analyse_awards

ROOT = Path(__file__).resolve().parents[1]


def test_entity_resolution_exposes_receipts_and_auto_merge():
    left = {"record_id":"a","name":"Nordlicht Daten GmbH","address":"Karl-Marx-Allee 88, 10243 Berlin","domain":"nordlicht-daten.de","directors":["Lea Winter"],"source":"one"}
    right = {"record_id":"b","name":"NORDLICHT DATEN","address":"Karl Marx Allee 88 10243 Berlin","domain":"www.nordlicht-daten.de","directors":["L. Winter"],"source":"two"}
    result = resolve_pair(left, right)
    assert result.decision == "auto_merge"
    assert result.relation == "SAME_AS"
    assert result.evidence["exact_domain"] is True
    assert result.evidence["postcode_match"] is True


def test_entity_resolution_does_not_merge_related_looking_company():
    left = {"record_id":"a","name":"Nordlicht Daten GmbH","address":"Karl-Marx-Allee 88, 10243 Berlin","domain":"nordlicht-daten.de","directors":["Lea Winter"]}
    right = {"record_id":"b","name":"Nordlicht Solar Solutions GmbH","address":"Karl-Marx-Allee 88, 10243 Berlin","domain":"nordlicht-solar.de","directors":["Lea Winter"]}
    result = resolve_pair(left, right)
    assert result.decision != "auto_merge"


def test_gitlaw_adapter_resolves_known_official_section_route():
    result = verify_citation("§ 39 VwVfG")
    assert result.syntax_valid
    assert result.law_code == "VwVfG"
    assert result.official_url.endswith("/vwvfg/__39.html")
    assert result.verification == "official_route_resolved"


def test_benefits_v2_prioritises_actionable_single_parent_checks():
    household = json.loads((ROOT / "examples" / "benefits_household.json").read_text())
    result = analyse_benefits(household)
    assert result.actions == sorted(result.actions, key=lambda a: a.priority, reverse=True)
    assert any(a.action_id == "check:unterhaltsvorschuss" for a in result.actions)
    assert any(a.action_id == "check:kinderzuschlag" and a.estimated_support for a in result.actions)
    assert any(a.action_id == "check:bildung-teilhabe" for a in result.actions)
    assert "not entitlement" in " ".join(result.uncertainties).lower()


def test_public_money_uses_entity_resolution_not_only_name_key():
    awards = json.loads((ROOT / "examples" / "public_money_awards.json").read_text())
    result = analyse_awards(awards)
    assert any(c.details.get("relation") == "SAME_AS" for c in result.claims)
    assert result.audit[0]["entity_provider"] == "SafeTrace Entity Resolution"


def test_decision_review_runs_citation_checks():
    text = (ROOT / "examples" / "decision.txt").read_text()
    result = review_decision(text)
    citation_claim = next(c for c in result.claims if c.claim_id == "decision:cited-provisions")
    assert citation_claim.details["resolved_count"] >= 1
    assert citation_claim.details["provider"] == "mikelninh/gitlaw"
