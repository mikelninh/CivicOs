# CivicOS

**Evidence-to-action infrastructure for ordinary people, investigators, and public institutions.**

> **Given what is known right now, what is the most useful thing I can do next — and why?**

CivicOS connects official sources, entities, rules, evidence, public money, responsibilities, uncertainty, source changes and safe next actions through one inspectable runtime.

## v1.0 first-tester release candidate

CivicOS `1.0.0-rc2` separates **three release gates** instead of hiding everything behind one green badge:

1. **Master proof — READY**: architecture, evidence and safety contract.
2. **Invite-only first-tester pilot — READY at build level**: controlled adult cohort with explicit consent and ephemeral personal evidence.
3. **Public beta — NOT YET**: production IAM/security, domain validation, representative evaluation and missing authoritative providers remain open.

The deployment-specific pilot gate still requires `CIVICOS_PILOT_MODE=true` and a secret configured outside Git.

### The three flagship verticals

**Benefits Graph**  
Household facts → ranked support → live evidence → official calculator/pre-check handoff → missing inputs → most useful next action.

**Public Money Graph**  
Budget → award → SafeTrace legal entity → reference + entity-based payment reconciliation → audit. Amount similarity alone never proves a payment link.

**Decision Review**  
Bescheid → hashed/untrusted intake → authority/outcome/factual basis → cited rules → evidence gaps → dates/remedy questions → reviewable next step.

## Invite-only first-tester pilot

The pilot is designed for **5–15 trusted adult testers**, not an open public launch.

When pilot mode is enabled:

- all write/research endpoints require an invite code or signed pilot session;
- explicit pilot consent is enforced server-side;
- the invite becomes a signed HttpOnly session cookie rather than being stored in browser JavaScript;
- deployed cookies default to `Secure` + `SameSite=Strict` and expire after eight hours;
- personal PDF/text decision uploads are processed in memory and the application does not persist the original document bytes;
- uploads are capped at 5 MB by default and limited to PDF/plain text;
- application responses use `Cache-Control: no-store` plus browser security headers;
- a bounded per-session rate limit avoids retaining IP addresses for the application-level limiter;
- consequential external actions remain human-approved;
- tester feedback is collected through a privacy-minimising GitHub issue template.

Pilot portal: `/pilot`

Pilot policy: `data/pilot_policy.json`

Pilot runbook: [`docs/PILOT_RELEASE.md`](docs/PILOT_RELEASE.md)

Required deployment environment:

```bash
CIVICOS_PILOT_MODE=true
CIVICOS_PILOT_TOKEN=<long-random-secret>
CIVICOS_PILOT_SECURE_COOKIES=true
```

Generate the secret locally, for example:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Never commit the invite secret.

## 12 executable golden cases

The v1 master-proof contract replays all twelve cases:

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

`GET /readiness` exposes all three gates.

### Master proof

Requires 12/12 executable cases, all deterministic replays passing, source-impact coverage, three flagship verticals, Watchtower scheduling/baselines, durable state adapter, current official-source registry and CI release gate.

### First tester pilot

Requires the master proof plus invite-only guard, explicit adult consent, non-persistent personal document bytes, bounded uploads, no-store/security headers, rate limiting, machine-readable pilot policy, tester runbook, privacy-minimising feedback path and pilot regression tests.

CI enforces this with `scripts/check_pilot_gate.py`.

### Public beta

Intentionally remains **not ready** until CivicOS has:

- production authentication/authorisation/IAM;
- encrypted persisted personal evidence where persistence is actually needed;
- retention/deletion and operational security controls;
- qualified benefits + administrative-law review;
- representative user evaluation;
- genuine recipient/payment-level public-money data;
- authoritative company identifiers + temporal ownership/control;
- production security/observability review.

See [`docs/V1_RELEASE.md`](docs/V1_RELEASE.md), [`docs/PILOT_RELEASE.md`](docs/PILOT_RELEASE.md), and [`docs/READINESS.md`](docs/READINESS.md).

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

- `/` — v1 home
- `/pilot` — invite + consent entry for first testers
- `/lab` — interactive Benefits / Public Money / Decision Review proof
- `/watchtower` — semantic-change replay UI
- `/readiness/ui` — human-readable three-gate release status
- `/readiness` — machine-readable release gates
- `/pilot/status` — pilot runtime policy/config state without exposing the secret
- `/docs` — FastAPI/OpenAPI

## Run

```bash
python -m pip install -e ".[dev]"
pytest -q
python scripts/check_release_gate.py
python scripts/check_pilot_gate.py
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
