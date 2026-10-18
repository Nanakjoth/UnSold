# Deploying UNSOLD (repo codename: Atlas) — operator runbook

One Cloud Run service: FastAPI + the built React SPA (multi-stage `Dockerfile`).
Gemini runs on Vertex AI through the runtime service identity — **no API keys,
no key files**. Firestore in native mode. This runbook is copy-paste ordered;
every step is idempotent or clearly marked one-time.

**Honest state of this codebase (2026-10-18):** the live-Gemini path has never
run from the dev machine (no credentials there). Everything below the "verify"
step is prepared and test-covered on the fallback path; the first real
`source: "gemini"` response happens in §5 on your project.

---

## 0. Prerequisites

- `gcloud` CLI installed and logged in: `gcloud auth login`
- A project with **billing enabled** and a **budget alert** set first (alerts
  notify you; they are not hard caps).
- Verify current Gemini model IDs and regional availability in the official
  _Gemini on Vertex AI_ docs before using any ID below. Nothing in this repo
  hardcodes a model ID; placeholders are rejected at startup in production.

Set your shell variables once:

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"   # must offer BOTH the chat and embedding models you pick
```

## 1. Configure the AI first — no deploy needed

This is the fastest way to prove the model wiring works, before any cloud
resource for the app exists.

```bash
gcloud auth application-default login          # ADC — no key files, ever
cp .env.example .env                           # then edit: real project, region, model IDs
#   GEMINI_MODEL=<current fast chat model id>  (verify in official docs)
#   EMBED_MODEL=<current embedding model id>   EMBED_DIM=<that model's output dim>
```

Run the app's own connectivity check **from the repo root** (so the root
`.env` is read), which makes exactly one real structured call through the
production code path and prints the honest label:

```bash
server/.venv/Scripts/python scripts/check_gemini.py     # Windows; server/.venv/bin/python on mac/linux
```

A friendlier, step-by-step version of §0–§1 lives in `docs/CONFIGURE_AI.md`.

| Exit | Meaning |
|---|---|
| 0 | `RESULT: gemini` — live path works. |
| 1 | `RESULT: fallback` — configured, but the call failed (see printed error: model ID, region, or permission). |
| 2 | Not fully configured — set the `GOOGLE_CLOUD_*` / `GEMINI_*` / `EMBED_*` variables. |

## 2. One-time cloud resources

Enable only what this stage needs:

```bash
gcloud services enable \
  run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  firestore.googleapis.com aiplatform.googleapis.com logging.googleapis.com \
  identitytoolkit.googleapis.com \
  --project "$GOOGLE_CLOUD_PROJECT"
```

Runtime service account, least privilege (no Owner/Editor):

```bash
gcloud iam service-accounts create atlas-run \
  --display-name="UNSOLD runtime" --project "$GOOGLE_CLOUD_PROJECT"

for ROLE in roles/datastore.user roles/aiplatform.user roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "$GOOGLE_CLOUD_PROJECT" \
    --member="serviceAccount:atlas-run@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com" \
    --role="$ROLE"
done
```

Firestore (native mode) + Artifact Registry repo:

```bash
gcloud firestore databases create --location="$GOOGLE_CLOUD_LOCATION" \
  --project "$GOOGLE_CLOUD_PROJECT"

gcloud artifacts repositories create atlas \
  --repository-format=docker --location="$GOOGLE_CLOUD_LOCATION" \
  --project "$GOOGLE_CLOUD_PROJECT"
```

## 3. Build and deploy

Canonical path — `cloudbuild.yaml` (build → push → deploy). The three
model-related substitutions have **no defaults on purpose**: the command fails
until you pass verified values.

```bash
gcloud builds submit --config cloudbuild.yaml . \
  --substitutions=_GEMINI_MODEL=<id>,_EMBED_MODEL=<id>,_EMBED_DIM=<dim>
```

Notes:

- The first deploy uses `--no-traffic`: nothing serves until you promote the
  verified revision (§5).
- `_APP_MODE` defaults to `production`. To put a fully clickable prototype
  online instead (demo routes on, synthetic-data banner visible — identical to
  what runs locally today), pass `_APP_MODE=demo`.
- Equivalent without `cloudbuild.yaml`: `gcloud run deploy atlas --source . …`
  (flags mirrored in README "Cloud deployment").

## 4. Seed the catalogue

Idempotent; prints per-collection counts. `app.seed` must run from `server/`
(the `app` package lives there) and reads `.env` from the directory you run
it in — so copy your root `.env` along:

```bash
cd server
copy ..\.env .      # Windows; cp ../.env . on mac/linux
python -m app.seed
```

## 5. Verify, then promote

```bash
export SERVICE_URL=$(gcloud run services describe atlas \
  --region "$GOOGLE_CLOUD_LOCATION" --format 'value(status.url)')

curl "$SERVICE_URL/healthz"            # {"ok": true}
curl "$SERVICE_URL/api/public/stats"   # aggregates only; accuracy stays unclaimed until ≥30 reviewed labels

# The AI check that needs no auth — the public Guardian playground:
curl -X POST "$SERVICE_URL/api/guardian/try" \
  -H "Content-Type: application/json" \
  -d '{"text":"Enroll now in my course at Brightpath Academy - limited seats!"}'
```

A pitch verdict whose JSON `source` reads **`"gemini"`** proves the live model
end to end (locally it has always been `"rules"`/`"fallback"`). A clean,
library-research text should stay `ALLOW`. Demo routes must be refused:

```bash
curl -X POST "$SERVICE_URL/api/dev/demo-login" -H "Content-Type: application/json" -d '{"label":"x"}'
# production: 404 (route not registered)
```

Cloud Logging should show structured `gemini_call` events with `status: "ok"`
and **no user content**. Then promote traffic:

```bash
gcloud run services update-traffic atlas --region "$GOOGLE_CLOUD_LOCATION" --to-latest
```

## 6. Known gap: browser sign-in on a production deploy

The React SPA today signs in only through `/api/dev/demo-login`, which
production mode does not register. So on an `APP_MODE=production` deployment:

- **Works from the browser:** home + composer (rules/fallback + Gemini behind
  the API), Explore, Trust page + Guardian playground, public stats.
- **Needs the not-yet-built Firebase anonymous-auth client integration:**
  submitting a need, sessions, reveal, feedback — anything that requires a
  verified user token.

Two honest options meanwhile: deploy with `_APP_MODE=demo` for a fully
clickable cloud prototype, or exercise write paths via the API with a Firebase
ID token. The Firebase client integration is a code task on this repo, not a
cloud setting.

## 7. Costs and safety

- Scale-to-zero by default (`--min-instances=0`); the API layer is pay-per-request.
- Guardian playground: anonymous, stores nothing, 10/min per IP.
- Global rate limit: 20/min per user/IP (single-instance in-process window).
- Deletion, retention (`DATA_RETENTION_DAYS`), and content-free logs behave as
  in `docs/PRIVACY_AND_SAFETY.md`.

## 8. Rollback and troubleshooting

Rollback: Cloud Run console → Revisions → promote the previous one (or
`gcloud run services update-traffic … --to-revision=<old>`).

| Symptom | Likely cause |
|---|---|
| App exits at startup mentioning placeholders | A `REPLACE_WITH_…` value reached production; set real IDs. |
| `PERMISSION_DENIED` on datastore | Service account lacks `roles/datastore.user`, or Firestore not created in the same region. |
| `PERMISSION_DENIED` on aiplatform | Service account lacks `roles/aiplatform.user`. |
| Model 404 / not found | Wrong model ID or the region lacks it — re-verify both together. |
| `embed_dim_mismatch` in logs | `EMBED_DIM` doesn't match the embedding model's output dimension. |
| `guardian/try` says `rules` not `gemini` | Client not configured (`cloud_configured` false) or the call failed — check `gemini_call` events in Logging. |
| 403 invoke from browser | Service deployed without `--allow-unauthenticated` (the advice front door is public; write routes are still auth-gated server-side). |
