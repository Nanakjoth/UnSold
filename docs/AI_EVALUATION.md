# AI Evaluation

**Status: the Guardian eval harness (Stage P3) is built and run; no live
Gemini call has ever been made in this project.** The numbers below describe
what actually exists. Anything that would require a live model is marked as
such — nothing here is a measurement that wasn't taken.

## What AI does in this product (spec §7)

| Feature | Where | Current state |
|---|---|---|
| Intent interpretation (need text → `NeedIntent`) | `matching.py` | Deterministic keyword path is the tested, live behaviour; a Gemini path activates only when configured *and* the call succeeds. Labelled `interpretation_source: "gemini" \| "fallback"`. |
| Mentor retrieval + re-ranking | `matching.py` | Transparent weighted fit (domain 0.34 / topic 0.40 / goal 0.16 / language 0.10). Gemini re-rank optional; labelled `retrieval_source: "keyword" \| "gemini"`. |
| Guardian anti-promotion classifier | `guardian.py` | Deterministic rules (EN+ES phrases + language-agnostic contact regexes) + optional Gemini layer. The **action** is always code, never the model. |
| Editable summary drafting | `sessions.py` | Template/fallback draft, labelled `source: "fallback"`. |
| Mentor replies | `simulator.py` | Deterministic, labelled **"Simulated mentor"** — never a real person, never presented as one. |
| Discovery search | `catalogue.py` | Deterministic keyword matching, labelled `search_source: "keyword"`. Frozen add-on. |
| Anything user-facing | — | Never simulated. The UI states when AI is unavailable. |

## Client & safety rails (already in place, `server/app/gemini.py`)

- Lazy client construction; a model call is impossible without explicit
  configuration (project, location, model, embedding settings validated at
  production startup).
- Structured JSON output with Pydantic schema validation; one retry on
  malformed output, then a degraded `GenerationResult` for a deterministic
  fallback.
- Provenance on every call: `source ∈ {"gemini", "fallback"}` and an
  `error_category` — the API layer converts this into the honest
  `interpretation_source` / `retrieval_source` / `source` labels users see.
- Prompts live in versioned files under `app/prompts/` (empty — a prompt file is
  only created alongside the feature that uses it).
- Log events record model, timing, and outcome categories — never prompt
  contents or member data.
- `scripts/check_gemini.py` reports the real configuration state (exit 2 when
  unconfigured) and **never fakes a call**.

## What is actually evaluated today: the Guardian (Stage P3)

The offline eval harness scores the Guardian classifier — the product's main
differentiator — and its numbers surface on the `/metrics` page.

- **Gold set:** `eval/gold_set.jsonl`, 80 messages — 40 clean (20 of them hard
  negatives: free resources, certification explanations, etc. that must **not**
  be flagged) and 40 pitches across the Guardian's categories (direct promo,
  contact solicitation, urgency/fear, soft steering, affiliate/referral).
- **Split:** even rows → dev, odd rows → test (isolated, so tuning on dev can't
  leak into the reported test numbers).
- **Runner:** `scripts/run_eval.py` → `eval/last_run.json`. Served by
  `GET /api/dev/metrics/eval` (demo-only).
- **Metrics:** precision / recall / F1, per-category recall, hard-negative false
  positive rate, and a confusion matrix. A predicted "pitch" is `is_pitch` OR
  severity ≥ 2.

**Honesty caveat (spec §12):** every one of the 80 labels is machine-generated
and currently marked `unreviewed`. Until a human reviews ≥30 of them, these
numbers describe the **current deterministic behaviour**, not proven accuracy —
and the Metrics page says exactly that. The tuning that lifted test recall from
0.40 → 0.95 (at precision 1.00, hard-negative FPR 0.00) widened EN+ES phrase
coverage (urgency, affiliate, soft-steering, off-platform contact); it should be
re-checked on fresh human-written rows.

## Evaluation plan for a live model (not yet run)

No live Gemini call has been made (no credentials here). When one is, the same
discipline applies:

- Ground truth is authored by hand **before** running the model, so results
  measure the system rather than post-hoc rationalising.
- Record per-call: intent parsed correctly (Y/N), output matches the schema
  (Y/N), latency, and the `source` label. Aggregate: intent accuracy, schema
  validity, p50/p95 latency, fallback rate, error categories.
- The discovery search set (20 natural-language queries with written expected
  filters/slugs) is defined in the frozen add-on's plan and is not scheduled.

## Cost tracking

Add after the first real measurement: per-feature table of model, token counts,
and USD cost per 100 calls, plus the daily-call estimate for the deployed
scale. No cost figures exist yet because no model calls have been made.

## Honesty rules this document must uphold

1. Never record a metric that was not measured on a live model.
2. `source` labels flip to `"gemini"` only for calls the live model actually
   handled; keyword/fallback results keep their labels.
3. Fallbacks are reported as fallbacks in evaluation results, not as successes.
4. If a model is unavailable, the product says so — the evaluation plan is not a
   promise that the feature exists.
5. Eval numbers derived from `unreviewed` labels are labelled as behaviour
   descriptions, not accuracy claims.
