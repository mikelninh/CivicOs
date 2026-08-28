# CivicOS

**Evidence-to-action infrastructure for ordinary people, investigators, and public institutions.**

> Given what is known right now, what is the most useful thing I can do next — and why?

CivicOS connects official sources, entities, rules, evidence, public money, responsibilities, uncertainty, source changes, golden-case replay, and safe next actions through one inspectable graph.

## v0.6 master proof — Watchtower

v0.6 closes the monitoring loop:

```text
Citizen Agents / source monitor
        ↓
explicit prior receipt + facts
        ↓
CivicOS live fetch
        ↓
SHA-256 + declared fact extraction
        ↓
fact delta
        ↓
affected claims
        ↓
affected golden cases
        ↓
deterministic replay
        ↓
Judge MCP request (optional second quality gate)
        ↓
SUPPRESS / NOTIFY / REVIEW
        ↓
human publication/action gate
```

The alert policy is deliberately asymmetric: **content-only churn is suppressed; declared fact changes are surfaced.** Missing replay coverage is `blocked`, never silently counted as a pass.

### 1. Watchtower — source change → replay → alert decision

New endpoint:

```text
POST /watchtower/{source_id}
```

Input is the same explicit prior-snapshot contract as `/sources/{source_id}/compare`, plus optional monitor metadata from Citizen Agents or another source watcher.

Watchtower returns:

- current cryptographic receipt + extracted current facts;
- semantic change state;
- affected claims and golden cases;
- executable golden-case replay results;
- deterministic safety/quality checks;
- prepared Judge MCP quality-gate requests;
- `suppressed`, `notify`, or `review` decision;
- whether human review is mandatory.

Content hash changed but declared facts stayed the same? **Suppressed.**

A declared fact changed and every affected executable case still passes? **Notify.**

A case fails or no executable fixture exists? **Review.**

### 2. Citizen Agents provider contract

`mikelninh/citizen-agents` remains the monitoring provider rather than being copied into CivicOS. Its cited/logged monitoring runs can hand Watchtower:

```json
{
  "previous_sha256": "...",
  "previous_facts": [...],
  "monitor_metadata": {
    "provider": "citizen-agents",
    "run_id": "..."
  }
}
```

CivicOS then performs the evidence comparison and impact/replay decision. No prior snapshot means no invented history.

### 3. Golden-case replay

v0.6 adds executable replay fixtures for the current mature master-proof paths, including:

- `citizen-benefits-gap`
- `citizen-wohngeld-rejection`
- `investigator-public-money`
- `investigator-procurement-pattern`
- `investigator-supplier-links`

Each replay runs the real CivicOS vertical and checks deterministic invariants:

- official/source context remains visible;
- a next action exists;
- uncertainty remains visible;
- claim IDs are unique;
- any external action requires approval;
- audit/replay information remains present.

Golden cases without an executable fixture are explicitly **blocked** until implemented.

### 4. Judge MCP quality-gate contract

CivicOS now ships a dedicated `civicos-evidence-to-action` rubric request for `mikelninh/judge-mcp`.

Judge MCP is deliberately a **second quality-control primitive**, not publication authority. Watchtower always runs deterministic checks first and prepares `register_rubric` + `judge_artifact` requests without silently spending model tokens or publishing from an LLM score.

Optional install:

```bash
python -m pip install -e ".[judge]"
```

### 5. Existing flagship verticals remain intact

**Benefits Graph**

Household facts → ranked support → live facts → official calculator/pre-check handoff → missing inputs → next action.

**Public Money Graph**

Budget → procurement/award → SafeTrace legal entity → reference + entity-based payment reconciliation → audit. Amount similarity alone never confirms a payment link.

**Decision Review**

Bescheid → authority → outcome → factual basis → cited rules → dates → remedy → reviewable response. Uploaded bytes remain hashed, untrusted, in-memory evidence; GitLaw citation existence stays separate from legal applicability.

## Trust states

1. **verified_route** — authoritative URL reviewed, not current-run evidence;
2. **live_fetch** — exact current-run bytes fetched and hashed;
3. **verified fact** — declared deterministic fact profile matched those bytes;
4. **user evidence** — hashed untrusted user document;
5. **change impact** — explicit prior/current comparison mapped to claims/cases;
6. **replay verdict** — affected golden case deterministically passed, failed, or was blocked;
7. **alert decision** — monitoring noise suppressed, meaningful change notified, or incomplete/failing coverage routed to human review.

## Providers, not a monolith

- **SafeTrace** — entity resolution, provenance, temporal investigation graph
- **GitLaw** — German federal-law retrieval, paragraph graph, citation verification
- **PrüfPilot** — PDF/text extraction and untrusted-document handling
- **Public Money MCP** — budget and audit context
- **Citizen Agents** — cited/logged source monitoring events
- **SafeVoice** — privacy-aware evidence intake
- **Judge MCP** — rubric-based second quality gate
- **Digital Worker Factory / CasePilot** — permissions, approval, completion integrity and replay

## API surfaces

- `POST /run` — flagship verticals
- `POST /sources/{source_id}/fetch` — receipt + declared facts/excerpts, never raw bytes
- `POST /sources/{source_id}/compare` — prior/current source comparison → change impact
- `POST /watchtower/{source_id}` — compare → golden-case replay → quality-gate request → alert decision
- `GET /watchtower/status` — provider, replay coverage and alert-policy status
- `POST /decision-review/upload` — secure PDF/text intake + claim-level Decision Review
- `GET /sources`, `/providers`, `/health`

## Proof boundaries

CivicOS v0.6 is a source-backed, regression-tested master proof. It is **not yet** a production public service, legal advice, an entitlement authority, a live public-payment database, or autonomous monitoring/publishing infrastructure.

Highest-value remaining gaps:

- persistent evidence/source snapshot store + scheduled Citizen Agent delivery into Watchtower;
- executable fixtures for all 12 golden cases;
- actual Judge MCP invocation in a controlled runtime + CasePilot before/after replay;
- richer semantic/section-level extraction beyond narrow deterministic profiles;
- genuine recipient/payment data provider;
- authorised register IDs + temporal ownership/control;
- encrypted/redacted persisted personal evidence + IAM/retention;
- qualified domain review and representative user evaluation.

## Run

```bash
python -m pip install -e ".[dev]"
pytest -q
uvicorn app:app --reload
```

Optional providers:

```bash
python -m pip install -e ".[public-money]"
python -m pip install -e ".[judge]"
```

Open `http://127.0.0.1:8000` to use the v0.6 master proof.
