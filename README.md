# UNSOLD — advice without an agenda

**UNSOLD** gives a person working through a decision **independent, agenda-free
guidance** — anonymously, for free, from people with nothing to sell them a
course, clinic, or coaching package. *Anonymous human guidance, protected by
AI.* Advice is the core product; a discovery catalogue is a frozen add-on.
(`atlas` remains the repo/package codename.)

> **Status:** the advice core is built and verified. That is Stages **A1**
> (describe a need → scrub → interpret → grounded mentor matches → front-door
> UI), **A2** (in-app session + the **Guardian** anti-promotion layer + the
> Friend Test), **A3** (mutual-consent identity reveal + editable summary with
> next steps + dual-role feedback with a Guardian agreement metric), and **P3**
> (an honest evaluation harness: an 80-message gold set + eval runner). Demo
> seed data — 35 synthetic mentors and 10 sample mentee situations — is in
> place. Cloud features (live Gemini, Firestore, Firebase auth) are **prepared
> but never run live** — no credentials on this machine, and the app says so
> honestly rather than faking a model call. See `docs/PROJECT_EXPLAINED.md`
> §15 for the exact roadmap.

This repository is the application itself. It is not a competition entry.

## What the product does (and does not do)

- **Describe a situation, get grounded matches.** You write what you're facing
  in plain words. The text is scrubbed of PII, interpreted into an editable
  intent, and matched against up to three mentors — each with a written reason
  they fit, built only from that mentor's public card and your own intent.
- **Talk in a moderated session.** Every message runs through the **Guardian**,
  which blocks promotion, contact-solicitation, urgency/fear, and affiliate
  wording. A mentor gets three strikes and the session ends. For money
  decisions, the Friend Test tracks whether the mentor pushed you to spend.
- **Leave with something concrete.** After a session you get an editable
  summary with up to five next steps, plus 2–3 small things to try from the
  catalogue. You can request a mutual-consent identity reveal (anonymously
  pseudonymous until both sides agree).
- **Anonymity is the default.** No email, no password, ever. Identity is a
  server-generated pseudonym; the uid comes only from a verified token.
- **It is not** therapy, medical, legal, or financial advice; not a marketplace
  (no payments, ads, or affiliate links); not a dating or popularity product;
  and not an AI chatbot that pretends to be a person. Every AI-assisted result
  carries the *real* source — `"gemini"` only if a live model produced it,
  `"fallback"`/`keyword"` otherwise.

## Repository layout

```
server/    FastAPI app (Python 3.12) — advice core, sessions + Guardian,
           discovery add-on, matching, evaluation harness. Tests in server/tests
web/       React 19 + Vite 6 + TypeScript + Tailwind v4 frontend
scripts/   cross-cutting live smoke scripts (a2/a3/eval/scenarios) + eval + checks
server/scripts/  advice/discovery smoke scripts + catalogue + status-code validators
eval/      gold_set.jsonl (80 messages) + last_run.json (last eval result)
docs/      PROJECT_EXPLAINED, ARCHITECTURE, DECISIONS, PRIVACY_AND_SAFETY,
           AI_EVALUATION, PRODUCT_SPEC
```

## Running locally

Prerequisites: Python 3.12, Node 20+, npm. No Google Cloud credentials are
required for demo mode.

### Backend

```powershell
# Windows PowerShell
cd server
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\uvicorn app.main:app --reload --port 8080
```

```bash
# macOS / Linux
cd server
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8080
```

Demo mode seeds the 88-entry catalogue **and** the 35-mentor corpus
automatically on first boot when the store is empty. The frontend dev server
proxies `/api` and `/healthz` to port 8080, so run the backend there unless you
change the proxy.

> **`.env` is read from the directory you start the server in.** With a live
> Gemini configuration in the repo-root `.env`, start the backend **from the
> repo root** instead: `server\.venv\Scripts\uvicorn app.main:app --app-dir server --port 8080`
> (Windows) / `server/.venv/bin/uvicorn app.main:app --app-dir server --port 8080`
> (mac/linux). Started from `server/`, the app runs on built-in defaults
> (fallback classifier, demo mode) and ignores the root `.env`.

### Frontend (second terminal)

```powershell
cd web
npm install
npm run dev        # http://localhost:5173, proxies /api and /healthz to :8080
```

Open **http://localhost:5173** — you land on the advice front door, where ten
sample situations are one click away.

### Tests and checks

```powershell
cd server
.venv\Scripts\python -m pytest                    # 206 passing
.venv\Scripts\python scripts\validate_catalogue.py # catalogue integrity gate

cd ../server   # live smoke, with the backend running on 8080
..\scripts\smoke_a2.ps1      # session + Guardian + Friend Test end-to-end
..\scripts\smoke_a3.ps1      # need → session → reveal → summary → feedback → metrics
..\scripts\smoke_eval.ps1    # run the eval, confirm the Metrics page serves it
..\scripts\smoke_scenarios.ps1  # the 10 sample scenarios each match their mentor #1

cd ..\server
.venv\Scripts\python ..\scripts\run_eval.py       # re-run the offline Guardian eval
.venv\Scripts\python ..\scripts\check_scenarios.py # assert every scenario's #1 match
.venv\Scripts\python ..\scripts\check_gemini.py    # honest Gemini-config check (exit 2 if unconfigured)
```

### Serving the built SPA from the API (single-service mode, as deployed)

```powershell
cd web; npm run build          # produces web/dist
cd ../server; .venv\Scripts\uvicorn app.main:app --port 8080   # then open http://localhost:8080
```

### Seeding a real (non-demo) store

Seeding is never a side effect of booting the app. Run it explicitly:

```powershell
cd server; .venv\Scripts\python -m app.seed
```

It is idempotent and prints the per-collection counts it wrote.

## Configuration

Configuration is environment-only, validated at startup
(`server/app/config.py`). Copy `.env.example` to `.env` and edit. For a
step-by-step personal checklist covering only the LLM/Gemini setup (project,
APIs, auth, model IDs, one-call verification), see
**`docs/CONFIGURE_AI.md`**. Highlights:

| Variable | Meaning |
|---|---|
| `APP_MODE` | `demo` (local default) or `production`. Production refuses to start without complete Google Cloud configuration and never registers demo routes. |
| `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION` | Project and region for Google APIs. Required in production. |
| `GEMINI_MODEL` / `EMBED_MODEL` / `EMBED_DIM` | Model names/dimension. Used only when a live Gemini client is configured. Placeholder values are rejected in production mode. Verify current model IDs and regional availability in official docs before use. |
| `ENABLE_DLP` / `ENABLE_APP_CHECK` | Optional hardening gates, off by default. |
| `DATA_RETENTION_DAYS`, `MAX_QUERY_CHARS`, `RATE_LIMIT_PER_MINUTE` | Product limits (defaults 30 days, 300 chars, 20/min). |

No secrets live in this repository. Local development uses Application Default
Credentials (`gcloud auth application-default login`) once Google APIs are
used; Cloud Run uses its attached service identity. No service-account key
files.

## API surface (current)

All `/api` routes require `Authorization: Bearer <token>` unless marked public.
Errors return `{ "error": { "code", "message" } }`. The full route-by-route
list is in `docs/PROJECT_EXPLAINED.md` §11 (35 routes). Grouped:

- **Advice (core):** `POST /api/needs` (scrub → interpret → match → persist),
  `GET /api/needs/scenarios` (public sample situations), `GET /api/mentors`,
  `GET /api/mentors/{id}`.
- **Sessions + Guardian:** open/list/get a session, send messages, the mentor
  simulator's reply, end, Friend Test, reveal, summary (get/patch), feedback.
- **Discovery (frozen add-on):** `GET /api/interests*`, `/api/library/saved*`,
  `/api/library/feedback`.
- **Public trust surfaces:** `POST /api/guardian/try` (anonymous Guardian
  playground — stores/logs nothing, 10/min per IP) and `GET /api/public/stats`
  (aggregates only; `accuracy_claimed` stays false until ≥30 labels are human-
  reviewed).
- **Account:** `POST/PATCH/DELETE /api/auth/session`, `GET /api/config`,
  `GET /healthz`.
- **Demo-only (`/api/dev/*`, never registered in production):** `demo-login`,
  `reset`, `me`, mentor `impact`, Guardian + eval `metrics`.

## Authentication

- **Production:** Firebase anonymous-auth ID tokens, verified server-side with
  the Admin SDK (Application Default Credentials). Initialization is lazy, so
  the app starts without credentials but refuses unverified requests.
- **Demo (`APP_MODE=demo`):** the API mints short-lived HMAC-signed tokens via
  `POST /api/dev/demo-login {"label": "a-name"}`. These run through the *same*
  verification and ownership code paths as production — the uid is never taken
  from a request body or query parameter.

## Privacy and data handling

Full details in `docs/PRIVACY_AND_SAFETY.md`. Summary:

- Synthetic identities and labelled sample content throughout; a visible
  banner shows this in demo mode.
- **PII is scrubbed before storage and before any model call** (emails, phones,
  URLs, handles, names → tokens). Raw PII never reaches the store or a prompt.
- **Deletion deletes.** `DELETE /api/auth/session` removes the user record and
  every record they own — needs, sessions, messages, feedback, saved interests,
  discovery feedback — and returns exact per-collection counts.
- **Retention:** `DATA_RETENTION_DAYS` (default 30) plus `retention.purge_expired`
  for records stamped with `expires_at`.
- **Rate limiting:** per-user (falling back to per-IP) sliding window, default
  20/min, `429` with `Retry-After`.
- **Logs:** structured, content-free events only. Long free-text values are
  defensively truncated.
- Client-side Firestore access is deny-by-default (`firestore.rules`); the
  React app talks only to the API.

## Cloud deployment (operator steps)

Step-by-step runbook with exact commands: **`docs/DEPLOY.md`**. Requires
Google Cloud access; not runnable from this machine (no `gcloud` CLI
installed). Summary:

1. Create/choose a project; set billing **budget alerts** before enabling
   anything (alerts notify, they are not hard caps).
2. Enable only what the current stage needs: Cloud Run, Cloud Build, Artifact
   Registry, Firestore, Gemini API, Cloud Logging.
3. Create the runtime service account with least privilege. Do not grant
   Owner/Editor. No key files — Cloud Run uses the attached identity.
4. Create Firestore (native mode) in the intended region.
5. Seed the catalogue: `python -m app.seed` with production env vars.
6. Deploy (verify current flags first):

   ```bash
   gcloud run deploy atlas \
     --source . \
     --region "$GOOGLE_CLOUD_LOCATION" \
     --service-account "atlas-run@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com" \
     --set-env-vars "APP_MODE=production,GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION},GEMINI_MODEL=${GEMINI_MODEL},EMBED_MODEL=${EMBED_MODEL},EMBED_DIM=${EMBED_DIM}"
   ```

7. After deploy: check the URL opens, `GET /healthz` returns `{ "ok": true }`,
   demo routes are refused, and logs contain no user content.
8. Rollback: promote the previous revision in the console.

Scale-to-zero is the default (min instances 0) for credit-conscious
development. A `Dockerfile`, `firestore.rules`, and `cloudbuild.yaml` are
provided; `docs/DEPLOY.md` walks through build, deploy, and verification
(including the no-auth `POST /api/guardian/try` check that proves the live
model end to end).

## Known gaps (honest list)

- **Live Gemini now runs and is verified** (2026-10-18): `check_gemini.py`
  returned `RESULT: gemini` and `POST /api/guardian/try` answered with
  `source: "gemini"` through the app itself. The first live run exposed a real
  bug in the never-exercised path — `genai.Client` was missing the required
  `vertexai=True` — which is fixed. The deterministic fallback remains the
  safety net: any failed/absent model call falls back honestly, and results
  still carry their true `source` label.
- **The React SPA has no Firebase anonymous-auth integration yet.** It signs
  in only through the demo route (`/api/dev/demo-login`), which production
  mode does not register. On an `APP_MODE=production` deploy the public
  surfaces work from the browser, but submitting a need / using sessions
  requires the client-side Firebase integration (a code task) or a
  `demo`-mode deployment. `docs/DEPLOY.md` §6 spells this out.
- **Cloud deployment is prepared but not executed** from this machine (no
  `gcloud`/Docker). `scripts/check_gemini.py` reports the real configuration
  state (exit 2 when unconfigured) and never fakes a call.
- **The evaluation gold set's 80 labels are machine-generated and all marked
  `unreviewed`.** Until a human reviews ≥30 of them (spec §12), the
  precision/recall/F1 on the Metrics page describe the current deterministic
  behaviour, **not** proven accuracy. The page states this outright.
- **The Guardian's rules cover English + Spanish phrase sets** plus
  language-agnostic contact regexes; a live Gemini classifier would widen this.
  Stated rather than hidden.
- **A3 nuance:** the mentor's reveal-consent is simulated (mentors don't
  authenticate in this prototype), and the mentor-impact + metrics routes sit
  behind `/api/dev/...` because there is no mentor auth to scope a production
  route to.
- **FirestoreStore, Firebase verification, and the multi-stage Dockerfile** are
  implemented but lazy and unexercised here for lack of credentials/Docker.
- **Discovery is a frozen add-on** (88 entries, 151 relationships). It works
  end-to-end but is deliberately not the headline; no new discovery features are
  planned while the advice core is the focus.
