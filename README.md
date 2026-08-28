# CivicOS

**Evidence-to-action infrastructure for ordinary people, investigators, and public institutions.**

> Given what is known right now, what is the most useful thing I can do next — and why?

CivicOS connects official sources, entities, rules, evidence, public money, responsibilities, uncertainty, source changes, and safe next actions through one inspectable graph.

## v0.5 master proof — close the loop

v0.5 extends the evidence contract from *current truth* to *change impact*:

```text
official source
    ↓
live fetch + SHA-256 receipt
    ↓
verified narrow facts
    ↓
claims
    ↓
SOURCE CHANGES
    ↓
changed/removed/added facts
    ↓
affected claims
    ↓
affected golden cases
    ↓
regression fixture
    ↓
most useful next action
```

A changed page is not automatically a changed rule. A changed fact is not automatically a changed entitlement or legal outcome. CivicOS keeps those boundaries explicit.

### 1. Benefits Graph — official-tool handoff, not fake calculation

Household facts → ranked support checks → live facts → **calculator/pre-check readiness** → official route.

CivicOS now prepares deterministic input plans for:

- **Wohngeld** — Berlin calculator route + current availability state/federal fallback; CivicOS does not invent a substitute amount;
- **Kinderzuschlag** — Bundesagentur **KiZ-Lotse**; explicitly scoped as an eligibility pre-check, not an amount calculator;
- **Elterngeld** — official Familienportal Elterngeldrechner; result remains non-binding until the Elterngeldstelle decides;
- **Unterhaltsvorschuss** — bounded age-band preview plus official route, never an entitlement conclusion.

The API returns each plan's `state`, supplied inputs, missing inputs, result scope, source ID and official route.

### 2. Public Money Graph — award → payment reconciliation

CivicOS now supports a second Public Money input shape:

```json
{"awards": [...], "payments": [...]}
```

A payment is automatically reconciled to an award **only** when both are true:

1. an explicit award/procedure reference matches; and
2. SafeTrace resolves the vendor/recipient records as the same legal entity.

Amount equality or proximity alone can **never** confirm a payment link.

The chain becomes:

```text
budget → procurement/award → legal entity → reconciled payment → audit
```

Ambiguous links go to human review. Unmatched payments remain unmatched. A reconciliation proves a record-to-record link only — not legality, performance, value-for-money, or wrongdoing.

### 3. Source change → regression

New endpoint:

```text
POST /sources/{source_id}/compare
```

The caller supplies its previous receipt hash and previous extracted facts. CivicOS live-fetches the current source and returns:

- content/fact change state;
- added, removed, or changed fact IDs;
- affected claim IDs;
- affected golden-case IDs;
- a machine-readable regression fixture;
- whether the change should force human review.

If no historical snapshot is supplied, CivicOS does **not** invent a previous state.

### 4. Decision Review remains claim-first

Bescheid upload still follows:

```text
authority → outcome → factual basis → cited rules → dates → remedy → reviewable response
```

Uploaded bytes are hashed, treated as untrusted evidence, processed in memory, and not persisted by v0.5. Structural claims remain linked to the exact document receipt. GitLaw citation existence stays separate from legal applicability, and CivicOS still refuses to invent an appeal deadline.

## Trust states

1. **verified_route** — authoritative URL reviewed, not current-run evidence;
2. **live_fetch** — exact current-run bytes fetched and hashed;
3. **verified fact** — declared deterministic fact profile matched those bytes;
4. **user evidence** — hashed untrusted user document;
5. **change impact** — explicit comparison between a supplied prior snapshot and current evidence, mapped to affected claims/cases.

## Shared product contract

```text
question / document / event
    ↓
source + case intake
    ↓
entities + relationships
    ↓
rules + responsibility
    ↓
receipts + facts + claims + contradictions
    ↓
evidence-chain completeness
    ↓
change impact / calculator / reconciliation boundary
    ↓
most useful unresolved next step + Why?
    ↓
privacy / freshness / policy gates
    ↓
human approval where consequential
    ↓
audit + regression + replay
```

**The model may interpret and propose. Authority remains outside the model.**

## Providers, not a monolith

- **SafeTrace** — entity resolution, provenance, temporal investigation graph
- **GitLaw** — German federal-law retrieval, paragraph graph, citation verification
- **PrüfPilot** — PDF/text extraction and untrusted-document handling
- **Public Money MCP** — budget and audit context
- **Citizen Agents** — monitored public-source changes
- **SafeVoice** — privacy-aware evidence intake
- **Judge MCP / CasePilot** — evaluation, completion integrity and replay
- **Digital Worker Factory** — tool permissions, policy gates and human approval

## API surfaces

- `POST /run` — flagship verticals; includes calculator plans or award-payment reconciliation where applicable
- `POST /sources/{source_id}/fetch` — receipt + declared facts/excerpts, never raw bytes
- `POST /sources/{source_id}/compare` — current source vs explicit previous snapshot → change impact + regression fixture
- `POST /decision-review/upload` — secure PDF/text intake + claim-level Decision Review
- `GET /sources` — official source registry
- `GET /providers` — provider map
- `GET /health` — version + evidence contract

## Proof boundaries

CivicOS v0.5 is a source-backed, regression-tested master proof. It is **not yet** a production public service, legal advice, an entitlement authority, a live public-payment database, or an autonomous fraud/corruption finder.

Highest-value remaining gaps:

- a real persistent source-snapshot/change store + Citizen Agent scheduler;
- richer semantic/section-level extraction beyond narrow deterministic profiles;
- automated browser/API handoff to official calculators only where technically and legally appropriate;
- a genuine recipient/payment data provider rather than supplied payment records;
- authorised register IDs + temporal ownership/control;
- redaction, encryption, IAM and retention/deletion before persisted personal evidence;
- Judge MCP / CasePilot replay across full runs;
- qualified domain review + representative user evaluation.

## Run

```bash
python -m pip install -e ".[dev]"
pytest -q
uvicorn app:app --reload
```

Optional Public Money MCP:

```bash
python -m pip install -e ".[public-money]"
```

Open `http://127.0.0.1:8000` to use the v0.5 master proof.
