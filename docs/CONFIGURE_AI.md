# Configure the LLM API — your personal checklist

This is **only** about one thing: making the app call the real Gemini model
instead of its built-in fallback. When you finish, `scripts/check_gemini.py`
prints `RESULT: gemini`, and from then on every classifier/interpretation
result produced with this configuration is honestly labelled `"gemini"`.

This does **not** deploy the app, create Firestore, or touch the website —
that's the later phase (`docs/DEPLOY.md`). Nothing here is irreversible, and
the whole thing takes about 30 minutes.

Work through the boxes top to bottom. Every command is copy-paste.

---

## ☐ 1. Install the gcloud CLI

Download: <https://cloud.google.com/sdk/docs/install> (Windows installer is
fine). Then open a **new** terminal and confirm:

```bash
gcloud --version
```

## ☐ 2. Create a project and add billing

1. Go to <https://console.cloud.google.com> → project dropdown → **New
   project** (any name, e.g. `ask-mentorship`).
2. Copy the **project ID** (the long lowercase one, not the display name) —
   you'll paste it into every command below as `YOUR_PROJECT_ID`.
3. **Billing** → attach a payment method to the project. (Enabling the APIs
   below costs nothing; you pay only when the model is actually called, and
   the one test call costs a fraction of a cent.)
4. **Budget alert** (strongly recommended): Billing → **Budgets & alerts** →
   create a budget for the project, enter your email, keep the default 50% /
   90% / 100% email thresholds. Remember: alerts *notify* you, they don't
   cap spending.

## ☐ 3. Enable the APIs (one command, free)

```bash
gcloud services enable aiplatform.googleapis.com run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com firestore.googleapis.com logging.googleapis.com identitytoolkit.googleapis.com --project YOUR_PROJECT_ID
```

Only `aiplatform` (Gemini) is needed for *this* checklist; the rest are for
the later deploy, and enabling them now means you never revisit this step.

## ☐ 4. Sign in — no key files, ever

```bash
gcloud auth login --project YOUR_PROJECT_ID
gcloud auth application-default login
```

The second command is the one the app uses ("Application Default
Credentials"). If your browser doesn't open automatically, follow the URL it
prints. **Do not** download any JSON key file — this project deliberately
never uses key files, anywhere.

## ☐ 5. Choose the two model IDs (the part you must not guess)

You need **two** models, verified against the official docs *today* — model
names change, and this repo hardcodes none:

- **Chat model** → goes in `GEMINI_MODEL`. Pick a current *fast* model
  (used for JSON classification and short mentor replies).
- **Embedding model** → goes in `EMBED_MODEL`, and its **output dimension**
  goes in `EMBED_DIM`. The dimension must match the model exactly — check
  what dimensions the model supports in the docs; don't assume.

Where to look (search for): **"Gemini on Vertex AI" models reference** in
Google's official `cloud.google.com/vertex-ai` docs. The model card there also
lists the regions it serves.

**Region** (`GOOGLE_CLOUD_LOCATION`, e.g. `us-central1`): pick one where
**both** models are available. If the check in step 7 fails with a
not-found/region error, this is the usual culprit.

## ☐ 6. Create your `.env`

From the **repo root**:

```bash
copy .env.example .env      (Windows)
cp .env.example .env        (mac / linux)
```

Open `.env` and set these five lines (leave `APP_MODE=demo` — production
mode is a deploy-time concern):

```
APP_MODE=demo
GOOGLE_CLOUD_PROJECT=your-real-project-id
GOOGLE_CLOUD_LOCATION=us-central1          <- the region you verified in step 5
GEMINI_MODEL=<the chat model id from step 5>
EMBED_MODEL=<the embedding model id from step 5>
EMBED_DIM=<that embedding model's output dimension>
```

This file is gitignored (`.env` is in `.gitignore`; only `.env.example` is
committed), so real values here can never be committed by accident.

## ☐ 7. Run the check (one real model call)

**Run from the repo root** so it picks up the `.env` you just made:

```bash
server\.venv\Scripts\python scripts\check_gemini.py      (Windows, repo has a venv)
server/.venv/bin/python scripts/check_gemini.py          (mac / linux, same)
```

On a **fresh machine** without the venv yet, create it first:

```bash
cd server
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt    (Windows)
.venv/bin/pip install -r requirements.txt        (mac / linux)
cd ..
```

What it does: prints your configuration, then makes **exactly one** real
structured call through the app's own prompt + schema path. It never fakes a
result.

## ☐ 8. Read the outcome

| You see | Meaning | What to do |
|---|---|---|
| `RESULT: gemini` (exit 0) | ✅ A real live model call succeeded through the production code path. **You are done** — the LLM API is configured. | Nothing. Deploy whenever you want (`docs/DEPLOY.md`). |
| `RESULT: fallback` (exit 1) | Configured, but the call failed. The printed `error` line says why. | See troubleshooting below. |
| exit 2, "not fully configured" | One of the five `.env` values is missing/placeholder. | Fix `.env` (step 6) and rerun. |

If it worked, you can also see it live later: whenever the app runs with this
`.env`, response `source` fields read `"gemini"` instead of `"fallback"`.

## Troubleshooting

| Error in output | Cause | Fix |
|---|---|---|
| `PERMISSION_DENIED` on aiplatform | Wrong project in `.env`, or ADC not done | Recheck `GOOGLE_CLOUD_PROJECT`; rerun `gcloud auth application-default login` |
| Model / publisher not found, or 404 | Model ID is wrong or outdated, or the region doesn't serve it | Re-verify the ID **and** the region together in the official docs (step 5) |
| `embed_dim_mismatch` (logged) | `EMBED_DIM` doesn't match the embedding model's actual output size | Set `EMBED_DIM` to the model's real dimension |
| Could not retrieve credentials / ADC errors | Step 4 wasn't run, or was run in a different terminal/user | Rerun `gcloud auth application-default login` |
| Quota / 429 | Per-project rate quota hit | Wait a minute and rerun; raise quota in the console if needed |
| `google-genai is required` | Python deps not installed in the venv you're using | Fresh-machine steps in §7 |

## What this does NOT do (so there are no surprises)

- **Does not deploy anything.** No website goes online; no Firestore is
  created. That's `docs/DEPLOY.md`, whenever you choose.
- **Does not change how the app behaves on this machine** until you run the
  server with this `.env` in scope — and even then, the fallback remains the
  safety net: if a model call ever fails, results fall back honestly instead
  of erroring or pretending.
- **Costs essentially nothing to run:** enabling APIs is free; the single
  test call is fractions of a cent. Ongoing model usage costs only when the
  deployed/running app is actually used.
