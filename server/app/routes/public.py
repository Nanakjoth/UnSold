"""Public trust surfaces: the Guardian playground and the aggregate stats feed.

Both routes are readable WITHOUT an account (UI redesign trust section):

* ``POST /api/guardian/try`` — paste a message and see exactly what the
  Guardian would do to it. The pipeline is the SAME one sessions use
  (scrub.py -> guardian.screen_message), run on the submitted text and then
  forgotten: nothing is written to the store and nothing user-shaped is
  logged. The response's `source` honestly names the classifier that ran.
* ``GET /api/public/stats`` — aggregates only (counts, shares, eval numbers):
  never member data, ids, message content, or per-record rows.

Registered in BOTH demo and production modes — they are not demo-only.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, Request

from ..deps import limit
from ..errors import ApiError
from ..guardian import screen_message
from ..mentor_corpus import all_mentors
from ..metrics import agreement_metric
from ..models import (
    AgreementStats,
    EvalRunMetrics,
    GuardianEvalStats,
    GuardianTryRequest,
    GuardianTryResponse,
    MentorCorpusStats,
    PublicStatsResponse,
)
from ..observability import log_event
from ..rate_limit import RateLimiter, _RateLimited
from ..scrub import scrub

router = APIRouter(prefix="/api", tags=["public"])

# Playground limit: stricter than the global limiter and always per-IP (the
# caller is anonymous, so there is no uid to key on). In-process like the
# global RateLimiter — honest about being per-process.
GUARDIAN_TRY_MAX_CHARS = 500
GUARDIAN_TRY_PER_MINUTE = 10
_guardian_try_limiter = RateLimiter(GUARDIAN_TRY_PER_MINUTE)

# Repo root is one level above server/ — same convention as routes/dev.py.
_EVAL_DIR = Path(__file__).resolve().parents[3] / "eval"

# Spec section 12: numbers only count as accuracy after this many HUMAN-
# reviewed labels. Mirrored from metrics.MIN_AGREEMENT_SAMPLES's role for
# the agreement share (CORE_REALIGNMENT P2.4: never a bare percentage).
MIN_REVIEWED_LABELS_FOR_ACCURACY = 30

_STATS_NOTICE = (
    "All mentors are synthetic. Eval numbers describe rule behaviour, not "
    "proven accuracy, until labels are human-reviewed."
)


@router.post("/guardian/try", response_model=GuardianTryResponse)
async def guardian_try(body: GuardianTryRequest, request: Request) -> GuardianTryResponse:
    """Screen one pasted message with the real Guardian pipeline. Stateless.

    Runs the exact session flow — scrub first (spec section 8), then the
    Guardian (spec 10.5) — and returns the verdict. Nothing typed here is
    stored or logged: only aggregate counters (lengths, categories, actions)
    are emitted, mirroring how the session flow logs without content.
    """
    # Per-IP sliding window; the global limiter cannot take a custom key with
    # a custom threshold, so this route carries its own (10/min, anonymous).
    ip = request.client.host if request.client else "unknown"
    key = f"guardian_try:{ip}"
    if not _guardian_try_limiter.check(key):
        log_event("rate_limited", key=key, path=request.url.path)
        raise _RateLimited()

    text = body.text
    if len(text) > GUARDIAN_TRY_MAX_CHARS:
        raise ApiError(
            400,
            "text_too_long",
            f"Keep the message under {GUARDIAN_TRY_MAX_CHARS} characters.",
        )

    cleaned = scrub(text)
    verdict, decision = screen_message(
        cleaned.text, "mentor", gemini=request.app.state.gemini
    )
    # What the recipient would see: scrubbed text, redacted when blocked
    # (decide() supplies REDACTED_TEXT; screen_message supplies the text).
    display = decision.display_text or cleaned.text

    # Structured audit line — counts and codes only, NEVER the text.
    log_event(
        "guardian_try",
        text_length=len(text),
        category=verdict.category,
        severity=decision.final_severity,
        action=decision.action,
        classifier_source=verdict.source,
        scrubbed=cleaned.changed,
    )

    notice = "Nothing you type here is stored or logged."
    if verdict.source == "gemini":
        notice += " A live Gemini classifier produced this verdict."
    else:
        notice += " A deterministic rules classifier ran (no live model)."

    return GuardianTryResponse(
        action=decision.action,
        severity=decision.final_severity,
        categories=[] if verdict.category == "NONE" else [verdict.category],
        is_pitch=decision.final_severity >= 2,
        display_text=display,
        scrubbed=cleaned.changed,
        source=verdict.source,
        notice=notice,
    )


def _guardian_eval_stats() -> GuardianEvalStats | None:
    """The latest eval run, aggregated. Returns None when the artifacts are
    absent or unreadable — the panel then says "no run" rather than inventing
    numbers (spec section 12 honesty)."""
    gold_path = _EVAL_DIR / "gold_set.jsonl"
    run_path = _EVAL_DIR / "last_run.json"
    if not gold_path.is_file() or not run_path.is_file():
        return None
    try:
        rows = [
            json.loads(line)
            for line in gold_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        run = json.loads(run_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None  # unreadable artifacts are treated as absent, never guessed

    total = len(rows)
    reviewed = sum(
        1 for r in rows if str(r.get("review_status", "unreviewed")) != "unreviewed"
    )

    test: EvalRunMetrics | None = None
    if "precision" in run and "recall" in run and "f1" in run:
        fpr = run.get("hard_negative_fpr")
        test = EvalRunMetrics(
            precision=float(run["precision"]),
            recall=float(run["recall"]),
            f1=float(run["f1"]),
            hard_negative_fpr=float(fpr) if fpr is not None else None,
        )

    return GuardianEvalStats(
        total_labels=total,
        labels_reviewed=reviewed,
        # Spec section 12: unreviewed labels are NOT ground truth, so the
        # numbers below 30 reviewed labels can never be called accuracy.
        accuracy_claimed=reviewed >= MIN_REVIEWED_LABELS_FOR_ACCURACY,
        test=test,
        run_at=run.get("created_at"),
    )


@router.get("/public/stats", response_model=PublicStatsResponse)
async def public_stats(request: Request, _limited=Depends(limit)) -> PublicStatsResponse:
    """Honest aggregate dashboard feed. Aggregates only — no member data.

    Registered in production as well as demo: everything here is a count,
    share, or eval number, never a user, id, or message.
    """
    store = request.app.state.store
    mentors = all_mentors(store)
    metric = agreement_metric(store)

    return PublicStatsResponse(
        mentors=MentorCorpusStats(
            count=len(mentors),
            all_synthetic=all(m.is_synthetic for m in mentors),
        ),
        guardian_eval=_guardian_eval_stats(),
        agreement=AgreementStats(
            shown=metric.share is not None,  # hidden below the sample threshold
            samples=metric.sample_size,
            share=metric.share,
        ),
        notice=_STATS_NOTICE,
    )


__all__ = ["router"]
