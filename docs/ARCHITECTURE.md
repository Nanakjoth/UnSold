# Architecture

## Shape

Two services in one repository, deployable as one process:

```
server/                      FastAPI, Python 3.12
  app/main.py                  app factory, routers, demo-mode seeding, SPA serving
  app/config.py                environment-only settings, startup validation
  app/models.py                Pydantic schemas (needs, sessions, Guardian, reveal, feedback, catalogue)
  app/store.py                 Store protocol: InMemoryStore + FirestoreStore
  app/auth.py                  token verification (Firebase prod / HMAC demo)
  app/scrub.py                 deterministic PII scrubbing (needs, messages, summary, reveal contact)
  app/matching.py              intent interpretation + retrieval + transparent fit scoring
  app/mentor_corpus.py         35 synthetic mentors (public card + private stats)
  app/sample_scenarios.py      10 sample mentee situations for the front door
  app/guardian.py              anti-promotion classifier + deterministic action policy
  app/simulator.py             synthetic mentor replies (honest/salesy/subtle)
  app/metrics.py               Guardian-vs-mentee agreement metric
  app/evaluation.py            offline eval scoring core (confusion matrix, FPR)
  app/catalogue.py             seed building, keyword search, relationship expansion
  app/catalogue_entries.py     88 sample entries + 151 reviewable edges (data only)
  app/retention.py             owner-scoped deletion (cascades advice core) + expires_at purge
  app/auth.py                  token verification (Firebase prod / HMAC demo)
  app/gemini.py                lazy Gen AI client with honest fallback labelling
  app/seed.py                  explicit `python -m app.seed` CLI
  app/rate_limit.py            in-process sliding window
  app/observability.py         content-free structured JSON logs
  app/routes/                  auth, needs, mentors, sessions, interests, library,
                               public (guardian/try + public/stats), dev (demo-only)
  tests/                       pytest suite (206 tests)
  scripts/validate_catalogue.py, smoke_a1.ps1, smoke_stage1.ps1, demo_a1.ps1,
  validate_status_codes.ps1

scripts/                      cross-cutting: smoke_a2/a3/eval/scenarios.ps1,
                              run_eval.py, check_scenarios.py, check_gemini.py,
                              generate_gold_set.py

eval/                         gold_set.jsonl (80 messages) + last_run.json

web/                         React 19 + Vite 6 + TypeScript + Tailwind v4
  src/App.tsx                   route table ("/" is advice)
  src/pages/                    Advice, Sessions, Metrics, Mentors, Explore,
                                 InterestDetail, Saved, Profile, Static, InProgress
  src/components/               Shell (nav/footer), AdviceResults, InterestCard, DemoBanner
  src/services/                 api (fetch/token), advice, sessions, auth, catalogue
  src/hooks/                    useSession (context), useConfig
  src/types/api.ts              mirrors backend schemas

docs/                        PROJECT_EXPLAINED, ARCHITECTURE, DECISIONS,
                              PRIVACY_AND_SAFETY, AI_EVALUATION, PRODUCT_SPEC
```

## Data model

Collections (Firestore names identical to in-memory buckets):

| Collection | Owner field | Contents |
|---|---|---|
| `users` | keyed by `uid` | pseudonym, language, is_synthetic, timestamps |
| `mentors` | — | synthetic mentor corpus: public card (exposed) + private stats (never exposed) |
| `needs` | `user_id` | scrubbed situation + interpreted `NeedIntent` + `no_strong_match` |
| `sessions` | `mentee_id` | participants, status, Guardian counters, money stance, reveal state, editable summary |
| `session_messages` | via `session_id` | post-scrub, post-Guardian: `text_scrubbed` (stored) + `display_text` (shown; redacted on block) |
| `session_feedback` | via `session_id` | one doc per `{session_id}_{role}`: mentee helpfulness/`felt_pitched`/recommend, or mentor seriousness/respectful; `is_simulated` on the mentor side |
| `interests` | — | full catalogue entries with embedded outgoing `relationship_edges` |
| `interest_relationships` | — | explicit edge records (`from_slug`, `to_slug`, `type`, `note`) kept separate so relationships are reviewable, mirrored by the embedded lists |
| `saved_interests` | `user_id` | `user_id` + `interest_id` + `interest_slug`, doc id `<uid>__<slug>` (idempotent save) |
| `discovery_feedback` | `user_id` | action + optional fixed reason, doc id includes timestamp |

The 10 sample situations are **not** a collection — they are a static module
(`sample_scenarios.py`) served at `GET /api/needs/scenarios`.

Ownership rule: every user-owned record carries `user_id` (or `owner_uid` /
`mentee_id` in advice-core collections). No route lists another member's
records; reads are always scoped to the verified caller. `retention.delete_user_data`
cascades: deleting a member removes their needs and, for each session they
opened, its messages and feedback.

The catalogue is **sample content**: every entry is `is_sample_content: true`.
Every mentor and session is `is_synthetic: true`.

## Request flow

```
HTTP → rate_limit → route handler
      → auth (verify bearer → VerifiedUser → AppUser)   [protected routes only]
      → scrub free text (needs, messages, summary, reveal contact)
      → Guardian screen (messages only)
      → store read/write
      → response (card projections never expose private stats or other users' data)
```

- Errors always return `{ "error": { "code", "message" } }` via shared handlers.
- Free-text fields pass through `scrub.py` before persistence **and** before any
  model call — raw PII never reaches the store or a prompt.
- Logs are structured, content-free events (IDs, counts, categories) with
  defensive truncation of long values.

## Matching (the advice core)

`matching.py` interprets a scrubbed need into a structured `NeedIntent`
(goal, domains from a fixed vocabulary shared with the corpus, money/distress
flags, traits), then scores every mentor with a **transparent weighted fit**:

| Signal | Weight |
|---|---|
| Domain overlap | 0.34 |
| Topic relevance (stemmed) | 0.40 |
| Goal / trait fit | 0.16 |
| Shared language | 0.10 |

Explanations are **grounded**: they may reference only the mentor's public card
fields and the mentee's own intent — never an invented employer, history, or
contact. Below a confidence floor the response sets `no_strong_match: true`
rather than dressing up a weak match.

`GET /api/needs/scenarios` serves 10 sample situations (2 per focus mentor);
each is engineered so the deterministic matcher ranks its intended mentor #1
(pinned by `tests/test_scenarios.py` and `scripts/check_scenarios.py`).

## The Guardian (session safety)

Every message runs `scrub() → screen_message() → store(text_scrubbed, display_text)`:

- **Layer 1 — deterministic rules:** contact details, off-platform phrases,
  promo/urgency/affiliate wording, spoken phone numbers. Contact regexes are
  language-agnostic; phrase sets cover English and Spanish.
- **Layer 2 — classifier:** Gemini when live (labelled `gemini`), otherwise a
  deterministic fallback (labelled `fallback`). User text is data, never
  instructions.
- **Layer 3 — action decided by code, never the model:** severity 0/1 → `ALLOW`,
  2 → `WARN`, 3 → `BLOCK_AND_REDACT`. Three strikes end the session.

The offline eval harness (`evaluation.py` + `eval/gold_set.jsonl` +
`scripts/run_eval.py`) scores this classifier and its numbers surface on the
`/metrics` page — with the honest caveat that the gold-set labels are still
`unreviewed`.

## Search (discovery add-on) and where AI plugs in

`catalogue.search_interests()` is deterministic: field-weighted keyword scoring
(title 3.0 > tags 2.0 > descriptions 1.0 > other fields 0.5), filters applied
before scoring, results sorted by score then title. Empty query = browse mode.
Nonzero query with zero hits = empty list, never a fabricated suggestion.

A live Gemini path could replace only the *query understanding* side, flipping
`search_source` to `"gemini"` for those queries. `gemini.py` already provides
lazy client construction, structured JSON output with schema validation, one
retry, and a `GenerationResult(source="gemini"|"fallback")` provenance record —
the caller decides how to label honestly. Discovery is frozen as an add-on, so
this is prepared but not scheduled.

## Demo vs production

- `APP_MODE=demo` (default): in-memory store, catalogue + mentor corpus seeded
  at boot when empty, HMAC demo tokens via `POST /api/dev/demo-login`, visible
  synthetic-data banner, and demo-only metrics/impact routes.
- `APP_MODE=production`: startup validation requires complete Google Cloud
  configuration; the demo route module is never imported (asserted by test);
  Firebase verifies ID tokens; FirestoreStore connects lazily so construction
  never needs credentials; seeding is explicit (`python -m app.seed`).

Both modes run the *same* authorization code paths, so ownership checks are
genuinely exercised locally.

## Frontend conventions

- Design tokens in `index.css` `@theme` (warm-neutral paper/ink palette + green
  accent + clay warning). Category accents are restrained chips with a small
  colour dot — one per catalogue category.
- Server state fetched per page via `services/advice.ts`, `services/sessions.ts`,
  `services/catalogue.ts`; session state in a React context that resolves an
  existing token on mount.
- Unbuilt routes render `InProgress` pages that state plainly what arrives
  later — never faked content.

## Testing strategy

- `test_advice.py` — interpretation, matching ranking/score-spread, grounded
  explanations, honesty labels, no-strong-match.
- `test_sessions.py` — Guardian eval list (block pitch, contact, hard negatives,
  prompt injection, spoken numbers, Spanish), lifecycle, strikes, Friend Test.
- `test_a3.py` — reveal state machine, editable summary, feedback validation,
  agreement math, mentor-impact privacy.
- `test_scenarios.py` — endpoint serves 10, covers 5 focus mentors, each ranks
  its intended mentor #1, corpus is 35.
- `test_evaluation.py` — gold-set shape, split isolation, confusion matrix,
  hard-negative FPR, review-status honesty.
- `test_retention.py` — deletion cascade (needs/sessions/messages/feedback),
  expiry purge, API deletion counts.
- `test_catalogue.py` / `test_interests.py` / `test_library.py` — seed integrity,
  search, filters, detail expansion, save/feedback authz, per-member isolation.
- `test_auth.py` — token verification, per-label identity isolation, production
  route absence, rate limiting.
- `test_config.py`, `test_health.py`, `test_scrub.py`, `test_observability.py` —
  configuration, endpoints, scrubbing, log hygiene.
