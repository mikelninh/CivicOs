# CivicOS

**Evidence-to-action infrastructure for ordinary people, investigators, and public institutions.**

> Given what is known right now, what is the most useful thing I can do next — and why?

CivicOS connects official sources, entities, rules, evidence, public money, responsibilities, uncertainty, and safe next actions through one inspectable graph.

## v0.4 master proof — receipts become knowledge

The core v0.4 contract is deliberately stricter than “we fetched an official page”:

```text
official source
    ↓
live fetch
    ↓
SHA-256 receipt
    ↓
declared deterministic fact profile
    ↓
exact evidence excerpt
    ↓
fact → claim link
    ↓
remaining evidence gap
    ↓
most useful next action
```

A live fetch is **not automatically a verified fact**. CivicOS only upgrades a claim when a narrow, pre-declared pattern is actually present in the fetched bytes. Unprofiled or unmatched content stays receipt-only.

### 1. Benefits Graph — personal empowerment
Household facts → ranked support checks → current rule snapshot → optional live source refresh → evidence-linked facts → missing evidence → official route.

The v0.4 fact profiles cover narrow source facts for **Wohngeld calculation factors, Kinderzuschlag maximum, Elterngeld ranges/work-hours/income-ceiling signals, Unterhaltsvorschuss age-band amounts, and Berlin Bildung & Teilhabe school-supplies support**. These facts support triage and explanation; they do not turn CivicOS into an entitlement authority or guarantee a payout.

### 2. Public Money Graph — institutional accountability
CivicOS now models the accountability chain explicitly:

```text
budget → procurement/award → legal entity → payment → audit
```

SafeTrace resolves `SAME_AS / REVIEW / DISTINCT` at the entity layer. Public Money MCP can populate budget/audit context. The **payment stage is deliberately marked missing** until recipient/payment-level evidence is connected and reconciled to the award and legal entity.

This means CivicOS can show *where the evidence chain breaks* instead of silently collapsing budget, award and payment into the same thing. Repeated awards and graph links remain investigation leads, never corruption findings.

### 3. Decision Review — rights and government transparency
Decision Review now decomposes an uploaded Bescheid into a claim graph:

```text
authority → decision/outcome → factual basis → cited rules → dates → remedy → reviewable response
```

`POST /decision-review/upload` accepts PDF or UTF-8 text through PrüfPilot-compatible intake. Personal bytes are hashed, scanned as untrusted content, processed in memory, and not persisted by v0.4. Every structural `decision:*` claim derived from that upload is linked back to the exact document receipt.

GitLaw resolves supported citation routes, but CivicOS keeps **citation existence**, **legal applicability**, and **factual correctness** separate. It still refuses to invent an appeal deadline.

## Evidence states

CivicOS separates four useful states:

1. **verified_route** — authoritative URL reviewed, not fetched for this run;
2. **live_fetch** — exact current-run bytes fetched and hashed;
3. **verified fact** — a declared deterministic fact profile matched those exact bytes and created an evidence excerpt + claim link;
4. **user evidence** — user-supplied bytes hashed and treated as untrusted evidence, never agent instructions.

The run response exposes `evidence_receipts`, `evidence_excerpts`, `evidence_facts`, claim `evidence_ids`, graph state, and freshness metrics.

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
most useful unresolved next step + Why?
    ↓
privacy / freshness / policy gates
    ↓
human approval where consequential
    ↓
audit + evaluation + replay
```

**The model may interpret and propose. Authority remains outside the model.**

## Providers, not a monolith

CivicOS is the orchestration/product layer. Existing projects remain independently testable providers:

- **SafeTrace** — entity resolution, provenance, temporal investigation graph
- **GitLaw** — German federal-law corpus, retrieval, paragraph graph, citation verification
- **PrüfPilot** — PDF/text extraction and untrusted-document handling
- **Public Money MCP** — budget and audit tools
- **Citizen Agents** — monitored public-source changes
- **SafeVoice** — privacy-aware evidence intake
- **Judge MCP / CasePilot** — evaluation, completion integrity and replay
- **Digital Worker Factory** — tool permissions, policy gates and human approval

## API surfaces

- `POST /run` — execute a flagship vertical; optional live source refresh and fact extraction
- `POST /sources/{source_id}/fetch` — return receipt + any declared verified facts/excerpts, never raw bytes
- `POST /decision-review/upload` — hash + inspect a PDF/text decision and run claim-level Decision Review
- `GET /sources` — official source registry
- `GET /providers` — provider/capability map
- `GET /health` — release/version + evidence contract

## Proof boundaries

CivicOS v0.4 is a source-backed, regression-tested master proof. It is **not yet** a production public service, legal advice, an official entitlement calculator, a complete public-finance database, or an autonomous fraud/corruption finder.

The next highest-value gaps are:

- richer semantic/section-level extraction from live official bytes beyond the narrow declared profiles;
- deterministic official benefit-calculator integration where feasible;
- **recipient/payment-level public-money ingestion and award-payment reconciliation**;
- authorised register identifiers + temporal ownership/control;
- source/version change detection and automatic regression fixtures;
- redaction, encryption, IAM and retention/deletion before persisted personal evidence;
- Judge MCP / CasePilot replay across the full evidence-to-action run;
- qualified domain review and representative user evaluation.

## Run

```bash
python -m pip install -e ".[dev]"
pytest -q
uvicorn app:app --reload
```

Optional Public Money MCP in-process provider:

```bash
python -m pip install -e ".[public-money]"
```

Then open `http://127.0.0.1:8000` and test the three flagship verticals through one evidence-to-action runtime.
