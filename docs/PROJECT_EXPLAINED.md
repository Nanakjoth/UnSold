# Atlas — The Project Explained

> A plain-language, deep-dive walkthrough of what this project is, how it is
> built, and how it actually works. Read this first if you want the whole
> picture before opening any code.
>
> **Status:** the advice core (backend + front-door UI) is built and verified.
> Sessions + the **Guardian** safety layer + the Friend Test are built and
> verified (Stage A2). The identity-reveal consent machine, the editable
> summary with concrete next steps, and the dual-role feedback loop with its
> Guardian agreement metric are built and verified (Stage A3). The honest
> evaluation harness — an 80-message gold set and an eval runner whose numbers
> appear on the Metrics page — is built and verified (Stage P3), though its
> labels await human review before they count as accuracy. Demo seed data — 35
> synthetic mentors (30 base + 5 focus) and 10 sample mentee situations — is in
> place. See [§15 Roadmap](#15-roadmap-honest-status) for exactly what is and
> isn't there yet.

---

## 1. What Atlas Is

**Atlas gives independent, pitch-free guidance to a person working through a
decision** — anonymously, for free, with no one trying to sell them a course,
clinic, or coaching package.

The core idea comes straight from a real problem: when you face a decision (a
job offer, a career change, burnout, a risky purchase), you may not have a
trusted person to ask. Advice is either hard to access, or the person giving it
has something to sell. Atlas exists to make honest guidance easier to get and to
make promotion easy to spot.

### The one-sentence journey

> You describe a situation in your own words → you see how the system understood
> it (and can correct it) → you compare up to three people who can help, each
> with a written reason they fit → you talk to one in a moderated session → you
> leave with an editable summary and next steps.

### What Atlas deliberately is **not**

This is as important as what it is. Atlas is **not**:

- **Not a marketplace.** No payments, subscriptions, paid mentorship, ads,
  affiliate links, or commercial rankings.
- **Not therapy, medical, legal, or financial advice.** It connects you to
  experienced peers, not professionals. Distress signals trigger a respectful
  support notice, never a clinical response.
- **Not a dating or popularity product.** No attractiveness scores, no swipe
  mechanics, no ranking people by popularity.
- **Not an AI chatbot wrapper.** AI assists the plumbing (interpreting intent,
  ranking candidates, drafting summaries) but never pretends to be a person and
  never fabricates a result.
- **Not a black box.** Every result carries a written reason you can check.

---

## 2. The Two Products In One

A key thing to understand about the current shape: Atlas is really **two things,
deliberately layered**, and the ordering matters.

```
┌─────────────────────────────────────────────────────────────┐
│  THE CORE:  ADVICE                                          │
│  Describe a situation → grounded mentor matches → session   │
│  This is the product. It is the front door (route "/").     │
├─────────────────────────────────────────────────────────────┤
│  THE ADD-ON:  DISCOVERY                                     │
│  An 88-entry catalogue of activities with explicit links.   │
│  It answers "what's a small thing I could try myself?" and  │
│  "what's one step beyond this?" — it supports the advice,   │
│  it is not the headline.                                    │
└─────────────────────────────────────────────────────────────┘
```

- **Advice is primary.** You open the app and land on *"What are you working
  through?"* — not on a browse page.
- **Discovery is supporting.** The catalogue is where you go for a concrete
  next step, a solo activity, or a surprise connection. It maps onto the old
  spec's "free-resource finder" and "follow-through" ideas.

> **Why this ordering is called out explicitly:** the project was briefly
> pivoted to be discovery-first, then re-scoped back to advice-first. That
> history — and the reasoning — is recorded in `docs/DECISIONS.md`. If you're
> wondering "why is discovery not the main thing?", that file is the answer.

---

## 3. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend | **Python 3.12 · FastAPI · Pydantic** | Typed request/response models, fast, great validation for free. |
| Storage | **In-memory store** (demo) / **Firestore** (production) | One `Store` interface; the whole product runs locally with zero cloud credentials. |
| Frontend | **React 19 · TypeScript · Vite · Tailwind v4 · react-router 7** | Component-driven UI, type-safe against the API schemas. |
| Auth | **HMAC-signed demo tokens** / **Firebase anonymous auth** (production) | Same verification + ownership code paths in both; no email/password ever. |
| AI | **Google Gemini** (`google-genai` SDK), lazily imported | Used only when actually configured; a real deterministic fallback otherwise. |
| Scrubbing | **Deterministic regex scrubber** | Strips PII before storage and before any model call. No external service needed. |

**A defining constraint:** the app runs **fully locally with no Google Cloud
credentials**. Cloud features (live Gemini, Firestore, Firebase) activate only
when real configuration is present, and the code says so honestly when they
aren't. This is why you can run the whole thing on your machine today.

---

## 4. Architecture Overview

```
      Browser (React SPA)
             │  fetch  ──────────────────────────────┐
             ▼                                        │
   ┌───────────────────┐                              │
   │  FastAPI (main.py)│  routes under /api           │
   │  ├─ auth verify   │  ← bearer token → real uid   │
   │  ├─ rate limit    │                              │
   │  ├─ scrub PII     │  ← runs on every free text   │
   │  ├─ matching      │  ← interpret + rank mentors  │
   │  ├─ catalogue     │  ← search + relationships    │
   │  └─ Gemini client │  ← only if configured        │
   └─────────┬─────────┘                              │
             │  Store interface (get/set/list/…)      │
             ▼                                        │
   ┌───────────────────┐        ┌────────────────────┐│
   │  InMemoryStore    │  or    │  FirestoreStore    ││
   │  (demo / tests)   │        │  (production)      ││
   └───────────────────┘        └────────────────────┘│
```

**The single most important architectural rule:** application code **never
touches a database client or a model SDK directly**. It always goes through two
seams:

1. **`Store`** — every read/write goes through one interface, so authorization
   ("is this the caller's record?") and serialization live in exactly one place.
2. **`GeminiClient`** — every model call returns its result **plus a `source`**
   label (`"gemini"` or `"fallback"`), so the app can never pretend a model ran
   when it didn't.

This is what makes the honesty guarantees *structural* rather than a promise.

---

## 5. How the Advice Core Works (the important part)

This is the heart of the product. Follow one need from keystroke to matches.

### Step 1 — You describe a situation

A free-text box on the front page. Minimum 20 characters so there's something
to work with. An optional checkbox asks *"does this involve a decision about
money?"* — because money decisions get special handling (see Friend Test,
step 6).

### Step 2 — Scrubbing (before anyone sees it)

The moment you submit, the text runs through a **deterministic PII scrubber**
(`scrub.py`). It replaces identifying values with meaningful tokens **before the
text is stored or sent to any model**:

| Detected | Replaced with |
|---|---|
| Emails | `[EMAIL]` |
| Phone numbers | `[PHONE]` |
| URLs | `[URL]` |
| Social handles | `[HANDLE]` |
| Names in "my name is X" / "I'm X" | `[PERSON]` |
| "WhatsApp me", "DM me", "meet offline" | `[OFF_PLATFORM_REQUEST]` |

The scrubber **never stores or logs what it matched** — only counts by type.
It's honest about its limits: perfect name detection is impossible with regex,
so the app never claims it's perfect.

### Step 3 — Interpretation (editable, and shown to you)

The scrubbed text is turned into a structured **`NeedIntent`**:

- **`short_summary`** — one sentence, drawn from your own words.
- **`goal_type`** — e.g. `make_a_decision`, `career_switch`, `negotiate`,
  `handle_setback`, `learn_skill`.
- **`domains`** — from a fixed vocabulary (software, career, money, wellbeing…)
  that is **shared with the mentor corpus**, so interpretation and matching
  always agree.
- **`money_involved`**, **`decision_pending`** — booleans.
- **`distress_level`** — `none` / `mild` / `moderate` / `high`. If what you
  wrote signals real distress ("hopeless", "can't sleep", "burned out"), this
  rises, and the UI adds a respectful support note. It is deliberately tuned to
  *catch* genuine distress words rather than under-report them.
- **`risk_flags`** — e.g. `money_involved`, `urgency`, `financial_loss_imminent`.
- **`preferred_mentor_traits`** — e.g. `direct`, `patient`, `analytical`.

It also generates **clarifying questions** ("is this a decision with a
deadline, or are you thinking ahead?") derived only from the intent.

**You see all of this** in the "How we read your situation" panel, so it can be
checked and corrected — the system does not silently run with a guess.

### Step 4 — Retrieval & ranking

Every mentor in the corpus is scored against your intent by a **transparent,
weighted function** (not a black box):

| Signal | Weight | Meaning |
|---|---|---|
| Domain overlap | 0.34 | How much of *your* areas the mentor actually covers. |
| Topic relevance | 0.40 | Their listed topics vs. your situation text (with light stemming so "negotiate"/"negotiating" match). |
| Goal / trait fit | 0.16 | Specific signals — e.g. a `negotiate` goal boosts mentors who list "negotiating an offer". |
| Shared language | 0.10 | So a cross-language match is honestly reflected in the score. |

Weights sum to ≤ 1.0 and **scores stay spread out** — you get 0.64 / 0.53 / 0.49,
never three fake "100%" ties. Up to **three** matches return.

If nothing scores above a confidence floor, it returns **`no_strong_match: true`
with a plain-English notice** rather than dressing up weak matches as good ones.

### Step 5 — Grounded explanations (the anti-fabrication rule)

Each match's written explanation may reference **only two things**:

1. Fields on that mentor's **public card** (their real listed topics, role band,
   experience band), and
2. **Your own** interpreted intent.

It **cannot** invent an employer, a shared history, a qualification, or contact
detail. A test literally asserts every explanation is reconstructible from the
public card. This is the "grounded explanations" guarantee from the old spec.

Each match also carries:
- **`match_type`** — `DIRECT` (same field) or `CROSS_DOMAIN` (different field,
  with a sentence on why that perspective still helps).
- **`watch_outs`** — honest caveats, e.g. "they don't list your language", or
  "this is a cross-domain match so context may differ".
- **`starter_questions`** — 2–3 concrete things you could ask to open.

### Step 6 — Start a session, moderated by the Guardian (built, A2)

Each match has a **Start a session** button. That opens a text session with the
mentor, and this is where the product's main differentiator lives.

**Every message — both directions — runs a fixed pipeline:**

```
raw text → scrub() → screen_message() → store(text_scrubbed, display_text)
```

- **Scrub first** (spec §8): emails, phones, URLs, handles, and names are
  replaced with tokens before the text is stored *or* classified. Raw PII never
  reaches the store or a prompt.
- **The Guardian** (`guardian.py`) then classifies the message:
  - Layer 0: Model Armor — a cloud-only seam, skipped honestly when unconfigured.
  - Layer 1: deterministic rules — contact details, off-platform phrases,
    promo/urgency/affiliate wording, and *spoken* phone numbers ("five five
    five…"). Contact regexes are language-agnostic; phrase sets cover English
    and Spanish.
  - Layer 2: a classifier — Gemini when live (labelled `gemini`), otherwise a
    deterministic fallback (labelled `fallback`). User text is data, never
    instructions.
  - Layer 3: **the action is decided by code, never by the model.** Severity
    0/1 → `ALLOW`, 2 → `WARN` (tagged "Possible promotion"), 3 →
    `BLOCK_AND_REDACT` (replaced with a notice, and a strike for a mentor).
- **Three strikes end the session** and reset the mentor's pitch-free streak.
- **`display_text` vs `text_scrubbed`**: what's stored is the scrubbed original
  (for audit); what the *recipient* sees is redacted when the Guardian blocks.

**Friend Test** (spec §10.6): for money decisions, the session tracks whether the
mentor *pushed spending*, *cautioned against it*, or *stayed neutral*. The
session value is the latest stance, except that `pushes_to_spend` never gets
downgraded once it appears.

**Mentor simulator** (spec §10.12): mentors in this prototype are synthetic, so
replies come from a simulator with three voices — honest, salesy, subtle — all
labelled **"Simulated mentor"**. This is a demo lever for exercising the
Guardian, not a real person.

### Step 7 — Reveal, editable summary, and feedback (built, A3)

When a session ends, three more pieces complete the loop:

- **Mutual-consent reveal** (spec §8): a state machine `NONE → ONE_SIDED →
  REVEALED`. Either side can request; you can withdraw only before `REVEALED`.
  Any contact you choose to share is **scrubbed before storage**, and once
  revealed the state locks. The mentor's half of the consent is simulated and
  labelled as such (mentors don't authenticate in this prototype).
- **Editable summary with next steps** (spec §10.8): generated once from the
  **displayed, non-blocked** messages only — key points, up to **five concrete
  action items**, caveats (what the mentor couldn't know), and 2–3 small
  catalogue "things to try". You can edit it; an edited summary is never
  clobbered by regeneration, and every line is re-scrubbed before storage.
- **Dual-role feedback with an agreement metric** (spec §10.11): both you and
  the (simulated) mentor file feedback. Your `felt_pitched` answer is compared
  with the Guardian's severity to produce an honest agreement metric — shown
  only once ≥3 samples exist and always labelled simulated. Disagreements (you
  felt pitched, the Guardian didn't flag it — or vice versa) are logged for a
  human to review, never auto-actioned.

---

## 6. The Honesty Model (a central design principle)

You will see honesty labels everywhere. This is intentional and enforced in
code, not just prose.

**The rule: never pretend a model ran when it didn't.** Every AI-assisted result
carries the *real* source:

| Where | Labels you'll see |
|---|---|
| Interpretation | `interpretation_source: "gemini"` **or** `"fallback"` |
| Matching / ranking | `retrieval_source: "gemini"` **or** `"keyword"` |
| Discovery search | `search_source: "keyword"` (until Gemini search lands) |

In the UI these appear as small badges: **"AI-interpreted"** / **"AI-ranked"**
when a live model genuinely produced the result, and **"Keyword match · AI not
configured"** when the deterministic local path did.

**Why it matters:** with no cloud credentials configured (the local default),
the deterministic path is what actually runs — and the app *says so* instead of
implying an AI recommended something. When you configure Gemini for real, the
labels flip automatically. The same discipline applies to synthetic data: every
sample mentor and catalogue entry is marked (`is_synthetic` / `is_sample_content`)
and shown as such.

---

## 7. Discovery (the add-on) — How It Works

The catalogue is **88 entries across 10 categories**, connected by **151 explicit
relationship edges** of 8 types (shared material, shared technique, shared skill,
shared way of thinking, related culture, complementary activity, prerequisite,
contrasts-with).

- **Search is keyword-based and labelled as such** (`search_source: "keyword"`).
  It reports real matches and never fabricates suggestions.
- **Relationships are explicit records**, not a similarity score — each link has
  a type and a written note, so you can see *why* two interests are connected.
- **Browse needs no account.** Only saving and feedback ask you to sign in.
- **A single dismissal never removes anything** — feedback is a signal, not a
  verdict that hides a catalogue entry.

Edges are stored **both** embedded on each interest (for fast detail views) and
in a separate reviewable collection. Integrity is gated by a validator script
and tests: unique slugs, valid endpoints, every entry participates in ≥2 edges,
all 8 edge types used, no duplicate pairs.

---

## 8. Auth & Identity (anonymous by design)

**No email, no password, ever.** Identity is pseudonymous and server-verified.

- **Local demo:** `POST /api/dev/demo-login {"label": "a"}` mints an
  HMAC-signed token. The `uid` is derived deterministically from the label, so
  you can create two distinct members to test multi-person flows. The token
  expires in an hour.
- **Production:** Firebase anonymous auth issues an ID token; the server
  verifies it with the Admin SDK.
- **The rule that never bends:** the caller's `uid` comes **only** from the
  verified token — never from a request body or query parameter. Every
  per-member record carries that `user_id`, and reads are always scoped to the
  caller. There is no route that lets you read someone else's saved list or
  advice.

The client stores the token and resolves the session on load; it never chooses
its own identity.

---

## 9. Privacy & Safety

- **PII scrubbing before storage and before any model call** (see §5).
- **Deletion deletes.** Deleting your data removes it — the prototype retains
  nothing, and the deletion response reports exactly what was removed.
- **Distress handling.** High-distress language triggers a respectful support
  note pointing to people or local support lines — explicitly *not* a clinical
  or crisis response, because a mentor is a peer, not a professional.
- **Off-platform contact requests** ("WhatsApp me", "meet offline") are detected
  and tokenised by the scrubber and flagged as a risk — the product is designed
  to keep people safe *in* the app, not push them off it.
- **Structured logs only.** Logs record event *types* and counts, never raw free
  text or matched PII.
- **Rate limiting** is an in-process sliding window (adequate for a single/small
  instance).
- `firestore.rules` stays **deny-all** because the client never talks to
  Firestore directly — it only talks to the API, where authorization is enforced.

---

## 10. Data Model (the collections)

| Collection | Holds | Notes |
|---|---|---|
| `users` | Pseudonymous user records: `uid`, `pseudonym`, `language`, `is_synthetic`, timestamps | No real identity. |
| `mentors` | 35 synthetic mentors (30 base + 5 focus): public card + private stats | **Only the public card is ever exposed by the API.** |
| `needs` | Your scrubbed situation + its interpretation + `no_strong_match` | Owned by the caller. |
| `interests` | 88 catalogue entries with embedded edges | All `is_sample_content: true`. |
| `interest_relationships` | 151 explicit, reviewable edges | Separate so they can be inspected. |
| `saved_interests` | Your saved catalogue entries | Scoped to `user_id`. |
| `discovery_feedback` | save / dismiss / already_know / want_to_try | Fixed reason enum — no free text, so nothing to leak. |

The **sample mentee situations** (spec §14) are *not* a collection: they're a
static module, `server/app/sample_scenarios.py` — 10 fictional prompts across
5 domains (AI career, AI upskilling, tech startup, non-tech business,
meditation), 2 per focus mentor, each carrying an `intended_mentor_id` that a
test asserts ranks #1. Served publicly at `GET /api/needs/scenarios` and shown
as clickable examples on the advice front door.

**Stage A2 collections** (sessions, Guardian, Friend Test):

| Collection | What it holds | Honesty / privacy note |
|---|---|---|
| `sessions` | One mentorship session: participants, status, Guardian counters, money-stance rollup, reveal state | Only the mentee (verified uid) can read their own. |
| `session_messages` | Each message after scrub + Guardian screening | `text_scrubbed` is what's stored (never raw PII); `display_text` is what the other side sees (redacted on a block). |

**Stage A3 collections / fields** (reveal, summary, feedback, agreement):

| Collection / field | What it holds | Honesty / privacy note |
|---|---|---|
| `sessions.summary` | The editable mentee-only digest (key points / ≤5 action items / caveats / 2–3 catalogue "things to try") | Generated from **displayed, non-blocked** messages only; every line re-scrubbed before storage; `source` is honest (`gemini`/`fallback`); `edited=true` blocks regeneration from clobbering it. |
| `sessions.reveal` | The mutual-consent reveal state (`NONE → ONE_SIDED → REVEALED`) + each side's optional contact | Contact is scrubbed before storage; only display names + chosen contacts are exposed; locks once REVEALED. |
| `session_feedback` | One doc per `{session_id}_{role}`: mentee helpfulness/`felt_pitched`/recommend, or mentor seriousness/respectful | Free text scrubbed; the mentor side is labelled `is_simulated`; disagreements are logged for human review, never auto-actioned. |

---

## 11. API Surface (35 routes)

**Advice (core):**
- `POST /api/needs` — scrub → interpret → match → persist. **Auth required.**
- `GET /api/needs/scenarios` — the 10 sample situations on the front door (public; each built to surface one of the 5 focus mentors). (Spec §14)
- `GET /api/mentors` — public directory (filter by domain/language). Public.
- `GET /api/mentors/{id}` — one public card. Public.

**Sessions + Guardian (Stage A2, the differentiator):**
- `POST /api/sessions` — open a session with a mentor (optionally linked to a need). **Auth.**
- `GET /api/sessions` — your sessions, newest first. **Auth.**
- `GET /api/sessions/{id}` — one session (participants only). **Auth.**
- `GET /api/sessions/{id}/messages` — messages in send order. **Auth.**
- `POST /api/sessions/{id}/messages` — send a message: scrub → Guardian → store → return the decision. **Auth.**
- `POST /api/sessions/{id}/mentor-reply` — the simulator's reply (honest/salesy/subtle), screened too. **Auth.**
- `POST /api/sessions/{id}/end` — end the session and update mentor pitch stats. **Auth.**
- `GET /api/sessions/{id}/friend-test` — did the mentor push/caution spending? **Auth.**
- `POST /api/sessions/{id}/reveal` — mutual-consent reveal (NONE → ONE_SIDED → REVEALED); withdraw allowed only before REVEALED; contact scrubbed on the way in. **Auth.** (A3)
- `GET /api/sessions/{id}/summary` — the editable mentee-only summary (key points / ≤5 next steps / caveats / 2–3 catalogue "things to try"), generated once the session ends. **Auth.** (A3)
- `PATCH /api/sessions/{id}/summary` — the mentee's edits (scrubbed, capped); marks it `edited` so regeneration never clobbers it. **Auth.** (A3)
- `POST /api/sessions/{id}/feedback` — mentee or mentor feedback; updates mentor quality, logs disagreements for human review, returns the agreement metric on mentee submissions. **Auth.** (A3)
- `GET /api/dev/metrics/guardian` — the Guardian-vs-mentee agreement (share hidden below 3 samples, always with its sample size, labelled simulated). **Demo build only.** (A3)
- `GET /api/dev/metrics/eval` — the last offline Guardian evaluation run (precision/recall/F1, per-category recall, hard-negative FPR, confusion matrix), reading `eval/last_run.json`. **Demo build only.** (P3)
- `GET /api/dev/mentors/{id}/impact` — a mentor's private impact dashboard. **Demo build only** — no mentor auth exists in this prototype; production requires a signed-in mentor scoped to their own record. (A3)

**Discovery (add-on, frozen):**
- `GET /api/interests` — search + filters (`q`, category, difficulty, beginner, mode, tag).
- `GET /api/interests/categories` — category facet counts.
- `GET /api/interests/{slug}` — full entry + expanded relationships.
- `GET/POST/DELETE /api/library/saved[/{slug}]` — your saved list. **Auth.**
- `POST /api/library/feedback` — discovery feedback. **Auth.**

**Public trust surfaces (UI redesign):**
- `POST /api/guardian/try` — the anonymous playground: scrub → Guardian → verdict, **nothing stored or logged** (aggregates only), 500-char cap, 10/min per IP. Public. Honest `source` label on every response.
- `GET /api/public/stats` — aggregates only (mentor count + synthetic flag, last eval run with `accuracy_claimed` false until ≥30 human-reviewed labels, agreement hidden below 3 samples). Public, registered in demo **and** production.

**Account:**
- `POST/PATCH/DELETE /api/auth/session` — sign in / update language / sign out.
- `GET /api/config` — public runtime flags (no secrets).
- `GET /api/healthz` (top-level) — liveness probe.

**Demo-only (never registered in production):**
- `POST /api/dev/demo-login`, `POST /api/dev/reset`, `GET /api/dev/me`.

Every error leaves as `{"error": {"code", "message"}}` with a correct status
(401 unauth, 403 forbidden, 404 not found, 422 validation). Stack traces, prompts,
and raw model output never reach the client. Guardian audit lines log counts and
code categories — **never message text**.

---

## 12. Frontend Structure

```
web/src/
├─ App.tsx                     routes — "/" is ASK (the front door); /trust added
├─ theme.tsx                   ThemeProvider — dark-first, persisted, light option
├─ index.css                   design tokens (@theme), glass/grad-edge/btn classes,
│                              all motion gated by prefers-reduced-motion
├─ pages/
│  ├─ Advice.tsx               hero composer + how-it-works + playground + sections
│  ├─ Trust.tsx                full trust surface: playground, rule table, honest
│  │                           numbers, privacy, known limits
│  ├─ Sessions.tsx             session list + chat + reveal / summary / feedback (A2+A3)
│  ├─ Metrics.tsx              Guardian-vs-mentee agreement view (A3)
│  ├─ Mentors.tsx              browse the mentor directory
│  ├─ Explore.tsx              the discovery catalogue (add-on)
│  ├─ InterestDetail.tsx       one entry + its relationships
│  ├─ Saved.tsx / Profile.tsx  your saved list / account + delete
│  └─ Static.tsx               About / Privacy / Terms
├─ components/
│  ├─ AdviceResults.tsx        interpretation panel + match cards (fit badges, chips)
│  ├─ GuardianPlayground.tsx   POST /api/guardian/try UI — redaction animation,
│  │                           aria-live verdict, honest source label
│  ├─ Constellation.tsx        static hero SVG (You · Guardian · Mentor), CSS-only
│  ├─ ProvenanceChip.tsx       honest source chip on every AI-assisted result
│  ├─ home/Sections.tsx        HowItWorks, FriendTestMeter, TransparencyPanel,
│  │                           ExploreTeaser, MentorInvite
│  ├─ InterestCard.tsx         catalogue card + category chips
│  ├─ Shell.tsx                AppShell: nav (UNSOLD · Sessions · Explore · How it
│  │                           works · Trust), identity chip, theme toggle,
│  │                           prototype ribbon, mobile bottom tabs, footer
│  └─ DemoBanner.tsx           demo-mode honesty banner
├─ services/                   api.ts (fetch + token), advice.ts (incl. guardianTry,
│                              getPublicStats), sessions.ts, auth.ts, catalogue.ts
├─ hooks/                      useSession (auth context), useConfig
└─ types/api.ts                TS types mirroring the Pydantic schemas
```

Nav is **UNSOLD · Sessions · Explore · How it works · Trust** (UI redesign spec):
advice leads, discovery follows, and the two trust surfaces are one click away
(scope freeze still holds — the mentors directory stays secondary, see
`docs/DECISIONS.md`). The theme is dark-first with a persisted light option.

---

## 13. Testing & Verification

- **206 backend tests pass** (`pytest`), covering: interpretation, matching
  ranking and score-spread, grounded-explanation constraints, the honesty labels,
  auth/ownership, scrubbing (including the deletion cascade that clears a
  member's needs/sessions/messages/feedback), catalogue integrity, retention,
  route behaviour including 401/404/422 paths, the Guardian eval list (A2), the
  A3 reveal state machine / editable summary / feedback validation / agreement
  math / mentor-impact privacy, the P3 evaluation harness (gold-set shape, split
  isolation, confusion matrix, hard-negative FPR, review-status honesty), the
  sample scenarios (each ranks its intended focus mentor #1), and the public
  trust endpoints (`POST /api/guardian/try` stores nothing + rate-limits per
  IP; `GET /api/public/stats` exposes aggregates only and keeps
  `accuracy_claimed` false while labels are unreviewed).
- **Catalogue validator** (`scripts/validate_catalogue.py`) gates the 88/151
  integrity rules.
- **Live smoke scripts** exercise the real running stack:
  - `scripts/smoke_stage1.ps1` — discovery end-to-end.
  - `scripts/smoke_a1.ps1` / `demo_a1.ps1` — advice end-to-end.
  - `scripts/smoke_a2.ps1` — session + Guardian + Friend Test end-to-end.
  - `scripts/smoke_a3.ps1` — need → session → reveal → summary → feedback →
    agreement → metrics → mentor impact.
  - `scripts/smoke_eval.ps1` — run the eval and confirm the Metrics page serves it.
  - `scripts/smoke_scenarios.ps1` — the 10 sample scenarios are served publicly
    and each focus mentor it targets ranks #1 through the real `/api/needs` path.
  - `scripts/validate_status_codes.ps1` — asserts the HTTP status of every
    click action (success + error paths).
- **Frontend** gates on `npm run build` (TypeScript type-check + Vite build).

Four real bugs were caught by this discipline and fixed: match scores that
saturated to fake "100%" ties; a stop-word/substring bug that hid the
"no strong match" signal; a PII gap where "My name is X" slipped past the
scrubber at sentence start; and a **deletion gap** where `DELETE /api/auth/session`
cleared the three discovery collections but left a member's `needs`, `sessions`,
`session_messages`, and `session_feedback` behind — the cascade was added and
pinned by a test, so "deletion deletes" is now literally true.

---

## 14. Running It

```bash
# Backend (Python 3.12 venv). Port 8080 is what the Vite dev proxy targets.
cd server
.venv\Scripts\uvicorn app.main:app --port 8080

# Frontend (dev server, proxies /api to :8080 automatically)
cd web
npm run dev        # → http://localhost:5173

# Tests
cd server
.venv\Scripts\python -m pytest          # 206 passing
```

> **If port 8080 is already held** by a stale backend, the browser path breaks
> (the proxy returns the *old* routes, e.g. 404 on `/api/needs/scenarios`)
> while a smoke script against 8081 still passes. Free the port or point the
> proxy (`web/vite.config.ts`) at whichever port you actually run.

Open **http://localhost:5173** — you land on the advice front door. Cloud deploy
(Cloud Run, real Gemini, Firestore, Firebase) is documented as operator steps in
`README.md`; it needs credentials this machine doesn't have.

---

## 15. Roadmap (honest status)

| Stage | What | Status |
|---|---|---|
| **A1** | Advice backend: models, 35-mentor corpus (30 base + 5 focus), matching engine, `/api/needs`, `/api/mentors` + **front-door UI** | ✅ **Done & verified** |
| Discovery | 88-entry catalogue, search, relationships, saved, feedback (frozen add-on) | ✅ **Done & frozen** |
| **A2** | In-app session + **Guardian** moderation (ALLOW/WARN/BLOCK) + **Friend Test** + mentor simulator | ✅ **Done & verified** |
| **A3** | Identity-reveal consent + editable summary/next-steps + feedback with agreement metric | ✅ **Done & verified** |
| **P3** | Honest evaluation: 80-message gold set (20 hard negatives) + eval runner (precision/recall/F1, per-category recall, hard-neg FPR, confusion matrix) shown on Metrics | ✅ **Done & verified** |
| **Seed** | Demo seed data: 5 focus mentors (AI career, tech/non-tech founders, meditation) + 10 sample mentee situations, each ranked #1 by its target mentor | ✅ **Done & verified** |
| **P4** | Only after P0–P3: Spend Check, translation, Firebase Auth + App Check, BigQuery/Looker, T&S queue, Practice Room (spec §3/§4) | ⬜ Planned (needs cloud) |

**Known gaps, stated plainly:**
- Live Gemini now runs against a real project (verified 2026-10-18:
  `check_gemini.py` → `RESULT: gemini`; `guardian/try` → `source: "gemini"`).
  The deterministic fallback stays as the safety net, and every decision keeps
  its honest `source` label. Note the live classifier is environment-dependent:
  without the configured `.env` + credentials the app correctly labels
  results `source: "fallback"`.
- Cloud deployment is still untested as a deployed service (no Cloud Run from
  this machine yet); `docs/DEPLOY.md` + `cloudbuild.yaml` are ready for the
  operator. `gcloud` + ADC now exist on this machine, so the live-model path
  is verified here.
- The Guardian's deterministic rules cover English + Spanish phrase sets plus
  language-agnostic contact regexes; the live Gemini classifier widens this
  when configured. This limitation is stated rather than hidden.
- **A3 nuance:** the mentor's reveal-consent is simulated (mentors don't
  authenticate in this prototype), and the metrics + mentor-impact routes sit
  behind `/api/dev/...` because there's no mentor auth to scope a production
  route to. Both are honest labels, not hidden shortcuts.
- **P3 nuance:** the gold set's 80 labels are machine-generated and every row is
  still marked `unreviewed`. Until two people review ≥30 of them (spec §12), the
  precision/recall/F1 on the Metrics page describe the current deterministic
  behaviour, **not** proven accuracy. The page says this outright. The tuning that
  lifted recall 0.40 → 0.95 widened category phrase coverage (urgency, affiliate,
  soft-steering, off-platform contact) — worth re-checking on fresh human-written
  rows.

---

## Where to go next in the code

| If you want to understand… | Open |
|---|---|
| The matching engine in detail | `server/app/matching.py` |
| The mentor corpus | `server/app/mentor_corpus.py` |
| The 10 sample mentee situations | `server/app/sample_scenarios.py`, `scripts/check_scenarios.py` |
| The advice routes | `server/app/routes/needs.py`, `routes/mentors.py` |
| The API models / schemas | `server/app/models.py` |
| The honesty-labelled Gemini client | `server/app/gemini.py` |
| PII scrubbing | `server/app/scrub.py` |
| The storage seam | `server/app/store.py` |
| The Guardian's rules + decision policy | `server/app/guardian.py` |
| The offline eval scoring core | `server/app/evaluation.py` |
| The gold set + eval runner | `eval/gold_set.jsonl`, `scripts/run_eval.py` |
| The advice UI | `web/src/pages/Advice.tsx`, `components/AdviceResults.tsx` |
| **Why the product is shaped this way** | `docs/DECISIONS.md` |
| Privacy & safety detail | `docs/PRIVACY_AND_SAFETY.md` |
| The AI evaluation plan | `docs/AI_EVALUATION.md` |
```
