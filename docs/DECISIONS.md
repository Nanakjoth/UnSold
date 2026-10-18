# Decisions & Assumptions

Decisions made without asking clarifying questions, per build spec §0. Each
entry: what was decided, why, and when it can be revisited. This file replaces
the root `ASSUMPTIONS.md`, whose history is preserved below.

## 2026-10-18 — Rebrand: the product is UNSOLD

Operator directive: the product's name, brand, and tagline are set — applied
to every user-facing surface (repo/package stays `atlas`):

- **Name: `UNSOLD.`** (period part of the mark, rendered in accent as a
  "node dot"). Wordmark in the nav + footer, nav home item, `<title>`
  ("UNSOLD — Advice without an agenda"), meta description, README heading.
- **Tagline: "Advice without an agenda"** — the hero eyebrow.
- **Line: "Advice from people with nothing to sell."** — leads the hero
  sub-line, merged with the existing honesty clause ("…anonymous, free, and
  screened so advice can't quietly become a sales pitch").
- **Brand concept: "Anonymous human guidance, protected by AI."** — footer
  tagline and meta description.
- Deliberately **kept**: the H1 sentence ("Ask for honest guidance…") — "ask"
  there is a verb, the product promise, not the brand; sample strings like
  "Ask for the salary band…" likewise. Previous DECISIONS entries naming
  "Atlas"/"Ask" stand as history; this entry supersedes them.

Revisit when: any naming work touches marketing assets, OG images, or the
deployed service name (`atlas` on Cloud Run is internal, not user-facing).
## 2026-10-18 — Live Gemini verified: first real model call, and the bug it exposed

Operator filled the root `.env` (project `ai-cup-work-2026`, `location=global`,
`gemini-3.5-flash-lite`, `gemini-embedding-001`, dim 768). First-ever run of
the live path surfaced a real bug and then succeeded:

- **Bug: `genai.Client` was missing `vertexai=True`** in
  `gemini.py::_ensure_client`. Without it the SDK treats `project`/`location`
  as a Google-AI-API request and raises `ValueError: Missing key inputs…`
  before any HTTP — which the honest fallback machinery correctly caught and
  labelled (`source: "fallback"`, exit 1). This was exactly the "live path
  never exercised" gap. Fixed with a comment; `location: "global"` is natively
  supported by google-genai 1.2.0 (routes to the global Vertex endpoint).
- **Verified twice:** `check_gemini.py` → `RESULT: gemini` (exit 0), then
  through the running app itself: `POST /api/guardian/try` →
  `BLOCK_AND_REDACT / DIRECT_PROMO / severity 3` with `source: "gemini"`.
  The app's own Guardian prompt + schema validated a real model response.
- **ADC now exists on this machine** (operator ran the gcloud login), so the
  environment constraint "no gcloud/ADC here" is partially retired: model
  calls are live locally; the Cloud Run deploy itself remains an operator
  step (`docs/DEPLOY.md`).
- **`.env` is CWD-scoped** (pydantic-settings resolves `env_file=".env"` from
  the working directory). The canonical local run command for live AI is
  therefore from the **repo root**: `uvicorn app.main:app --app-dir server`.
  README quickstart documents this; started from `server/`, the app runs on
  built-in demo defaults and ignores the root `.env`.
- Docs synced: README known-gaps ("live Gemini has never run" retired),
  PROJECT_EXPLAINED gaps, DEPLOY.md seeding/check CWD fixes.

Revisit when: embeddings are exercised for real (the structured/text path is
what's verified today), and after the first Cloud Run deploy.

## 2026-10-18 — Neural backdrop behind the home hero (neural_backdrop_build_brief.md)

Implemented the canvas network background per the brief, with these calls:

- **Seeded RNG (mulberry32, fixed seed)** for the layout: same page every
  reload; the pure geometry lives in `web/src/lib/neuralGraph.ts`
  (buildGraph / projectPoints / depthOf — no DOM, deterministic for a seed).
- **`--color-accent-2` token added** (dark `#4da3ff`, light `#1d6fe0`) — the
  brief reads it for links/"you" node and it didn't exist yet. Dim nodes fall
  back to a theme-aware neutral; light mode darkens them for visibility.
- **Replaced `Constellation.tsx` in the hero** (file deleted as dead code):
  the static SVG constellation was the placeholder for exactly this role.
  The backdrop stays mounted after matches arrive; three hero links light up
  (`highlight` = first 3 match indices) and clear while a new request runs.
- **Phase 2 `flash` prop implemented in the component but deliberately NOT
  wired** to the Guardian playground: the only playground instances sit below
  the hero (off-screen; the backdrop pauses there) and behind a form, and the
  brief's own placement rule forbids mounting the effect behind forms or
  anywhere but the hero. Wiring needs a product decision first.
- **Adaptive quality** per the brief: measured draw cost over the first ~2s;
  above 8ms average it halves node count once, then settles to a static
  frame; never degrades repeatedly.
- **No test runner exists in `web/`** and the brief says do not add one —
  verified manually instead: headless-Edge screenshots (dark, light,
  reduced-motion static frame, real hero), zero console errors, tsc/vite
  build clean. Real-device frame timings honestly **not measured**.



Asked to get the project deployable so the operator (who owns all Google Cloud
access) can configure the real Gemini path. What was decided without asking:

- **`cloudbuild.yaml` written** (build → Artifact Registry → Cloud Run with
  `--no-traffic` first). The three model substitutions (`_GEMINI_MODEL`,
  `_EMBED_MODEL`, `_EMBED_DIM`) deliberately have **no defaults**: submit fails
  until an operator passes verified values, so a stale model ID can never be
  baked in by this repo. Model IDs remain the operator's decision per the
  standing "verify current IDs in official docs" rule.
- **`docs/DEPLOY.md` is the single runbook** (README links to it): configure
  AI locally via ADC + `check_gemini.py` *before* deploying; one-time
  resources (budget alert, 6 APIs, least-privilege SA, Firestore, Artifact
  Registry); deploy; seed; verify; promote; rollback; troubleshooting table.
- **The no-auth AI verification is `POST /api/guardian/try`**: the public
  Guardian playground exercises the exact live classifier path, so "is the
  model live?" is answerable from a browser with zero auth — its `source`
  flips from `"rules"` to `"gemini"` when the live path works.
- **New honest gap recorded (README + runbook §6): the SPA has no Firebase
  anonymous-auth client integration.** Production mode registers no demo
  login, so on a production deploy the browser can use every public surface
  but cannot submit a need. Options stated, not hidden: `_APP_MODE=demo`
  deploy for a fully clickable cloud prototype, or API-level writes with a
  Firebase ID token. The client integration is a future code task.
- **Runtime identity is the Cloud Run service account** (datastore.user,
  aiplatform.user, logging.logWriter). No key files anywhere, consistent with
  the existing ADC-only stance.

Revisit when: the operator runs the runbook (first real `source: "gemini"`)
and when the Firebase client integration is built.



Full restyle executed per `ui_redesign_spec.md`. Assumptions made without
asking — each reversible:

1. **Name stays "Atlas" / "Ask"** — the spec leaves renaming open ("decide the
   name"). The wordmark, `<title>`, and footer now read **Ask** (the product
   verb) while repo/package names keep `atlas`. A real rename is a find-replace
   if a name is chosen later.
2. **Dark-first, light available** (spec §12 decision). Dark is the default
   and the pre-paint theme; a persisted toggle (`atlas.theme` in localStorage)
   flips `html[data-theme]`. The spec's dark palette (#0B1113 / #121B1F /
   #EAF1F2 / #34D399) is the default `@theme`; the previous light palette is
   the override, so **token names never changed** — every existing page
   restyled without per-page edits (only journey pages got structural work).
3. **Nav = Ask · Sessions · Explore · How it works · Trust** per the UI spec —
   this supersedes the earlier "Advice · My sessions · Explore" naming but not
   the scope freeze: mentors stay secondary, no social surfaces. "How it works"
   is an in-page anchor on `/`; "Trust" is the new `/trust` route. Metrics stays
   footer-linked.
4. **Fonts loaded from Google Fonts** (Space Grotesk / Inter / JetBrains Mono)
   with preconnect + `display=swap` and full system fallbacks — no new package
   dep, degrades cleanly offline. Swap if a self-hosted bundle is wanted.
5. **Hero = static constellation + CSS-only motion** (spec's "ship static
   first"): an SVG of You → Guardian → Mentor with a halo drift and node pulse.
   Every animation is disabled under `prefers-reduced-motion`; no canvas/WebGL.
6. **Three-step submit progress** (Strip PII → Read intent → Match mentors)
   animates on a timer while the single real request runs — the labels name
   steps that genuinely happen server-side, and completion is driven by the
   actual response, never a fake finish.
7. **Mint buttons take dark ink in dark mode** — white on #34D399 fails 4.5:1,
   so `html[data-theme="dark"] .bg-accent.text-white` flips to #052E22; light
   mode keeps white-on-green. This keeps every pre-existing button compliant
   without editing each one.
8. **Playground honesty**: `POST /api/guardian/try` stores/logs nothing (see
   the endpoint entry below), the UI states that per the spec's required copy,
   429 is explained as "the rate limit doing its job", and the classifier
   source label (AI vs rules) is shown on every verdict.
9. **Transparency numbers render only what `/api/public/stats` returns** —
   no eval run ⇒ "no numbers are shown" rather than placeholders; the
   not-accuracy caveat shows whenever `accuracy_claimed` is false (currently
   false: 0/80 labels reviewed).

Revisit: rename, self-hosted fonts, animated (non-static) constellation.

## 2026-10-18 — Public trust endpoints (guardian/try + public/stats)

UI redesign asks for two PUBLIC routes that make the honesty claims checkable
without an account. Both are additive; no existing behaviour changed.

1. **`POST /api/guardian/try`** (routes/public.py) — the trust proof: paste a
   message, see the REAL Guardian verdict, with zero persistence. It reuses the
   exact session pipeline (`scrub()` then `screen_message()`), never writes to
   the store, and logs only aggregates (lengths/categories/actions — never the
   text). Decisions:
   - *Screened as sender_role "mentor"* — pitch semantics are defined for
     mentor messages (a mentee is never labelled a pitcher, spec 10.5), so the
     playground screens what the Guardian exists to judge.
   - *Dedicated per-IP limiter (10/min)* — the global `RateLimiter` is
     constructed with one app-wide threshold and cannot take a custom
     per-route one, so the router module carries its own `RateLimiter(10)`
     keyed `guardian_try:<ip>`, raising the same `_RateLimited` → 429 +
     Retry-After path. In-process like the global one (honest about it).
   - *`ApiError(400, "text_too_long", ...)` directly* — the `bad_request()`
     helper hardcodes code `bad_request`; the spec wants a distinguishable
     code, so the route raises the shared `ApiError` with its own code (same
     envelope). Empty-after-strip is a Pydantic validator → 422 like any other
     request-validation failure.
   - *No optional-auth dependency* — the codebase has no "optional verified
     user" pattern (`current_verified` raises when the header is absent), so
     the route is purely public; it works identically for anonymous and
     signed-in callers because it ignores identity entirely.
2. **`GET /api/public/stats`** (routes/public.py) — aggregates only: mentor
   corpus count + all_synthetic, the latest eval run (from
   `eval/gold_set.jsonl` + `eval/last_run.json`, same repo-root path convention
   as routes/dev.py; null when absent/unreadable), and the agreement metric
   shown only at >= 3 samples. `accuracy_claimed` is gated at >= 30
   human-reviewed gold labels (spec 12) — today 0 of 80 are reviewed, so the
   panel honestly reports rule behaviour, not accuracy. Registered in BOTH
   demo and production (verified by test): it exposes no member data, ids, or
   per-record rows.

Revisit when: a distributed rate limiter is needed; the eval artifacts move
into the store; or live Gemini traffic makes playground volume a cost factor.

## 2026-10-18 — Full documentation sync + a real deletion bug found and fixed

User request: update the docs (PROJECT_EXPLAINED and the rest) so it's clear
**what changed and what the current state is**. While auditing the docs against
the code to make every claim true, one claim did not hold up — so it was fixed
in code, not papered over in prose.

**Bug found and fixed (deletion gap, spec §8 "deletion deletes"):**
`retention.delete_user_data` still only cleared the three *discovery-era*
collections (`users`, `saved_interests`, `discovery_feedback`). Stages A1–A3 had
since added four advice-core collections — `needs`, `sessions`,
`session_messages`, `session_feedback` — that carried a user's own free text and
were **silently left behind** after `DELETE /api/auth/session`. The API kept
reporting success, so a member could believe their advice history was gone when
it wasn't.

Decisions and why:

1. **Fix in code, not docs.** The honest move was to make the promise true
   (`delete_user_data` now cascades: needs by `user_id`, then for each session
   the member opened, its messages and feedback by `session_id`), not to soften
   the docs to match the old buggy behaviour. Ownership fields differ per
   collection (`user_id` / `mentee_id` / via `session_id`), so the cascade
   collects the member's session ids **before** deleting the sessions, then
   clears the dependents.
2. **Pinned by two tests** (`tests/test_retention.py`): one drives a full
   need → session → message → mentor-reply → end → feedback flow over the real
   HTTP API and asserts every collection is emptied *and* reported in the
   deletion counts; the other asserts one member's delete never touches another
   member's session or messages. Suite now **188 passing** (was 186).
3. **Docs updated to the true current state, not a rewrite of history:**
   - `README.md` was still describing the pre-realign "Global Discovery
     Platform / Stage 1 of 5" product with the wrong nav and a discovery-only
     API table. Rewritten to describe the advice core, the real 33-route surface
     grouped by area, the demo/production split, the honest known-gaps list
     (unrun Gemini, `unreviewed` gold-set labels, simulated mentor side), and
     the ports note (Vite proxies to **8080** — a stale server there returns
     old routes while a smoke against 8081 passes).
   - `PROJECT_EXPLAINED.md`: removed the stale "Still to come (A3)" (A3 is
     done) and replaced it with the built Step-7 (reveal/summary/feedback);
     added the seed-data row to the roadmap; recorded the deletion bug alongside
     the three earlier real bugs; corrected the running/ports note; 188 tests.
   - `PRIVACY_AND_SAFETY.md`: the storage table was missing all four
     advice-core collections and still said "messaging does not exist yet" and
     "no automated moderation exists" — both false now that sessions + the
     Guardian are built. Added a Guardian section, the deletion cascade, the
     real AI-honesty story (scrub-before-model, source labels), and rewrote the
     known-limits list.
   - `ARCHITECTURE.md`: was discovery-only (scrubbing labelled "for future
     free text", no advice collections). Rewritten to the current tree, the
     full data model, the matching + Guardian flow, and the P3 eval harness.
   - `AI_EVALUATION.md`: still framed as a "Stage 3 discovery search" plan that
     was never built. Rewritten to describe what is actually evaluated today —
     the **Guardian** (80-message gold set, split, runner, metrics, the
     `unreviewed`-labels caveat) — plus the still-unrun live-model plan and the
     honest cost-tracking gap.
   - `PRODUCT_SPEC.md`: got a superseded banner pointing to
     `unsold_product_spec.md` + `CORE_REALIGNMENT.md` as the spec of record;
     kept intact as the record of the frozen discovery add-on.
4. **No behaviour changed** beyond the deletion cascade. Nothing else in the
   product was touched in this pass.

**Revisit:** when a staffed moderation console, real mentor accounts, or cloud
deletion (Firestore batch deletes) arrive, re-audit `delete_user_data` so the
cascade and its reported counts stay literally true.

## 2026-10-18 — Demo seed data: 5 focus mentors + 10 sample scenarios

User request: add synthetic data for **5 mentors** (2 AI-career, 2 startup
founders — one tech + one non-tech, 1 meditation) and **10 mentee situations**
across different domains, each engineered so that describing it and searching
surfaces *that* mentor. `unsold_product_spec.md` §14 (seed data) is the source.

Decisions and why:

1. **The 5 mentors extend the existing 35-card corpus** (30 base + 5 focus)
   rather than a separate list, so matching, the directory, and sessions all see
   them with no special-casing. Each uses the corpus's controlled domain
   vocabulary (career/data/software/business/money/wellbeing) so the
   deterministic matcher ranks them; topics are phrased the way a mentee would
   describe the situation (e.g. "switching into an AI career").
2. **The 10 scenarios live in `server/app/sample_scenarios.py`** with an
   `intended_mentor_id` (2 per mentor). They are **sample content**
   (`is_sample_content=True`), fictional, and served publicly at
   `GET /api/needs/scenarios` (no auth — they're generic front-door prompts a
   visitor could have typed). The `intended_mentor_id` is a build-time seed
   hint that a test asserts against; it is never consulted at match time (matches
   are computed from the corpus per request).
3. **Each scenario is engineered to rank its mentor #1** by aligning its text to
   that mentor's domains + topics. Two rewrites were needed to avoid accidental
   keyword traps: the substring "tech" inside "technical"/"tech background"
   trips the software-domain keyword and pulled the tech-founder mentor into the
   two *non-tech* business scenarios; "machine learning" in an AI-career
   scenario over-weighted the data domain and let the upskilling mentor win.
   Both fixed by rewording, verified by `scripts/check_scenarios.py` (10/10 #1).
4. **Wellbeing lexicon gained meditation terms** (`meditat`, `mindful`,
   `racing mind`, `breathing`, `unwind`, `switch off`, `decompress`, `calm my`,
   `quiet my mind`) so a meditation scenario detects the `wellbeing` domain —
   a plain-language need must not silently fall to `no_strong_match`.
5. **The Advice front door's 3 hardcoded examples were replaced** by these 10
   fetched scenarios, grouped in a 2-up grid with a domain label and a "money
   involved" tag that also pre-ticks the money checkbox — so a click sets up the
   exact situation (text + money flag) the scenario was written for.

Verification: `server/tests/test_scenarios.py` (4 tests — endpoint serves 10,
covers the 5 focus mentors, **each scenario ranks its mentor #1**, corpus is 35)
→ **186 total backend tests pass**; `npm run build` clean; live smoke
`scripts/smoke_scenarios.ps1` (10 served, 5 in directory, meditation + non-tech
scenarios match their mentor #1 over the real HTTP path).

## 2026-10-18 — Stage P3: honest evaluation (gold set + eval runner)

`CORE_REALIGNMENT.md` §5 P3 ("Evaluate honestly") and `unsold_product_spec.md`
§12 are the source. The stage after A3 is the evaluation harness — **not** the
profiles/quality-view work sketched loosely earlier; that was an invented
side-path and is corrected here (the instruction is to follow the two spec docs
strictly).

Decisions and why:

1. **The gold set is generated, then marked `unreviewed` until humans review it.** Spec
   §12: "LLM-written labels are not ground truth." `generate_gold_set.py` emits the
   exact spec shape — 80 rows: 40 clean (20 plain + **20 hard negatives**), 40 pitches
   (10 direct, 15 contact, 8 urgency/fear, 7 subtle/affiliate) — every row starting
   `review_status: "unreviewed"`. The Metrics page and the eval report both say the
   numbers are *current behaviour, not accuracy*, until ≥30 rows are reviewed. Revisit
   when a second human reviewer is available (spec wants two people on ≥30 rows).
2. **Split by index (even→dev, odd→test) so `dev`/`test` are stable** across
   regenerations. Tuning happens on `dev` only; reported metrics come from `test`
   (spec §12). 40/40 split.
3. **The scorer is pure and reusable** (`server/app/evaluation.py`): `evaluate(rows,
   predict)` takes labelled rows + any predictor, so the real `classify_fallback` and
   a test stub both satisfy it structurally. It reports precision/recall/F1,
   per-category recall, hard-negative FPR, and the confusion matrix — all with the
   sample size and split baked into the result. Never a bare percentage.
4. **A predicted pitch = `is_pitch` OR severity ≥2**, mirroring production (severity 2
   maps to WARN/BLOCK, so that is what a reviewer would call "flagged").
5. **The eval drove real rule tuning.** The first run scored recall 0.400 (precision
   1.000, hard-neg FPR 0.000) — the deterministic rules missed urgency/fear, affiliate,
   soft-steering, and several off-platform contact phrases. These are categories spec
   §10.5 *requires* the Guardian to catch, so the phrase sets were widened (EN + ES).
   Result on `test`: **recall 0.400 → 0.950, precision held at 1.000, hard-negative FPR
   stayed 0.000** — no clean advice newly blocked. This is category coverage, not
   test-set memorisation, but it is stated plainly so a reviewer can re-check on fresh
   rows.
6. **The eval run is served by a demo-only route** (`/api/dev/metrics/eval`), reading
   `eval/last_run.json`. In production this belongs behind an operator view; there is
   no auth scope for it in the prototype, so it stays demo-only like the impact and
   metrics routes.

Verification: `server/tests/test_evaluation.py` (12 tests — split isolation, perfect
score, FP/FN handling, hard-neg FPR, per-category recall, review-status honesty,
gold-set shape) → **182 total backend tests pass**; `npm run build` clean (61 modules);
live smoke `scripts/smoke_eval.ps1` (eval served with n=40, recall ≥0.9, precision 1.0,
hard-neg FPR 0.0, `review_status: unreviewed`).

## 2026-10-18 — Stage A3: reveal, editable summary, feedback, agreement metric

Release 1 of the advice core (`CORE_REALIGNMENT.md` §5 P2, acceptance: full run
"need → feedback" ends with an agreement number on a metrics view).
`unsold_product_spec.md` §7/§8/§9/§10.8/§10.11 is the source.

Decisions and why:

1. **Reveal locks once REVEALED.** Spec §8 says "either side may withdraw before
   REVEALED", so withdrawal is offered only in NONE/ONE_SIDED. After both sides
   consent the contacts are treated as shared; a second consent call returns 400
   with a plain-language explanation. Revisit when real two-sided auth exists.
2. **The mentor's consent is simulated.** Mentors never authenticate in this
   prototype, so the synthetic mentor "consents back" when the mentee does —
   honestly labelled (`RevealContact.is_simulated=true` on the mentor side). This
   keeps the state machine genuinely two-sided and exercisable without faking a
   human. Revisit at mentor auth (later release).
3. **Reveal exposes display names + optional contacts only** — never a real
   identity. The offered contact is scrubbed before storage (spec §8), so a raw
   phone number typed into the reveal field cannot be persisted; verified by test
   and smoke.
4. **A summary is generated once, then owned by the mentee.** Regeneration never
   clobbers an edited summary (`edited` flag). Action items are capped at 5 (spec
   §10.8) and every produced line is re-scrubbed before storage — belt-and-braces
   against a model smuggling contact details into a summary. `source` stays
   honest: "gemini" only when a live model drafted it.
5. **"Things to try" uses the existing keyword retrieval** over the need's
   domains + text (`search_interests`), returning 0–3 entries rather than padding
   to always show 3. Catalogue is sample content, and the summary labels
   generated content honestly (CORE_REALIGNMENT C3).
6. **Agreement excludes "unsure" and hides below 3 samples** (spec §10.11,
   P2.4). The share is never returned without `sample_size`, and the two
   sub-counts (Guardian-flagged vs mentee-reported) always accompany it so the
   number is never unexplained. Everything is labelled `is_simulated` while
   mentors are synthetic. The math is `(felt_pitched=="yes") == (max_severity>=2)`.
7. **Feedback disagreements are logged for human review, never auto-actioned**
   (spec §10.11). A mentee saying "yes" when the Guardian saw severity <2 (or vice
   versa) writes a `disagreement` field + an audit event — no automatic strike,
   downgrade, or ban.
8. **Mentor impact + Guardian metrics routes live behind the demo router**
   (`/api/dev/...`). There is no mentor auth in this prototype, so a production
   `/mentors/me/impact` would leak private stats through a public path. Demo-only
   keeps the production surface honest; in production both require a signed-in
   mentor scoped to their own record (spec §9). The public mentor card is tested
   to never expose `stats`.
9. **Feedback model naming: `SessionFeedbackCreate/SessionFeedbackResponse`.**
   The A3 names initially shadowed the discovery-feedback `FeedbackCreate/
   FeedbackResponse` the library route imports (broke 4 tests) — renamed instead
   of touching the discovery path (scope freeze: discovery stays untouched).
10. **Mentee feedback updates quality with a Bayesian-flavoured blend**
    (prior weight 3), so one rating can't swing a mentor's score; strikes in the
    session penalise quality, clean sessions nudge it up (spec §10.11/§13).

Verification: `server/tests/test_a3.py` (30 tests — reveal machine incl. lock &
withdraw, summary editability/cap/scrub, feedback validation & dupe rejection,
agreement math incl. sample gating & unsure-exclusion, impact, public-card
privacy) → **170 total backend tests pass**; `npm run build` clean (61 modules);
live smoke `scripts/smoke_a3.ps1` — full run need → session → salesy BLOCK →
reveal (scrubbed contact, locked after) → end → summary (fallback, 3 things to
try, edit survives regeneration) → mentee + mentor feedback → agreement (hidden
at 1 sample) → metrics → impact → public-card privacy.

## 2026-10-18 — Stage A2: sessions, the Guardian, and the Friend Test

Built the differentiator that `CORE_REALIGNMENT.md` §5 P1 identified as missing.
`unsold_product_spec.md` §7/§9/§10.5/§10.6/§10.12 is the source.

**The Guardian's one non-negotiable rule (spec §10.5): the ACTION is decided by
deterministic code, never by the model.** `guardian.py` runs a fixed pipeline —
rules → (Model Armor seam) → classifier → `decide()`. A classifier (Gemini when
live, a deterministic fallback otherwise) only proposes a `(category, severity,
money_stance)`; code maps severity to `ALLOW`/`WARN`/`BLOCK_AND_REDACT`. This is
what makes the safety behaviour testable: a prompt-injection cannot talk the
model into passing a pitch, because the model does not choose the action.

Decisions and why:

1. **Scrub runs BEFORE the Guardian** (spec §8), so the Guardian classifies the
   scrubbed text. Raw PII never reaches a prompt. Consequence: the Guardian
   detects the scrubber's *tokens* (`[PHONE]`, `[EMAIL]`, `[OFF_PLATFORM_REQUEST]`,
   `[URL]`) as contact evidence rather than re-deriving the values. Raw-PII
   regexes are kept as defence-in-depth only.
2. **A bare URL is severity 1 (allow+log), not a block** — it may be a legitimate
   free resource, and the spec's hard negatives require free-resource advice to
   pass. Contact *details* and off-platform *requests* are severity 3.
3. **Stacked promo signals escalate to severity 3.** The spec wants the "obvious
   pitch" shape (enrol + limited seats + use my code) *blocked*, not merely
   tagged. Three or more distinct promo-family signals = clear promotion.
4. **Spoken phone numbers are detected.** "five five five one two three four"
   evades both the scrubber's digit regex and naive rules, so the Guardian counts
   runs of number-words: ≥6 consecutive = a phone number (block), 4–5 = ambiguous
   counting (warn).
5. **The rules layer is bilingual (English + Spanish).** The spec's eval list
   requires "another language" to be caught. Contact regexes are language-agnostic
   by construction; phrase sets cover EN + ES. This is stated as a limitation, not
   hidden — a live Gemini classifier would widen it.
6. **Distress is read from ONE lexicon.** `matching.detect_distress` is shared by
   the need interpreter and the Guardian's `safety` field, so a message flagged
   mid-session reads the same as one flagged when describing a need. `GuardianSafety`
   was widened to the app's 4-level `DistressLevel` for that consistency.
   Distress is **never** a reason to block; it is surfaced, not punished.
7. **Only MENTOR strikes count.** A mentee leaking their own phone number is
   redacted for privacy but never labelled a pitch or struck. Three mentor strikes
   end the session and reset that mentor's `pitch_free_streak` (spec §10.5/§13).
8. **`display_text` vs `text_scrubbed`.** The stored record keeps the scrubbed
   original (for audit); the recipient-facing `display_text` is the redaction
   notice when blocked. They differ only on a block.
9. **Friend Test rollup (spec §10.6):** latest non-`n/a` stance, except
   `pushes_to_spend` is never downgraded once it appears. Honest: while every
   mentor is synthetic the result is labelled `is_simulated`.
10. **Mentor replies come from `simulator.py`** with three voices (honest/salesy/
    subtle), all labelled "Simulated mentor". The style picker is a demo lever for
    exercising the Guardian, not a user-facing product feature.

**Fixed two latent bugs found while building (not pre-existing):**
- `prompts/guardian.md` contained unescaped JSON braces (`{ distress: ... }`)
  that would have crashed `str.format()` on the live-Gemini path. Escaped as
  `{{ }}`, matching `intent.md`/`rerank.md`.
- `GeminiClient` had no plain-text generation method; added `generate()` for the
  simulator alongside the existing `structured()`.

**Verification:** 140 tests pass (was 111; +29 in `tests/test_sessions.py`),
covering the spec's full eval list — obvious pitch, contact solicitation, hard
negatives, prompt-injection (alone and bundled with a pitch), number-spelled-out,
another language, and distress phrases — plus the session lifecycle, strike
bookkeeping, privacy isolation, and the Friend Test. Frontend builds clean (60
modules). Live smoke (`scripts/smoke_a2.ps1`) green end to end.

**Revisit when:** real mentors exist (the simulator and its style picker become
test-only), or a live Gemini classifier is configured (the `source` label flips
from `fallback` to `gemini` and language coverage widens).

## 2026-10-17 — Scope freeze: one spec of record, discovery frozen

Per `CORE_REALIGNMENT.md` §4/§6 (the realignment review). This entry freezes
scope so effort goes to the differentiator, not the supporting layer.

1. **`unsold_product_spec.md` (v2) is the spec of record.** It is the single
   source of truth for the product, architecture, data model, AI components, and
   build order. Where it conflicts with anything else, it wins.
2. **The discovery spec is add-on reference only.** `global_discovery_platform_build_spec.md`
   is demoted: its exclusions ("no mentorship", "not a career portal") do **not**
   apply to the core. A header note marks it as such. The catalogue it produced
   is retained as the supporting layer.
3. **Discovery is frozen.** No new catalogue entries, filters, or relationship
   edges. Its remaining job is to feed "something small you could try" into the
   advice flow (session summary + advice results) — a Release 1/2 task, not
   expansion.
4. **Nav reordered to the core's priorities:** Advice (front door) → My sessions
   → Explore. The mentors directory becomes secondary (reachable from Advice and
   Explore, not top-level nav). People and Communities placeholder nav items are
   **removed** — they implied a social product that is explicitly out of scope
   for the advice core.
5. **The differentiator is unbuilt and now prioritised.** Per the realignment
   scorecard, the Guardian, Friend Test, sessions, consent-reveal, feedback
   agreement, and mentor impact are the parts that make this product unique, and
   all were missing after A1. Stage A2 (Session + Guardian + Friend Test) is the
   next build; A3 (reveal + summary + feedback + metrics) after it.
6. **Honest status carried forward:** no Google AI service has ever run (no
   credentials on the dev machine); everything uses the deterministic fallback
   and is labelled as such. Cloud de-risking (P0 in the realignment doc) is a
   human task and blocks any claim of live-AI capability.

**Build order (from `unsold_product_spec.md` §16, Release 1):** Session chat +
Guardian + Friend Test + mentor simulator (A2) → consent reveal + editable
summary + feedback + agreement metric + mentor impact (A3) → hardening/eval.
Do not start Release 2 until Release 1 is built and deployable.

## 2026-10-17 — Re-scope: advice/mentorship restored as the CORE product

The product owner reviewed the Atlas Stage 1 build and reversed the pivot's
scope decision: the **independent-advice mentorship experience is the core
product**, and Global Discovery is a **supporting add-on**, not the other way
round. Recorded here because it supersedes the removal decision (#3) below.

- **Why it changed.** The 2026-10-17 pivot followed
  `global_discovery_platform_build_spec.md`, which explicitly excludes paid
  mentorship and repositions the product as discovery-first. Executing that spec
  faithfully removed the advice core (need → grounded guidance → mentor matches →
  session → summary). The owner judged that this lost the product's central idea.
- **New scope: advice core + discovery add-on.** Rebuild the Unsold
  advice/mentorship journey (anonymously describe a decision, get an editable
  interpretation, compare up to three grounded pitch-free mentors, hold a
  Guardian-moderated session, close out with an editable summary and next steps,
  give feedback) as the heart of the app. Keep Atlas's interest catalogue as the
  **"ways to explore / try something / next steps"** layer around advice — it maps
  onto the old spec's free-resource finder (§2.5) and follow-through (§2.7).
- **Code is not in git** (repo has no `.git`), so the removed modules are rebuilt
  rather than reverted. Shared infrastructure that survived the pivot — `store.py`,
  `scrub.py`, `pseudonym.py`, `rate_limit.py`, `errors.py`, `observability.py`,
  `deps.py`, `gemini.py` — is reused unchanged. Rebuilt fresh: advice models,
  synthetic mentor corpus, matching/re-ranking, need/session routes, Guardian,
  Friend Test, identity-reveal consent, summary, feedback.
- **Honesty rules carry over unchanged** (old spec §13/§15 and Atlas §16): every
  model-assisted result is labelled with its real source (`gemini` vs
  `fallback`/`keyword`); deterministic keyword matching stands in for live Gemini
  locally and says so; no simulated outcome is ever shown as a real one.
- **Atlas discovery stays** — catalogue, search, saved list, discovery feedback —
  repositioned as the add-on. Its Stage 1 decisions (#4–#18 below) still stand for
  that surface; only the product framing changes.
- **Working name.** "Atlas" is retained as a placeholder pending a final name; it
  now covers the advice-first product with a discovery add-on. Revisit when a name
  is chosen.

Staged rebuild (report after each, wait for "next"):
**A1** advice-core backend (models, ≥30 synthetic mentors, deterministic
retrieval + honest Gemini re-rank, `/api/needs`, `/api/mentors`, `/api/sessions`)
with the Atlas catalogue wired in as explore/next-step backing. **A2** in-app
session + Guardian (ALLOW/WARN/BLOCK_AND_REDACT, strikes) + Friend Test.
**A3** identity-reveal consent + editable closeout summary/next steps + feedback
with agreement metric. **A4** frontend (reinstate advice UI, Atlas Explore as
add-on nav). **A5** quality/audit views + docs.

## 2026-10-17 — Stage 1: product pivot to the Global Discovery Platform

> **Superseded in scope by the re-scope above.** Retained for history: the
> discovery surface it describes is kept as the add-on.

The build spec at `global_discovery_platform_build_spec.md` describes a
different product from the earlier "Unsold" mentorship spec
(`unsold_build_spec_revised.md`, now superseded). The pivot was confirmed with
the product owner: keep the stack and reusable infrastructure (auth, scrubbing,
store, Gemini client, tests), remove mentorship-specific features, and build the
new product stage by stage, reporting after each stage.

1. **Working product name "Atlas".** The new spec has no product name; "Atlas"
   matches its "global curiosity atlas" framing (§11) and is used for the
   wordmark, FastAPI title, and demo token salt. Revisit when a final name exists.
2. **Stack unchanged** (spec §12: adapt to the existing repo): FastAPI +
   React/Vite/TS/Tailwind v4 on the in-memory/Firestore store. No migration to
   Next.js/Postgres.
3. **Mentorship modules removed:** `matching.py`, `guardian.py`, `safety.py`,
   `embed_local.py`, `seed_data.py`, `routes/needs.py`, `routes/mentors.py`,
   prompts (`intent.md`, `rerank.md`), `data/crisis_resources.json`, and their
   tests. Kept unchanged: `store.py`, `scrub.py`, `pseudonym.py`,
   `rate_limit.py`, `errors.py`, `observability.py`, `deps.py`, `gemini.py`.
4. **Catalogue: 88 entries / 151 edges.** Eight per-category-ish mix across the
   spec's 10 categories (8–9 each), inside the 80–120 target. Entries are built
   by one `_i()` helper with required keyword args, so a missing field fails at
   import rather than silently. Edges are explicit `(from, to, type, note)`
   tuples stored both embedded on interest documents and as separate
   `interest_relationships` records (spec §8: reviewable). Integrity is gated by
   `scripts/validate_catalogue.py` + `tests/test_catalogue.py`.
5. **Card vs detail split.** `InterestCard` carries scannable fields only;
   `long_description`, `ways_of_thinking`, and edges live on the detail
   response. Keeps list payloads small without hiding anything behind an extra call.
6. **Search is keyword-only and says so.** `search_source: "keyword"` and
   `ai_search_available` appear on every list response; the UI shows a status
   pill. Gemini takes over only the query side in Stage 3, and only for queries
   it actually handled (spec §13 honesty rule).
7. **`time_commitment` is a display string; filtering uses booleans.**
   The spec's filter list ("time commitment") is not Stage 1 — structured time
   buckets would require a schema the spec doesn't define. Stage 1 exposes only
   catalogue-backed filters (category, beginner, solo/group, online/in-person)
   per "do not show filters unless the catalogue supports them".
8. **Demo login uses `label`, not `role`.** `POST /api/dev/demo-login {"label":
   "a"}` derives `demo-<sha256(label)>`, so multi-member tests (and Stage 4
   connections) can mint two genuinely distinct verified identities without a
   mentor/mentee role concept.
9. **`AppUser` slimmed** to `uid/pseudonym/language/is_synthetic/timestamps`.
   `topics_interest` and `role` removed; `UserInterest` (onboarding selections)
   deferred to Stage 4.
10. **Feedback reasons are fixed choices** (`too_similar`, `not_relevant`,
    `not_accessible`) rather than free text — nothing to scrub, nothing to
    accidentally disclose. Dismissals never remove catalogue entries (spec §5).
11. **Agreement summary appears only at ≥3 samples** and is labelled
    "Simulated sample feedback" while the user base is synthetic. Below that it
    is `null` and simply not displayed.
12. **Seeding is a side effect only in demo mode.** Production stores are seeded
    explicitly via `python -m app.seed` (idempotent), because boot-time writes
    would touch Firestore credentials during app construction — this broke three
    production-shape tests before the fix.
13. **Config cleanup.** Removed Unsold-era settings (`MAX_NEED_CHARS`,
    `MAX_MESSAGE_CHARS`, `SESSION_RETENTION_DAYS`, `MATCH_NO_STRONG_THRESHOLD`,
    `ENABLE_RESOURCE_GROUNDING`, `USE_ADK`); added `DATA_RETENTION_DAYS` and
    `MAX_QUERY_CHARS`. Production validation still requires project, location,
    `GEMINI_MODEL`, `EMBED_MODEL`, `EMBED_DIM`.
14. **`/api/config` now returns `ai_available`** (replacing
    `resource_grounding_enabled`) so the UI can be honest about AI search before
    Stage 3 exists.
15. **People and Communities are nav placeholders** routing to `InProgress`
    screens. Spec §4 lists them in the main nav; faking content would violate
    §16, hiding them would surprise Stage 4 — an honest placeholder is the
    truthful middle.
16. **Category accents as chips, not backgrounds.** The warm-neutral palette is
    kept; each of the 10 categories gets one soft chip colour + dot, so the UI
    gains orientation without leaving the spec's warm-neutral direction.
17. **Backend suite: 88 tests passing** after the pivot (down from 94: two
    mentorship test files removed, three new files added).
18. **Environment constraints unchanged:** no `gcloud`, no Docker, no ADC on
    this machine; cloud deploy and live Gemini remain operator steps (README)
    and Stage 3 work respectively. Windows/PowerShell; Python 3.12 venv.

## Carried over from ASSUMPTIONS.md (still relevant infrastructure decisions)

### Phase 0 — platform

- **Host has no Google Cloud CLI / ADC.** All cloud-side work is documented as
  operator steps; the app runs fully in local demo mode without credentials.
- **Python 3.12 via `py -3.12`.** Machine default is 3.14; spec mandates 3.12.
- **`APP_MODE=demo` is the local default.** Production validation requires full
  Google Cloud configuration only when `APP_MODE=production`.
- **Google Cloud SDK dependencies added when first used.** `google-genai`,
  `firebase-admin`, `google-cloud-firestore` install from requirements but
  initialize lazily.
- **`GET /api/config` exists beyond the spec's API table** because the frontend
  needs the demo banner / AI-availability flags. Returns no secrets.
- **Model IDs and `EMBED_DIM` remain placeholders** until Stage 3; production
  validation rejects placeholders with an actionable error. Verify current model
  IDs in official docs before use.
- **Frontend stack:** React 19, Vite 6, TypeScript 5.7, Tailwind CSS v4,
  react-router-dom 7.
- **`firestore.rules` / `firestore.indexes.json` stay deny-all/empty** because
  the client never touches Firestore; it talks only to the API.
- **Node 22-slim for the frontend Docker build stage** (LTS); lockfile committed
  for reproducible `npm ci`.
- **No Docker on the build machine** — `Dockerfile` untested locally; it uses
  the same commands verified locally.

### Phase 1 — auth & storage (kept)

- **Demo auth uses HMAC-signed local tokens, not trusted headers.** Same
  verification/ownership code paths as production; uid never from body/query.
- **In-memory store is the demo backend; `FirestoreStore` is lazy** so
  constructing a production app never needs credentials (test-verified).
- **`DEV_TOKEN_SECRET` optional**; process-derived secret otherwise (tokens reset
  on restart); never read in production.
- **Rate limiting is in-process sliding window** — adequate for a single/small
  instance; distributed limiting deferred until measurements justify it.
- **PII scrubbing is deterministic** (emails, phone numbers, URLs, social
  handles, names in simple identifying phrases). Perfect name detection is not
  claimed anywhere in product copy.
- **Deletion retains nothing** in the prototype; any future exception must be
  documented in README and the API response before being implemented.
- **Two API additions beyond the spec table:** `PATCH /api/auth/session` and
  `GET /api/dev/me`. Neither exposes private data.
- **Session state lives in a React context** that resolves an existing token on
  mount; the client never chooses its own identity.

### Obsolete after the pivot (recorded for history)

- Guardian/mental-safety layers, matching thresholds, need interpretation flow,
  mentor corpus of 41, crisis-resource directory, local hashing embeddings,
  need→matches three-step UI — all removed with the mentorship product. Their
  underlying infrastructure (scrubbing, rate limiting, structured logs,
  fallback labelling) carried forward.
- *"Landing CTAs route through `/profile`"* — replaced: landing routes to
  `/explore` first; sign-in is only required for save/feedback.
