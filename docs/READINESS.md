# CivicOS readiness

The source of truth is the machine-readable `GET /readiness` endpoint and `scripts/check_release_gate.py`.

## v1 master proof

Target: **12/12 executable golden cases + three deeper flagship verticals + scheduled Watchtower + durable snapshot adapter + CI release gate.**

The three flagship verticals are:

- Benefits Graph
- Public Money Graph
- Decision Review

The other seven golden cases are explicitly bounded scenario contracts. They prove cross-domain product/safety behaviour without being misrepresented as mature general-purpose verticals.

## Public beta

Public beta is intentionally a stricter gate and remains **not ready** until CivicOS has:

1. encrypted persisted personal evidence;
2. authentication/authorisation, IAM and retention/deletion controls;
3. qualified benefits and administrative-law review;
4. representative user evaluation with correction/comprehension metrics;
5. a genuine recipient/payment-level public-money provider;
6. authoritative company identifiers and temporal ownership/control;
7. production deployment/security/observability review.

## Commands

```bash
pytest -q
python scripts/check_release_gate.py
python scripts/watchtower_cycle.py --output artifacts/watchtower-report.json
```

See `docs/V1_RELEASE.md` for the complete release definition.
