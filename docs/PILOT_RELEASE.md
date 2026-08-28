# CivicOS first-tester pilot release

## Release definition

The first tester release is deliberately narrower than a public beta.

**Pilot-ready means:** a small invite-only cohort of adults can use CivicOS to test whether the evidence, uncertainty and next-action experience is understandable and useful, without CivicOS storing personal decision documents or taking external consequential actions.

It does **not** mean production IAM, legal advice, GDPR certification, authority-grade benefit decisions, public deployment to unknown users, or safe handling of arbitrary sensitive documents.

## Cohort

Start with **5–15 trusted adult testers**.

Recommended sequence for each tester:

1. Use the synthetic Benefits Graph case.
2. Use the synthetic Decision Review case.
3. Use the synthetic Public Money case.
4. Explain in their own words what CivicOS believes, what remains uncertain, and what the next action is.
5. Only then, if comfortable, try one **redacted** real situation that fits the pilot boundaries.
6. Submit the pilot feedback issue without personal information.

Do not recruit children as direct pilot users.

## Deployment environment

Required for an invite-only pilot deployment:

```bash
CIVICOS_PILOT_MODE=true
CIVICOS_PILOT_TOKEN=<long-random-secret>
CIVICOS_PILOT_SECURE_COOKIES=true
```

Optional bounded controls:

```bash
CIVICOS_MAX_UPLOAD_BYTES=5242880
CIVICOS_PILOT_RATE_LIMIT_PER_MINUTE=30
```

Generate the invite secret with a cryptographically secure random generator, for example:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Do not commit the secret to GitHub.

For local HTTP-only testing, `CIVICOS_PILOT_SECURE_COOKIES=false` may be used. Do not use that setting on an internet-facing deployment.

## Pilot data boundary

The CivicOS application:

- does not persist uploaded personal document bytes;
- processes PDF/text decisions in memory;
- stores a cryptographic receipt in the response/audit trace, not the original personal document;
- does not implement application-level request-body logging;
- disables browser caching with `Cache-Control: no-store`;
- limits pilot uploads to PDF/plain text and a bounded maximum size;
- does not create a personal-case database for the pilot.

Testers should redact unnecessary names, addresses, case/account numbers and identifiers before upload.

Do **not** upload passwords, authentication codes, bank credentials, identity-document scans, medical records, criminal-case material or intimate information.

A deployment provider may still process ordinary connection/operational metadata according to its configuration. That must be reviewed before expanding the cohort.

## Authority boundary

CivicOS may retrieve, structure, compare and recommend. It may prepare a draft or next step. It does not autonomously submit applications, objections, accusations, complaints or other consequential external actions.

For benefits and legal/administrative questions, testers must verify consequential guidance against the official source or a qualified professional.

## What to measure

The first cohort is not a vanity traffic test. Measure these four things:

1. **Time to next action** — how long until the tester knows what to do next?
2. **Next-action comprehension** — can the tester explain why that action is first?
3. **Evidence comprehension** — can they distinguish verified evidence from uncertainty/missing evidence?
4. **Wrong/unsafe signal** — did CivicOS say anything misleading, overconfident, unsafe or materially incomplete?

Secondary observations:

- Did the tester understand the `Why?` view without help?
- Did they know what CivicOS *could not* conclude?
- Did they find the official route they needed?
- Did they want to take the proposed next action?
- What input did CivicOS ask for that felt unnecessary or invasive?

## Stop conditions

Pause the pilot and fix before inviting more users if any of these occur:

- CivicOS invents a deadline, entitlement, legal applicability or authority;
- a consequential action can execute without explicit human approval;
- uploaded personal document bytes are persisted unexpectedly;
- a high-risk document bypasses quarantine;
- a tester cannot distinguish an investigative lead from a wrongdoing finding;
- an access-control bypass is found;
- a real user reports materially harmful or dangerously overconfident guidance.

Every meaningful failure becomes a permanent regression fixture.

## Feedback

Use `.github/ISSUE_TEMPLATE/pilot-feedback.yml`.

Feedback deliberately asks for no names, case numbers, documents or sensitive information. Testers should describe issues using synthetic/redacted summaries.

## Promotion criteria

Do not expand beyond the trusted pilot cohort until:

- the pilot CI gate is green;
- at least 5 testers complete the core flows;
- no unresolved high-severity safety/privacy defect remains;
- the most common misunderstanding has been turned into a UI/product fix;
- domain review has begun for benefits and administrative-law language;
- a deployment/security review confirms the hosting configuration matches the pilot policy.
