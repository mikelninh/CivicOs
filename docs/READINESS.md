# CivicOS readiness

The source of truth is the machine-readable `GET /readiness` endpoint plus the CI gate scripts.

## 1. v1 master proof

Target: **12/12 executable golden cases + 12/12 source-impact coverage + three deeper flagship verticals + scheduled Watchtower + durable snapshot adapter + CI release gate.**

The three flagship verticals are:

- Benefits Graph
- Public Money Graph
- Decision Review

The other seven golden cases are explicitly bounded scenario contracts. They prove cross-domain product/safety behaviour without being misrepresented as mature general-purpose verticals.

Gate command:

```bash
python scripts/check_release_gate.py
```

## 2. Invite-only first-tester pilot

Target: a **small invited cohort of trusted adults** can test usability and safety without CivicOS becoming an open personal-data service.

The build-level pilot gate requires:

1. master-proof readiness;
2. invite-only server-side access guard;
3. explicit adult pilot consent;
4. original personal decision-document bytes not persisted by the CivicOS application;
5. PDF/plain-text upload type + size bounds;
6. browser `no-store` and security headers;
7. bounded rate limiting without retaining IP addresses for the application limiter;
8. a machine-readable pilot policy;
9. a first-tester runbook and hard stop conditions;
10. privacy-minimising feedback path;
11. automated pilot regressions.

Gate command:

```bash
python scripts/check_pilot_gate.py
```

A build can be `first_tester_pilot_ready=true` while `pilot_runtime_configured=false`. That is intentional: the invite secret must be injected at deployment time, never committed.

Required runtime environment:

```bash
CIVICOS_PILOT_MODE=true
CIVICOS_PILOT_TOKEN=<long-random-secret>
CIVICOS_PILOT_SECURE_COOKIES=true
```

See `docs/PILOT_RELEASE.md` and `data/pilot_policy.json`.

## 3. Public beta

Public beta is intentionally stricter and remains **not ready** until CivicOS has:

1. production authentication/authorisation and IAM;
2. encrypted persisted personal evidence where persistence is needed;
3. operational retention/deletion and security controls;
4. qualified benefits and administrative-law review;
5. representative user evaluation with correction/comprehension metrics;
6. a genuine recipient/payment-level public-money provider;
7. authoritative company identifiers and temporal ownership/control;
8. production deployment/security/observability review.

## Commands

```bash
pytest -q
python scripts/check_release_gate.py
python scripts/check_pilot_gate.py
python scripts/watchtower_cycle.py --output artifacts/watchtower-report.json
```

See `docs/V1_RELEASE.md` for the master-proof definition and `docs/PILOT_RELEASE.md` for the first-user test protocol.
