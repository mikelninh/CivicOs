# CivicOS v1.0 release definition

> **Given what is known right now, what is the most useful thing I can do next — and why?**

CivicOS v1.0 is defined as a **master-proof release**, not a claim that CivicOS is already a production public authority or legal/benefit decision service.

## v1 master-proof release gates

1. **12/12 executable golden cases** across citizen, investigator and government-operator workflows.
2. **Three deeper flagship verticals**: Benefits Graph, Public Money Graph, Decision Review.
3. Evidence states remain distinct: authoritative route → live receipt → narrow verified fact → claim → uncertainty → action.
4. SafeTrace entity matching is evidence-backed; related entities are not collapsed into legal identity.
5. Public-money reconciliation requires a stable award reference plus legal-entity match; amount similarity alone never confirms a payment link.
6. Decision Review hashes and treats uploaded documents as untrusted evidence; cited law existence remains separate from legal applicability.
7. Watchtower suppresses content-only source churn and replays affected golden cases on semantic fact changes.
8. Watchtower has reviewed semantic baselines, a scheduled GitHub workflow, and an optional durable SQLite snapshot adapter.
9. Judge MCP can be invoked only behind an explicit execution gate and remains a quality signal, never publication authority.
10. CI runs the full accumulated test suite and a separate release-readiness gate.

## 12 golden cases

### Citizens
- Wohngeld rejection / administrative decision review
- missing benefits/support
- rent increase verification
- digital harassment evidence preservation
- responsible authority discovery
- information-access request preparation

### Investigators
- supplier identity/link analysis
- public-money chain
- procurement pattern analysis
- contradictory control/company records

### Public operators
- permit/service routing and blocker diagnosis
- policy/rule change impact

The 7 non-flagship cases are deliberately labelled **bounded golden scenarios**. They execute the same safety/product contract but are not presented as mature general-purpose domain engines.

## Watchtower

```text
Citizen Agents / scheduler
        ↓
official source fetch + SHA-256 receipt
        ↓
semantic fact delta
        ↓
affected claims + golden cases
        ↓
deterministic replay
        ↓
optional Judge MCP quality signal
        ↓
SUPPRESS / NOTIFY / REVIEW
        ↓
human authority gate
```

Repo-reviewed semantic baselines are never auto-promoted after a change. A human review decides whether a new fact becomes the accepted baseline.

## What blocks public beta

The `/readiness` endpoint must continue to report `public_beta_ready=false` until these are solved:

- encrypted persisted personal evidence;
- authentication/authorisation and IAM;
- retention/deletion controls;
- qualified benefits and administrative-law review;
- representative user testing and measured correction/comprehension rates;
- genuine authoritative recipient/payment-level public-money provider;
- authoritative company identifiers and temporal ownership/control;
- production deployment/security/observability review.

This distinction is intentional:

**v1 master proof = coherent, inspectable, regression-tested platform proof.**

**public beta = a service ordinary people can responsibly rely on with real personal cases.**
