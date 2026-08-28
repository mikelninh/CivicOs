from __future__ import annotations
import json

from civicos.core.readiness import release_readiness


def main() -> None:
    readiness = release_readiness()
    print(json.dumps({
        "release_candidate": readiness["release_candidate"],
        "master_proof_ready": readiness["master_proof_ready"],
        "public_beta_ready": readiness["public_beta_ready"],
        "master_proof_gates": readiness["master_proof_gates"],
        "golden_cases": readiness["golden_cases"],
    }, indent=2))
    if not readiness["master_proof_ready"]:
        raise SystemExit("CivicOS master-proof release gate failed")


if __name__ == "__main__":
    main()
