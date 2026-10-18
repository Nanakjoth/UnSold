# Product Specification — Atlas (Global Discovery Platform)

> **⚠️ SUPERSEDED — historical record, not the spec of record.**
>
> This document specifies the **discovery-first** product that was built as
> Stage 1, then re-scoped. It is kept because the **discovery catalogue it
> describes still exists as a frozen add-on** (88 entries, 151 relationships)
> and its integrity rules are still enforced.
>
> The **spec of record for the product as it now stands** is
> `unsold_product_spec.md` (root), read together with `CORE_REALIGNMENT.md`
> (root), which restored **advice/mentorship as the core product** and froze
> discovery. For what is actually built and verified today, read
> `docs/PROJECT_EXPLAINED.md`. The reasoning behind the pivot and the re-scope
> is in `docs/DECISIONS.md`.

This document is the working product specification for Atlas, derived from
`global_discovery_platform_build_spec.md` (the authoritative build spec at the
repository root). It records what the product *is* at the current stage and is
updated as stages land.

## 1. Purpose

Atlas helps people discover activities and crafts they would not have found on
their own, and shows *why* two interests are related through explicit,
reviewable relationships rather than a hidden score.

Homepage line (spec §11): **"There's more out there than you've discovered."**

## 2. Current stage

**Stage 1 — Foundation (complete):**

- Design tokens, application shell, navigation, responsive layout.
- Data model + seed data + demo mode.
- Catalogue browse, search, detail pages.
- Save and feedback persistence with per-member ownership.

**Remaining stages (per spec §15):**

| Stage | Scope |
|---|---|
| 2 | Deterministic weighted recommendation ranking + three discovery modes |
| 3 | Gemini intent parsing, grounded explanations, 20-query evaluation set |
| 4 | Profiles, visibility controls, connections, blocks, reports, onboarding |
| 5 | Quality pass, moderation visibility, audit against spec §16 |

## 3. Core user flows (spec §5)

1. **Explore without an account** — browse the catalogue, search, open detail pages, follow relationship edges. No identity required.
2. **Save an interest** — requires a pseudonymous session; saved list is private and deletable.
3. **Give feedback** — `save`, `dismiss` ("Not for me"), `already_know`, `want_to_try`, each with an optional *fixed-choice* reason. A dismissal is feedback, not a permanent filter: it never removes the entry from the catalogue for anyone.
4. **See connections** — every detail page expands its relationship edges into related cards, each labelled with its type and reason.
5. **Delete data** — profile page reports exact per-collection deletion counts.

## 4. Information architecture (spec §4)

| Route | Status |
|---|---|
| `/` | Built — landing page with spec §11 copy |
| `/explore` | Built — search, filters, pagination |
| `/interests/:slug` | Built — detail + expanded relationships + save/feedback |
| `/saved` | Built — private saved list |
| `/profile` | Built — identity, language, data controls |
| `/about`, `/privacy`, `/terms` | Built — honest static pages |
| `/people` | In-progress placeholder (Stage 4) |
| `/communities` | In-progress placeholder (Stage 5) |
| `/onboarding`, `/settings/privacy`, `/connections`, `/reports` | Future (Stage 4) |

Main navigation: Explore, Saved, People, Communities, profile menu. Unbuilt
destinations appear only as honest placeholders — never as faked content.

## 5. Catalogue (spec §5, §8)

- **Size:** 88 entries across 10 categories (target 80–120), 151 relationship records.
- **Categories:** Creative Practices · Making & Repair · Nature & Living Systems · Movement & Play · Music & Sound · Food & Culture · Design & Visual Thinking · Games & Strategy · Science & Everyday Experiments · Community & Craft.
- **Schema fields per entry:** `slug`, `title`, `short_description`, `long_description`, `category`, `tags[]`, `skills[]`, `materials[]`, `ways_of_thinking[]`, `beginner_step`, `time_commitment` (nullable), `difficulty` (nullable), `accessibility_notes[]`, `solo_or_group[]`, `online_or_in_person[]`, `languages[]`, `relationship_edges[]`, `source_notes`, `is_sample_content`.
- **Relationship types (all 8 in use):** `shares_material`, `shares_technique`, `shares_skill`, `shares_way_of_thinking`, `related_culture_or_context`, `complementary_activity`, `prerequisite_for`, `contrasts_with`.
- **Integrity rules** (enforced by `server/scripts/validate_catalogue.py` and `tests/test_catalogue.py`): unique well-formed slugs; every edge endpoint exists; no duplicate ordered pairs; every entry participates in ≥2 edges; every relationship type used; all entries `is_sample_content: true`.
- **Content rules:** no invented cultural origins, dates, prices, or safety guarantees. Living cultural practices carry a source note pointing to practitioners. Only real, general resources may be named (public libraries, iNaturalist, NASA apps, public park systems).

## 6. Search honesty (spec §13)

Every search response carries:

- `search_source: "keyword"` — the mechanism that actually produced the result.
- `ai_search_available` — whether a model is configured in this deployment.

The Explore page displays this as a status pill. When Stage 3 lands, `search_source`
becomes `"gemini"` only for queries genuinely handled by the live model; the label
must never claim AI ran when it did not. Zero-hit queries return an empty list —
the interface says keyword search only reports real matches and never fabricates
suggestions.

## 7. Non-goals

- Not therapy, crisis support, coaching, hiring, or financial advice.
- Not a social network at this stage (People/Communities arrive later).
- Not a recommendation black box: relationships stay inspectable.
- Analytics, when added, must be aggregate-only and documented first.
