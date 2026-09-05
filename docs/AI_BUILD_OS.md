# CivicOS — AI Build OS

CivicOS uses a six-stage operating model for serious changes:

**Shape → Specify → Delegate → Prove → Ship → Watch**

The purpose is not to maximise agent autonomy. It is to maximise useful autonomy while keeping evidence, uncertainty, release state and human authority inspectable.

## 01 — SHAPE

**Problem → user → constraints → architecture**

Before implementation, establish:
- the concrete user decision or workflow,
- which sources are authoritative,
- privacy / safety / legal constraints,
- whether the capability belongs in a flagship engine, bounded golden case or future scope,
- the smallest architecture that can prove the idea.

CivicOS deliberately avoids turning one generic agent into a monolith. Providers and deterministic controls own narrow responsibilities.

## 02 — SPECIFY

**Requirements → boundaries → acceptance criteria**

A substantial task should define:
- inputs and outputs,
- non-goals,
- source requirements,
- authority boundary,
- failure behaviour,
- golden cases affected,
- measurable done criteria.

Release labels are part of the specification. `master proof`, `first-tester pilot` and `public beta` are separate claims and may not silently collapse into one another.

## 03 — DELEGATE

**Agents execute within explicit autonomy limits**

Use the smallest safe autonomy class:
- A0 observe,
- A1 local reversible,
- A2 shared reversible,
- A3 consequential / human approval,
- A4 high-impact / explicit approval + stronger independent verification.

Typical agent passes:
1. Shaper — scope and architecture,
2. Builder — implementation,
3. Verifier — independent checks,
4. Critic — adversarial review,
5. Operator — approved release/action only.

The model may interpret and propose. Authority remains outside the model.

## 04 — PROVE

**Tests → evals → benchmarks → adversarial cases**

CivicOS evidence currently includes:
- 12 executable golden cases,
- deterministic replay,
- source-impact coverage,
- release and pilot gate scripts,
- policy/security regressions,
- explicit human-review boundaries,
- provider-specific evidence and evaluation.

A change is not successful because the UI looks plausible. It must survive the relevant automated checks and preserve the intended boundary.

Preferred evidence:
- deterministic test result,
- golden-case replay,
- source receipt / provenance,
- measurable benchmark,
- explicit failure case,
- inspectable trace or readiness output.

## 05 — SHIP

**CI → deployment gates → production**

Shipping follows the release claim, not developer confidence.

```text
local / branch proof
  ↓
CI + deterministic gates
  ↓
master proof
  ↓
controlled pilot requirements
  ↓
first-tester pilot
  ↓
production IAM/security/domain validation
  ↓
public beta
```

A lower stage cannot self-promote to a higher one.

## 06 — WATCH

**Traces → logs → regressions → feedback**

Watchtower is the clearest production-shaped example:

```text
official source
  ↓
content receipt + semantic delta
  ↓
affected claims / golden cases
  ↓
deterministic replay
  ↓
SUPPRESS / NOTIFY / REVIEW
  ↓
human authority
```

Monitoring should feed back into the build system:
- missed change → regression fixture,
- noisy alert → better semantic rule,
- stale evidence → freshness policy,
- unsafe proposal → stronger permission boundary,
- repeated user correction → revised spec/eval.

## Evidence contract for portfolio claims

When CivicOS is used as proof of engineering capability, reviewers should be able to answer:
1. What problem is bounded here?
2. What may the model do?
3. What may it not do?
4. What evidence supports a result?
5. Which automated checks prove the behaviour?
6. What remains unknown or not production-ready?
7. What happens when sources change?
8. Where does human judgement enter?

If those answers are hidden behind a generic AI score, the proof is weaker than it should be.

## Portfolio principle

> **Agents build. Evidence earns trust. Humans retain judgement.**
