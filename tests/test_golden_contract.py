import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_all_12_golden_cases_have_power_contract():
    data = json.loads((ROOT/"data"/"golden_cases.json").read_text())
    assert len(data["cases"]) == 12
    required = {"official_sources","entities","rules_or_context","claims","uncertainty","next_action","why","audit"}
    for case in data["cases"]:
        assert required.issubset(set(case["contract"]))
        assert "hide_uncertainty" in case["must_not"]
