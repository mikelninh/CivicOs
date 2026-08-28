import json
from pathlib import Path
from civicos.verticals.benefits import analyse_benefits
from civicos.verticals.public_money import analyse_awards
from civicos.verticals.decision_review import review_decision
from civicos.connectors.official import get_source, SourceError

ROOT = Path(__file__).resolve().parents[1]

def test_benefits_returns_ranked_safe_actions():
    payload = json.loads((ROOT/"examples"/"benefits_household.json").read_text())
    result = analyse_benefits(payload)
    assert result.actions
    assert all(a.consequence == "informational" for a in result.actions)
    assert all(not a.requires_human_approval for a in result.actions)
    assert any("Wohngeld" in a.title for a in result.actions)

def test_public_money_never_labels_repeat_awards_as_corruption():
    awards = json.loads((ROOT/"examples"/"public_money_awards.json").read_text())
    result = analyse_awards(awards)
    combined = (result.summary + " ".join(c.text for c in result.claims)).lower()
    assert "corrupt" not in combined
    assert any("Repeated awards" in u for u in result.uncertainties)

def test_decision_review_does_not_invent_deadline():
    text = (ROOT/"examples"/"decision.txt").read_text()
    result = review_decision(text)
    assert result.actions[0].requires_human_approval
    assert any("does not infer an appeal deadline" in u for u in result.uncertainties)

def test_source_allowlist_rejects_unknown():
    try:
        get_source("evil-url")
        assert False
    except SourceError:
        assert True
