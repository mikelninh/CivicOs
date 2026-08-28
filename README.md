# CivicOS

**Evidence-to-action infrastructure for ordinary people, investigators, and public institutions.**

> Given what is known right now, what is the most useful thing I can do next — and why?

CivicOS connects official sources, entities, rules, evidence, public money, responsibilities, uncertainty, and safe next actions through one inspectable graph.

## v0.3 master proof

### 1. Benefits Graph — personal empowerment
Household facts → ranked support checks → current rule signals → missing evidence → official route → optional **live re-fetch + SHA-256 receipt**.

The first 2026 rule snapshot includes official signals for **Wohngeld, Kinderzuschlag, Elterngeld, Unterhaltsvorschuss and Berlin Bildung & Teilhabe**. Bounded figures are shown only where official guidance supports them; rankings remain triage, never entitlement decisions.

### 2. Public Money Graph — institutional accountability
Awards → vendor records → **SafeTrace entity resolution** → SAME_AS / REVIEW / DISTINCT → reproducible patterns → primary-evidence follow-up.

CivicOS now also exposes a real **Public Money MCP provider contract** for `get_budget`, distributions, year comparisons, anomaly heuristics and Bundesrechnungshof lookup. The provider's current bundled scope is budget/audit context — **not recipient/payment-level proof**. If the provider is unavailable, CivicOS fails visibly instead of fabricating a budget answer.

### 3. Decision Review — rights and government transparency
Administrative decision → **PrüfPilot-compatible document intake** → document hash → untrusted-content scan → dates + reasoning + remedy language → cited provisions → **GitLaw citation adapter** → evidence gaps → reviewable next step.

`POST /decision-review/upload` accepts PDF or UTF-8 text. Uploaded personal bytes are processed in memory and **not persisted by v0.3**. Prompt-injection/script-like document content is quarantined. A source route proves a citation can be located, not that it governs the concrete case. CivicOS deliberately refuses to invent appeal deadlines.

## Three evidence states

CivicOS keeps these trust levels separate:

1. **verified_route** — an authoritative URL has been reviewed, but not fetched for this run;
2. **live_fetch** — CivicOS fetched the allowlisted official source for this run and created a cryptographic receipt;
3. **user evidence** — a user-supplied document is hashed and processed as untrusted input; it is never treated as an instruction to the agent.

A run can request `refresh_sources=true`. The result then shows `live_fetch_count`, failures, source states, and evidence receipts. Optional persistence of *public official-source bytes* requires an explicit `CIVICOS_EVIDENCE_DIR`; otherwise receipts remain in memory only.

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
claims + evidence + contradictions
    ↓
freshness + privacy + provider boundaries
    ↓
best next action + Why?
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
- **PrüfPilot** — PDF/text extraction and untrusted-document handling
- **Public Money MCP** — budget and audit tools
- **Citizen Agents** — monitored public-source changes
- **SafeVoice** — privacy-aware evidence intake
- **Judge MCP / CasePilot** — evaluation, completion integrity and replay
- **Digital Worker Factory** — tool permissions, policy gates and human approval

## API surfaces

- `POST /run` — execute a flagship vertical; optional live source refresh
- `POST /sources/{source_id}/fetch` — fetch one allowlisted official source and return its receipt, never the raw bytes
- `POST /decision-review/upload` — hash + inspect a PDF/text decision and run Decision Review
- `GET /sources` — inspected official source registry
- `GET /providers` — provider/capability map
- `GET /health` — release health/version

## Proof boundaries

CivicOS v0.3 is a source-backed, regression-tested master proof. It is **not yet** a production public service, legal advice, an official entitlement calculator, a complete public-finance database, or an autonomous fraud/corruption finder.

The biggest remaining gaps are:

- current-law / source parsing from live bytes rather than only attaching receipts;
- deterministic official benefit-calculator integration where legally/technically available;
- recipient/payment-level public-money ingestion;
- authorised company/register identifiers + temporal ownership/control;
- redaction, encryption, IAM and retention/deletion for any future persisted personal evidence;
- Judge MCP / CasePilot replay across the full run;
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

Then open `http://127.0.0.1:8000` and test all three flagship verticals through one evidence-to-action runtime.
