# Core Realignment: Are we on track, what to change, what to do

> Based on `PROJECT_EXPLAINED.md`, `DECISIONS.md` and `global_discovery_platform_build_spec.md` as uploaded on 17 Oct 2026.
> I have not seen the code, so every status below comes from those documents. Anything I could not confirm is marked **(verify)**.

---

## 1. Verdict

**Direction: yes. Core value: not yet.**

- The 17 Oct re-scope was the right call. Advice is the front door again, the honesty model is strong, and the plumbing (scrubbing, auth, store seam, labelled Gemini client, 111 tests) is solid.
- But what is built so far (**A1**) is the *commodity* part of the idea: describe a situation, get three explained mentor matches. Free mentorship directories already exist.
- The parts that make this product different are **all still unbuilt**: the Guardian (pitch detection), the Friend Test, sessions, consent-based reveal, feedback with the agreement metric, and mentor impact stats.
- Nothing runs on Google Cloud AI yet. Live Gemini has never been called, there are no embeddings, no Model Armor, no Firestore, no deployment.
- Meanwhile a large share of effort went to the add-on (88 catalogue entries, 151 edges, two placeholder nav items).

**Plain answer: we are on the right road but only at stage A1 of A5. The unique idea is not demonstrable yet.**

---

## 2. Scorecard against the core idea

| Core capability | Status | Note |
|---|---|---|
| Anonymous, pseudonymous identity | Done | Demo tokens now; Firebase anonymous auth planned. |
| PII scrubbing before storage and model calls | Done | Deterministic regex; honest about limits. Sensitive Data Protection not used yet. |
| Describe situation, see interpretation | Done | Confirm the panel is actually **editable** by the user, not just visible **(verify)**. |
| Matching with written reasons | Done (keyword-based) | Transparent weights; grounded explanations; DIRECT vs CROSS_DOMAIN. This is not AI matching yet. |
| Honesty labels (`gemini` vs `fallback`/`keyword`) | Done | Excellent; keep it. |
| `no_strong_match` handling | Done | |
| Distress notice | Partly | The crisis-resource file was removed in the pivot. Confirm the support note uses **verified local resources**, none invented **(verify)**. |
| **Guardian: pitch / contact / steering detection** | **Not built** | This is the main differentiator. |
| **Friend Test** (did the mentor caution against spending?) | **Not built** | |
| In-app session chat | Not built | Needed to show the Guardian working. |
| Mentor simulator (honest / salesy / subtle) | Not built | Needed for demos and tests. |
| Consent-based identity reveal | Not built | |
| Editable summary and next steps | Not built | Discovery catalogue can feed "next steps" here. |
| Feedback + Guardian-vs-mentee agreement metric | Not built | |
| Mentor impact dashboard, pitch-free streak, quality score | Not built | |
| Gold set + evaluation report | Planned in `docs/AI_EVALUATION.md` | No results yet **(verify)**. |
| Live Gemini, embeddings, vector retrieval | Not done | Never run for lack of credentials. |
| Model Armor, Sensitive Data Protection | Not done | |
| Firestore, Cloud Run deployment | Not done | Untested; no `gcloud`/Docker on the dev machine. |
| Discovery catalogue (add-on) | Done | Over-invested relative to the core. |

---

## 3. What went wrong, and why it matters

1. **Two specs with opposite goals.** The discovery spec explicitly excludes mentorship and says "not a career portal". Following it faithfully removed the advice core. The owner then reversed it. That cost a stage of work and left a repo with two product stories.
2. **Effort went to the supporting layer.** 88 entries, 151 edges, validators and tests are impressive but are not what makes the product unique.
3. **The honest labels hide a bigger gap.** Because everything falls back correctly, the app *looks* complete locally. The honest status is that no Google AI service has been exercised.
4. **Two names.** The docs use "Atlas" while the original idea is "Unsold". Pick one before anything public.

---

## 4. What to change (decisions to record in `DECISIONS.md`)

| # | Change | How |
|---|---|---|
| C1 | **One spec of record.** Make `unsold_product_spec.md` (v2) the source of truth for the core. Mark `global_discovery_platform_build_spec.md` as "add-on reference only; its exclusions do not apply to the core". | Add a "Scope freeze" entry to `docs/DECISIONS.md` and a header note in the discovery spec. |
| C2 | **Freeze discovery.** No new catalogue entries, filters or edges. | Remove the People and Communities placeholder nav. Keep Explore as a secondary tab. |
| C3 | **Discovery's job is "next steps".** Surface 2 to 3 relevant catalogue entries inside the session summary and on the advice results page ("something small you could try"). | A3 task. |
| C4 | **Nav order:** Advice, My sessions, Explore. Mentors directory becomes secondary. | Small UI change. |
| C5 | **Front-door copy states the promise:** "Free. Anonymous. Mentors cannot sell to you, and an AI checks." | Update landing copy; keep claims modest until the Guardian is measured. |
| C6 | **Name decision.** Choose Atlas or Unsold (or a third). | Record in `DECISIONS.md`; one find-and-replace pass. |
| C7 | **Matching:** keep the deterministic path as the fallback, add embeddings retrieval + Gemini re-rank when cloud config is present, keep the same honesty labels. | Per v2 spec section 10.2 and 10.3. |
| C8 | **Crisis resources:** restore a `crisis_resources.json` with verified entries for the countries you target. | Human task; never let the AI invent numbers. |

---

## 5. What to do, in order

### P0: De-risk the cloud (do first; you must do these, the coding agent cannot)
1. On a machine or Cloud Shell with `gcloud`, run `gcloud auth application-default login` and pick the project that holds your credits.
2. Set a **budget alert** (25%, 50%, 90%).
3. Enable APIs: Agent Platform (`aiplatform`), Firestore, Cloud Run, Cloud Build, Artifact Registry, Model Armor (full list in v2 spec section 5).
4. In the docs, find the current Flash-class model ID for your region and the current embedding model. Put them in the env vars.
5. Ask the coding agent to make **one real Gemini call** end to end (the interpretation step) and confirm the label flips from `fallback` to `gemini`.
6. Deploy the existing app to Cloud Run so you know deployment works **before** more features exist.

Acceptance: a public Cloud Run URL; the advice flow works on it; at least one response shows `interpretation_source: "gemini"`.

### P1: Stage A2 (the differentiator): Session + Guardian + Friend Test
Build in this order:
1. Sessions API and session chat UI (text, realtime or polling is fine).
2. **Guardian** with four layers: rules → Model Armor (when configured) → Gemini classifier (JSON schema) → deterministic action policy (ALLOW / WARN / BLOCK_AND_REDACT, 3 strikes). Log decisions without message text. Spec: v2 section 10.5.
3. **Friend Test** (`money_stance`) per v2 section 10.6.
4. **Mentor simulator** with honest, salesy and subtle modes, labelled "Simulated mentor".
5. Tests: obvious pitch, contact solicitation, hard negatives ("courses can help but check free options first"), prompt-injection text, number-spelled-out evasions, another language, distress phrases.

Acceptance: in one session you can show an honest reply passing, a salesy reply redacted with a strike, a subtle reply tagged, and the Friend Test result.

### P2: Stage A3: Reveal + Summary + Feedback + Metrics
1. Consent-based reveal state machine (NONE → ONE_SIDED → REVEALED, withdraw before reveal).
2. Editable summary and next steps. Pull 2 to 3 catalogue entries as "things to try".
3. Feedback for both sides ("Did you feel pitched?" is the key question).
4. **Agreement metric** between the Guardian and mentee feedback; show it only with sample size and a "simulated" label while data is synthetic.
5. Mentor impact view: sessions, minutes, helpfulness, pitch-free streak, quality score.

Acceptance: a full run from need to feedback with an agreement number on the Metrics page.

### P3: Evaluate honestly
1. Build the 80-message gold set (v2 section 12), including 20 hard negatives. Two people review at least 30 labels.
2. Tune on `dev`, report on `test`: precision, recall, F1, hard-negative false-positive rate, confusion matrix, three example failures.
3. Rate the top match for 12 scenarios by hand.

Acceptance: `eval_runs` has a result; the README and deck quote only those numbers.

### P4: Only after P0 to P3
Spend Check (grounded search), Session Summary agent, translation, Firebase Auth + App Check, BigQuery/Looker, ADK agents, T&S queue, voice, Practice Room. Details in v2 spec sections 3 and 4.

---

## 6. Copy-paste prompts for the coding agent

**Scope freeze (run first)**
> Read `docs/DECISIONS.md`, `PROJECT_EXPLAINED.md` and `unsold_product_spec.md`. Add a "Scope freeze" entry to `docs/DECISIONS.md` stating: the advice core is the product; `unsold_product_spec.md` is the spec of record; the discovery spec is add-on reference only; discovery is frozen. Remove the People and Communities nav placeholders. Reorder nav to Advice, My sessions, Explore. Do not touch the catalogue. Report what changed.

**Cloud enablement (after you complete P0 steps 1 to 4)**
> Make the interpretation step call live Gemini when `GEMINI_MODEL` and project config are present, using `google-genai` in Agent Platform mode. Keep the deterministic fallback and the honesty labels. Add a script `scripts/check_gemini.py` that makes one real call and prints the source label. Verify every SDK call against current official docs. Do not fake a live call.

**Stage A2**
> Implement Stage A2 from `unsold_product_spec.md`: sessions API and chat UI, the four-layer Guardian (sections 10.5), Friend Test (10.6), and the mentor simulator (10.12). The Guardian action policy must be deterministic code. Log decisions without message text. Write tests for obvious pitches, contact solicitation, hard negatives, prompt injection, spelled-out number evasions, non-English pitches and distress phrases. Stop and report when tests pass.

**Stage A3**
> Implement Stage A3: consent-based reveal (section 8), an editable session summary with 2 to 3 catalogue "things to try", feedback for both roles, the Guardian-vs-mentee agreement metric (10.11), and the mentor impact view. Label agreement as simulated while data is synthetic and hide it below 3 samples. Stop and report.

**Evaluation**
> Create `eval/gold_set.jsonl` (80 mentor messages, 40 clean including 20 hard negatives, 40 pitches) and `scripts/run_eval.py` reporting precision, recall, F1, per-category recall, hard-negative false-positive rate and a confusion matrix on the `test` split. Mark generated labels as "unreviewed" until a human reviews them. Store results and show them on the Metrics page.

---

## 7. How you will know we are on track

Within the next two stages you should be able to run this 3-minute demo on a deployed URL:
1. Describe a money-related career decision. See the interpretation and edit it.
2. See 3 matches with grounded reasons, one cross-domain.
3. Start a session. Receive an honest mentor reply (passes).
4. Trigger a salesy reply: it is redacted and the mentor gets a strike.
5. Trigger a subtle reply: it is tagged "Possible promotion".
6. End the session: see the Friend Test result and an editable summary with next steps.
7. Submit feedback; see the Guardian-vs-mentee agreement on the Metrics page, labelled as simulated.

If any of steps 3 to 7 is missing, the unique idea is not yet visible.

---

## 8. Risks and honest notes

- **Time.** If the AI Builder Cup submission is still your target, the official site gave 18 Oct as the deadline and the roadmap said "before October 18". Today is 17 Oct. A deployed URL, a PDF deck and a 3-minute public video are required. Confirm the cutoff time on your dashboard. If you are racing it, ship P0 and P1, plus the thinnest slice of P2 (feedback and the agreement number), and cut everything else.
- **Guardian accuracy is unknown** until P3. Do not claim accuracy beyond the test-split numbers.
- **Synthetic data proves plumbing, not demand.** Say so in the product and any pitch.
- **Volunteer motivation under anonymity is a hypothesis.** The private badge and impact stats are the current bet.
- **Verification vs anonymity** still conflict. Keep "Verified (simulated)" labels until real verification exists.
- **Sunk cost.** The discovery catalogue stays as a supporting layer. Do not expand it.

---

## 9. Decisions only you can make

1. Final product name (Atlas or Unsold).
2. Whether Explore stays in the main nav or moves to a secondary tab.
3. Which countries to cover for verified crisis resources.
4. Whether the contest deadline still drives scope (changes what we cut).
5. Who completes P0 (cloud access) and by when.
