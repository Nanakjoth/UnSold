# Privacy & Safety

This document is the operative privacy and safety record for Atlas. It tracks
what the product *actually does today*; anything not listed here does not exist
yet and is not implied anywhere in the UI.

## What is stored today

| Data | Where | Owner field | Lifetime |
|---|---|---|---|
| Pseudonymous account record (generated pseudonym, language, `is_synthetic`, timestamps) | `users` | keyed by `uid` | until the member deletes it |
| Advice needs (scrubbed situation + interpreted intent + `no_strong_match`) | `needs` | `user_id` | until deleted |
| Mentorship sessions (participants, Guardian counters, money stance, reveal state, summary) | `sessions` | `mentee_id` | until deleted |
| Session messages (post-scrub, post-Guardian; `text_scrubbed` + `display_text`) | `session_messages` | via `session_id` | until deleted |
| Dual-role session feedback | `session_feedback` | via `session_id` | until deleted |
| Synthetic mentor corpus (public card + private stats) | `mentors` | none (shared content) | until re-seeded |
| Saved interests | `saved_interests` | `user_id` | until deleted |
| Discovery feedback (action + optional fixed reason) | `discovery_feedback` | `user_id` | until deleted |
| Catalogue content (sample) | `interests`, `interest_relationships` | none (shared content) | until re-seeded |

**Not stored:** real names, emails, phone numbers, passwords, precise location,
employers, contact details, and any form of ad tracking. Message and need text
is stored **only after PII scrubbing** — raw free text never reaches the store
or a model prompt. Chosen reveal contacts are scrubbed before storage too.

## Identity model

- Members are identified by a server-generated pseudonym (`adjective-animal-number`)
  and an opaque `uid`. The uid is derived from a **verified token only** — never
  from a request body or query parameter (test-enforced).
- In demo mode identities are labeled `is_synthetic: true` and a banner states
  this on every screen.
- In production the intended path is Firebase anonymous auth: an account with no
  personal data attached. No email or phone is ever requested.
- Saved interests and feedback are **private by default**: every read is scoped
  to the verified caller, and no route exists that lists another member's data
  (test-enforced: `test_saved_lists_are_per_member`).

## Input safety by design

- **Feedback reasons are fixed choices** (`too_similar`, `not_relevant`,
  `not_accessible`) — free text does not exist in user feedback, so there is
  nothing to leak and nothing to scrub.
- **Free text** (advice needs and session messages) passes through deterministic
  PII scrubbing (`scrub.py`) before persistence and before any model call;
  logs record replacement *counts*, never matched values. Perfect name detection
  is not claimed.
- **Rate limiting:** per-user (falling back to per-IP) sliding window,
  default 20/min, `429` with `Retry-After`.

## Deletion rights

`DELETE /api/auth/session` removes every record owned by the caller — account,
advice needs, sessions, session messages, session feedback, saved interests,
and discovery feedback — and returns exact per-collection counts. Deletion
**cascades**: a session the member opened takes its messages and feedback with
it, so nothing orphaned survives the request. The prototype retains nothing
after deletion. Any future security/quality exception must be documented here
*and* in the API response before being implemented.

UI affordances: Profile → "Delete my data" with a confirmation step; the result
shows the deletion totals.

## Retention

- `DATA_RETENTION_DAYS` (default 30) governs records stamped with `expires_at`,
  purged by `retention.purge_expired`.
- Demo data additionally resets whenever the server restarts (in-memory store).
- Firestore deployments can back this with native TTL on `expires_at`.

## Logging & observability

- Structured JSON events with IDs, counts, categories, and status codes only.
- Long values are defensively truncated (`[truncated: …]`) so free text cannot
  leak into logs even if a future field reaches one.
- No message or query text is ever logged. Search events record `query_chars`
  (length), not the query.

## The anonymous playground (`POST /api/guardian/try`)

- Visitors can test the Guardian without an account, and **nothing they type is
  stored or logged**: the endpoint scrubs → screens → returns the verdict and
  discards the text. Only aggregate counters are emitted (length, category,
  severity, action, classifier source, scrubbed flag) — never content.
- Caps: 500 characters per request, 10 requests per minute per IP (`429` with
  `Retry-After`). It is the one endpoint where free text touches nothing.
- `GET /api/public/stats` is the mirror image: aggregates only — counts, eval
  numbers, an agreement share — never ids, text, or per-record data, and it is
  registered in production as well as demo.

## AI honesty (privacy-adjacent)

- Every AI-assisted result states its **real** source: `interpretation_source`
  and `retrieval_source` are `"gemini"` only when a live model produced them,
  otherwise `"fallback"` / `"keyword"`. The UI never implies a model produced a
  result when it did not.
- AI features are never simulated or mocked. A configured-but-failing model
  degrades to the deterministic path and is labelled as such, not dressed up.
- **What is (and is not) sent to a model:** text is scrubbed of PII *before* any
  model call, so a model sees scrubbed content only — never the member's
  identity, saved list, or raw contact details. With no cloud credentials
  configured (the local default), no model call happens at all.
- Mentor replies in this prototype come from a deterministic simulator labelled
  **"Simulated mentor"** — never a real person, never presented as one.

## Client-side surface

- The React app talks only to the API. `firestore.rules` keeps client-side
  Firestore access deny-by-default; the client has no Firestore credentials.
- The demo bearer token lives in `localStorage` under `atlas.demo.token`; in
  production this becomes a Firebase ID token from anonymous auth. Neither is a
  password.

## Content safety in the advice session (the Guardian)

- Every message — both directions — is scrubbed and then screened by the
  **Guardian** before it is stored or displayed.
- The Guardian classifies promotion, contact-solicitation, urgency/fear, and
  affiliate wording, plus language-agnostic contact regexes and spoken phone
  numbers. Phrase sets cover English and Spanish; a live Gemini classifier would
  widen this (stated as a limit below).
- The **action is decided by deterministic code, never by the model**: severity
  0/1 → `ALLOW`, 2 → `WARN`, 3 → `BLOCK_AND_REDACT`. Three strikes end a
  session.
- Blocked messages are stored (for audit) but **displayed redacted**. Logs record
  counts and code categories, never message text.
- Distress language triggers a respectful support note — never a clinical or
  crisis response, because a mentor is a peer, not a professional.
- Off-platform contact requests ("WhatsApp me", "meet offline") are detected and
  tokenised by the scrubber and flagged as a risk.

## Content safety in the catalogue

- Entries avoid invented cultural origins, historical claims, dates, prices,
  and safety guarantees (build spec §8).
- Entries involving physical risk (bouldering, carving, slacklining) carry
  honest safety-conscious access notes without claiming guarantees.
- Living cultural practices carry a source note directing readers to
  practitioners rather than the summary.
- Only real, general resources are named (public libraries, iNaturalist, NASA
  apps, public park systems). No invented organizations or URLs.
- `is_sample_content: true` on every entry, surfaced in the UI.

## Known honest limits

- A pseudonym hides members from *each other*; it does not prevent operators or
  cloud providers from processing technical metadata (e.g. IP addresses in
  server logs). Stated on the Privacy page and landing "What this is not".
- The Guardian is deterministic rules (English + Spanish phrase sets +
  language-agnostic contact regexes), not a live model — a live Gemini
  classifier would widen coverage. The **human** review queue for
  Guardian-vs-mentee disagreements is a logged signal only; no staffed
  moderation console exists in this prototype.
- The mentor's side of a session (replies, reveal consent, feedback) is
  **simulated** and labelled as such; there is no real mentor account, so
  mentor-facing dashboards sit behind demo-only routes.
- Cloud-side behavior (Firestore, Firebase token verification, live Gemini) is
  implemented but unexercised in this environment for lack of credentials.
