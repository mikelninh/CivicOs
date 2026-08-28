# CivicOS

**Evidence-to-action infrastructure for ordinary people, investigators, and public institutions.**

> Given what is known right now, what is the most useful thing I can do next — and why?

CivicOS connects official sources, entities, rules, evidence, public money, responsibilities, uncertainty, and safe next actions through one inspectable graph.

## v0.2 master proof

### 1. Benefits Graph — personal empowerment
Household facts → ranked support checks → current rule signals → missing evidence → official route.

The first 2026 rule snapshot includes current official signals for **Wohngeld, Kinderzuschlag, Elterngeld, Unterhaltsvorschuss and Berlin Bildung & Teilhabe**. Bounded figures are shown only where official guidance supports them; rankings remain triage, never entitlement decisions.

### 2. Public Money Graph — institutional accountability
Awards → vendor records → **SafeTrace entity resolution** → SAME_AS / REVIEW / DISTINCT → reproducible patterns → primary-evidence follow-up.

CivicOS now distinguishes a repeated vendor label from evidence-backed legal-entity matching. A relationship or repeated award is a lead, not a corruption finding.

### 3. Decision Review — rights and government transparency
Administrative decision → dates + reasoning + remedy language → cited provisions → **GitLaw citation adapter** → official section route / unresolved lookup → evidence gaps → reviewable next step.

A source route proves a citation can be located, not that it governs the concrete case. CivicOS deliberately refuses to invent appeal deadlines.

## Shared product contract

```text
question / document / event
    ↓
official sources + case intake
    ↓
entities + relationships
    ↓
rules + responsibility
    ↓
claims + evidence + contradictions
    ↓
current constraint
    ↓
best next action + Why?
    ↓
freshness / privacy / policy gates
    ↓
human approval where consequential
    ↓
audit + evaluation + replay
```

**The model may interpret and propose. Authority remains outside the model.**

## Providers, not a monolith

CivicOS is the product/orchestration layer. Existing projects stay independently testable behind explicit contracts:

- **SafeTrace** — entity resolution, provenance, temporal investigation graph
- **GitLaw** — German federal-law corpus, retrieval, paragraph graph, citation verification
- **PrüfPilot** — typed document extraction/review
- **Public Money MCP** — budget and audit tools
- **Citizen Agents** — monitored public-source changes
- **SafeVoice** — privacy-aware evidence intake
- **Judge MCP / CasePilot** — evaluation, completion integrity and replay
- **Digital Worker Factory** — tool permissions, policy gates and human approval

## Proof boundaries

CivicOS v0.2 is a source-backed, regression-tested master proof. It is **not yet** a production public service, legal advice, an official entitlement calculator, or an autonomous fraud/corruption finder.

The next production gaps are live per-run source receipts, deterministic official benefit calculators where available, richer company/register identifiers, recipient-level payment ingestion, secure document upload/redaction, and qualified user/domain evaluation.

## Run

```bash
python -m pip install -e ".[dev]"
pytest -q
uvicorn app:app --reload
```

Then open `http://127.0.0.1:8000` and test all three flagship verticals through the same `/run` contract.
