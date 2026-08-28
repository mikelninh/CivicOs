from pathlib import Path
import json
from civicos.engine import run

ROOT = Path(__file__).resolve().parents[1]

def show(vertical, payload):
    result = run(vertical, payload)
    print(f"\n=== {result.vertical.upper()} ===")
    print(result.summary)
    if result.next_action:
        print("NEXT:", result.next_action.title)
        print("WHY:", result.next_action.why)
        print("MISSING:", ", ".join(result.next_action.missing_evidence) or "none")
    print("UNCERTAINTY:", " | ".join(result.uncertainties))

if __name__ == "__main__":
    show("benefits", json.loads((ROOT/"examples"/"benefits_household.json").read_text()))
    show("public-money", json.loads((ROOT/"examples"/"public_money_awards.json").read_text()))
    show("decision-review", {"text": (ROOT/"examples"/"decision.txt").read_text()})
