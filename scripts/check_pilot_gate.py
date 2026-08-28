from __future__ import annotations
import json

from civicos.core.readiness import release_readiness


def main() -> None:
    readiness = release_readiness()
    print(json.dumps({
        "release_candidate": readiness["release_candidate"],
        "master_proof_ready": readiness["master_proof_ready"],
        "first_tester_pilot_ready": readiness["first_tester_pilot_ready"],
        "pilot_runtime_configured": readiness["pilot_runtime_configured"],
        "public_beta_ready": readiness["public_beta_ready"],
        "first_tester_pilot_gates": readiness["first_tester_pilot_gates"],
    }, indent=2))
    if not readiness["first_tester_pilot_ready"]:
        raise SystemExit("CivicOS first-tester pilot release gate failed")


if __name__ == "__main__":
    main()
