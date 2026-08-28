# Deploy the CivicOS first-tester pilot

This is the deployment checklist for the invite-only first-user cohort.

## Safety property

A Vercel deployment is **fail-closed by default**.

If `VERCEL_ENV` is present and `CIVICOS_PILOT_MODE` was not explicitly set, CivicOS automatically enables pilot protection. If no invite secret is configured, protected write/research endpoints return `503` instead of becoming public.

This makes an accidental Git import safer, but the deployment is not ready to share until the runtime checks below pass.

## 1. Import the repository

Create a Vercel project from:

`https://github.com/mikelninh/CivicOs`

CivicOS declares its FastAPI entrypoint in `pyproject.toml`:

```toml
[tool.vercel]
entrypoint = "app:app"
```

## 2. Configure secrets before sharing

Set these for the environment you will give to testers:

```text
CIVICOS_PILOT_MODE=true
CIVICOS_PILOT_TOKEN=<long-random-secret>
CIVICOS_PILOT_SECURE_COOKIES=true
```

Optional:

```text
CIVICOS_MAX_UPLOAD_BYTES=5242880
CIVICOS_PILOT_RATE_LIMIT_PER_MINUTE=30
```

Generate the invite secret locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Never put the secret in Git, a URL, frontend JavaScript, screenshots, or public feedback.

## 3. Deploy over HTTPS

Use the normal Vercel preview/production deployment. Do not share an HTTP-only endpoint with `CIVICOS_PILOT_SECURE_COOKIES=false`.

The scheduled Watchtower remains a GitHub Actions concern; the public web deployment does not need a persistent SQLite filesystem for the first-user pilot.

## 4. Runtime acceptance checks

Before sending the URL to a tester, open:

### `/pilot/status`

Require:

```text
enabled = true
invite_secret_configured = true
secure_cookies = true
personal_evidence_persistence = false
```

### `/readiness`

Require:

```text
master_proof_ready = true
first_tester_pilot_ready = true
pilot_runtime_configured = true
public_beta_ready = false
```

`public_beta_ready=false` is expected.

### Unauthorized write check

Without logging in, a `POST /run` request must be rejected with `401`. If no secret was configured, it must fail closed with `503`.

### Login check

Open `/pilot`, enter the invite code and accept the pilot conditions. Confirm that the synthetic Benefits Graph flow works after login.

### Upload check

Use a synthetic `.txt` decision first. Confirm:

- Decision Review returns a result;
- audit metadata reports `persisted=false`;
- files larger than the configured maximum return `413`;
- unexpected file types return `415`.

## 5. Hosting/log review

Before using real redacted cases, inspect the deployment's runtime/build log configuration.

CivicOS does not implement request-body logging, but the hosting platform may process ordinary connection/operational metadata. Confirm the hosting setup matches the pilot disclosure and do not add middleware that prints request bodies, uploaded text, invite codes or cookies.

## 6. First cohort

Share the URL and invite code separately with **5–15 trusted adults**.

Ask them to:

1. run synthetic cases first;
2. explain the evidence and uncertainty back to you;
3. use a redacted real case only if they understand the boundary;
4. submit privacy-minimised feedback using the pilot issue template.

Do not post the invite code publicly.

## 7. Rollback / stop

Stop sharing the pilot immediately if a high-severity privacy, access-control or overconfidence defect is found.

Rotate `CIVICOS_PILOT_TOKEN` to revoke all existing signed pilot sessions, then redeploy after the issue is fixed. Every meaningful failure should become a regression test before reopening the cohort.
