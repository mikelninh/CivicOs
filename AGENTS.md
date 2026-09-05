# AGENTS.md — CivicOS

## Mission
Build evidence-to-action infrastructure that helps people and institutions decide what to do next without hiding uncertainty, provenance, policy boundaries or human authority.

## Start here
1. Read `README.md`.
2. Read the release and pilot docs relevant to the task.
3. Load only the provider/domain code needed for the current change.
4. Re-open current tests, readiness gates and source registries before making claims.

## Source-of-truth map
- Product scope and current release state: `README.md`
- Release contract: `docs/V1_RELEASE.md`, `docs/READINESS.md`
- Pilot contract: `docs/PILOT_RELEASE.md`, `data/pilot_policy.json`
- Runtime and APIs: `app.py`, `civicos/`
- Golden cases and fixtures: `data/`, `examples/`
- Verification scripts: `scripts/`
- Tests: `tests/`
- CI / scheduled monitoring: `.github/workflows/`
- Public proof surfaces: `web/`

## Contract before work
Every substantial task must define:
- goal,
- authoritative sources,
- outputs,
- constraints and non-goals,
- acceptance criteria,
- forbidden actions,
- risk class,
- retry budget,
- verification commands,
- next owner.

Do not silently widen a bounded golden scenario into a production capability claim.

## Roles
- **Shaper** — clarifies user, problem, constraints, architecture and success criteria.
- **Builder** — implements a bounded change.
- **Verifier** — independently checks tests, golden cases, evidence and release claims.
- **Critic** — looks for unsupported conclusions, unsafe authority transfer, stale sources, regressions and overengineering.
- **Operator** — performs approved external actions only after the relevant release/policy gate.

Builder and Verifier should be separate passes for consequential changes.

## Action classes
- **A0 Observe** — read/search/analyse. Automatic.
- **A1 Local reversible** — draft/test/edit isolated work. Automatic.
- **A2 Shared reversible** — branch, PR, preview, issue. Logged; normally automatic.
- **A3 Consequential** — deploy, publish, send, write externally, promote a baseline. Human approval required.
- **A4 High-impact** — personal-data egress, destructive production changes, entitlement/legal findings, public-beta promotion. Explicit approval plus stronger independent verification.

Trust the action class, not the agent personality.

## Verification gates
Minimum engineering checks:

```bash
pytest -q
python scripts/check_release_gate.py
python scripts/check_pilot_gate.py
```

For Watchtower/source changes, also replay the affected golden cases and inspect semantic deltas before any baseline promotion.

Never claim a command passed unless it actually ran. Never treat an optional judge score as publication authority.

## Autonomy boundary
Agents may interpret evidence, propose next actions, generate code, run tests and prepare reversible changes.

Agents may not autonomously:
- make consequential benefit/legal/enforcement decisions,
- collapse entity relationships into allegations,
- promote semantic source baselines,
- widen pilot access,
- publish production claims,
- perform irreversible external actions.

Human authority remains outside the model.

## Evidence and uncertainty
Preserve these distinctions:
- official route ≠ current evidence,
- live fetch ≠ verified semantic fact,
- verified fact ≠ legal/benefit applicability,
- entity link ≠ wrongdoing,
- budget/award ≠ payment,
- changed page ≠ changed rule,
- model/judge output ≠ authority.

Unknown is a valid result. Do not repair missing evidence with confident prose.

## Retry policy
Use bounded repair loops. Default maximum: 3 attempts.
If the same failure repeats twice, stop and improve the test, fixture, source rule, architecture or decomposition instead of retrying blindly.

## Failure upgrades
- missed source change → source-impact regression
- wrong entity merge → entity-resolution fixture
- unsupported recommendation → decision-boundary test
- unsafe action → permission gate
- stale source → freshness rule
- lost state → durable state/receipt
- repeated failure → stronger harness or decomposition

A fix should reduce recurrence across future cases, not only patch the current demo.

## Definition of done
Work is done only when:
1. acceptance criteria are evidenced,
2. affected golden cases pass,
3. uncertainty and provenance remain visible,
4. release/pilot boundaries are unchanged unless explicitly approved,
5. consequential actions remain gated,
6. rollback and next step are known,
7. the claim made in the UI/README is no stronger than the evidence.