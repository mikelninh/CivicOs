# CivicOS architecture

## North star

> Given what is known right now, what is the most useful thing I can do next — and why?

## Shared engine

CivicOS deliberately separates source truth, entity truth, rule/context truth, claims, uncertainty, action, authority, and evaluation.

## First three verticals

### Benefits Graph
Household facts → candidate support routes → missing evidence → official check/application route.

### Public Money Graph
Budget/procurement inputs → normalised organisations → reproducible patterns → primary evidence follow-up.

### Decision Review
Decision text/document → facts/dates/citations → evidence gaps → current rule verification → review checklist/draft.

## Provider strategy

Existing repositories stay independent. CivicOS integrates them behind explicit interfaces:

- SafeTrace: entity resolution, claims, provenance, investigation graph
- GitLaw: legal retrieval and citation verification
- Public Money MCP: deterministic fiscal tools
- Citizen Agents: monitored changes
- PrüfPilot: typed document intake
- SafeVoice: privacy-aware evidence packaging
- Judge MCP / CasePilot: evaluations and replay
- Digital Worker Factory: tool/policy/approval runtime

The master proof should prove composition, not create a monolith.
