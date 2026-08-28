# CivicOS

**Evidence-to-action infrastructure for ordinary people, investigators, and public institutions.**

> **Given what is known right now, what is the most useful thing I can do next — and why?**

CivicOS connects official sources, entities, rules, evidence, public money, responsibilities, uncertainty, source changes and safe next actions through one inspectable runtime.

## v1.0 release candidate

CivicOS `1.0.0-rc1` defines a **master-proof release** with a machine-enforced readiness gate. It does **not** claim production public-service readiness.

### The three flagship verticals

**Benefits Graph**  
Household facts → ranked support → live evidence → official calculator/pre-check handoff → missing inputs → most useful next action.

**Public Money Graph**  
Budget → award → SafeTrace legal entity → reference + entity-based payment reconciliation → audit. Amount similarity alone never proves a payment link.

**Decision Review**  
Bescheid → hashed/untrusted intake → authority/outcome/factual basis → cited rules → evidence gaps → dates/remedy questions → reviewable next step.

## 12 executable golden cases

The v1 master-proof contract now replays all twelve cases:

- Wohngeld rejection
- missing benefits/support
- rent increase review
- digital-harassment evidence preservation
- responsible-authority discovery
- information-access request preparation
- supplier identity/link analysis
- public-money chain
- procurement patterns
- contradictory company/control records
- permit/service routing
- policy-change impact

Five cases exercise the deeper flagship engines; seven are clearly labelled **bounded golden scenarios**, not mature general-purpose domain engines.

## Watchtower

```text
Citizen Agents / scheduled monitor
        ↓
official source fetch + SHA-256 receipt
        ↓
semantic fact delta
        ↓
affected claims + golden cases
        ↓
12-case deterministic replay
        ↓
optional Judge MCP quality signal
        ↓
SUPPRESS noise · NOTIFY material change · REVIEW uncertainty
        ↓
human authority gate
```

- repo-reviewed semantic baselines live in `data/watchtower_baselines.json`;
- `.github/workflows/watchtower.yml` runs the monitor every six hours after merge;
- `SnapshotStore` provides a durable SQLite adapter for deployed instances;
- baseline changes are **never auto-promoted** by the scheduler.

## Quality and authority boundaries

- official route ≠ current evidence;
- live fetch ≠ verified semantic fact;
- verified fact ≠ entitlement/legal applicability;
- entity link ≠ wrongdoing;
- budget/award ≠ payment;
- amount similarity ≠ payment match;
- changed page ≠ changed rule;
- Judge MCP score ≠ publication authority;
- consequential external action requires human approval.

## Release readiness

`GET /readiness` separates two gates:

### v1 master proof

Requires 12/12 executable cases, all deterministic replays passing, three flagship verticals, Watchtower scheduling/baselines, durable state adapter, current official-source registry and CI release gate.

### public beta

Intentionally remains **not ready** until CivicOS has:

- encrypted persisted personal evidence;
- authentication/authorisation, IAM and retention/deletion controls;
- qualified benefits + administrative-law review;
- representative user evaluation;
- genuine recipient/payment-level public-money data;
- authoritative company identifiers + temporal ownership/control;
- production security/observability review.

See [`docs/V1_RELEASE.md`](docs/V1_RELEASE.md) and [`docs/READINESS.md`](docs/READINESS.md).

## Providers, not a monolith

- **SafeTrace** — entity resolution, provenance, temporal investigation graph
- **GitLaw** — legal retrieval, paragraph graph, citation verification
- **PrüfPilot** — document extraction + untrusted intake
- **Public Money MCP** — budget/audit context
- **Citizen Agents** — cited/logged public-source monitoring
- **SafeVoice** — privacy-aware evidence preparation
- **Judge MCP** — optional rubric-based second quality gate
- **Digital Worker Factory / CasePilot** — permission gates, approval and replay concepts

## Main surfaces

- `/` — v1 master-proof home
- `/lab` — interactive Benefits / Public Money / Decision Review proof
- `/watchtower` — semantic-change replay UI
- `/readiness/ui` — human-readable release gates
- `/readiness` — machine-readable release gates
- `/docs` — FastAPI/OpenAPI

## Run

```bash
python -m pip install -e ".[dev]"
pytest -q
python scripts/check_release_gate.py
uvicorn app:app --reload
```

Optional providers:

```bash
python -m pip install -e ".[public-money]"
python -m pip install -e ".[judge]"
```

Scheduled monitoring can also be run locally:

```bash
python scripts/watchtower_cycle.py --output artifacts/watchtower-report.json --state-db .civicos/state.sqlite3
```

**The model may interpret and propose. Authority remains outside the model.**
