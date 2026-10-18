"""Advice-core routes: interpret a need and return grounded mentor matches.

This is the heart of the product (docs/DECISIONS.md re-scope). The flow:

1. The mentee describes a situation in free text.
2. The text is scrubbed (PII tokens, spec section 8), then interpreted into a
   structured, editable `NeedIntent`.
3. Mentors are retrieved and re-ranked; up to three grounded matches are
   returned with explanations, watch-outs, and starter questions.

Every response is labelled with its real source — `"gemini"` only when a live
model actually produced the interpretation/re-rank, `"keyword"`/`"fallback"`
otherwise (old spec section 13). No match is ever dressed up as stronger than it
is: a low-confidence result sets `no_strong_match` rather than pretending.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request

from ..deps import current_user, limit
from ..matching import interpret_need, match_mentors
from ..mentor_corpus import all_mentors
from ..models import (
    AppUser,
    Need,
    NeedCreate,
    NeedInterpretation,
    NeedMatchesResponse,
)
from ..observability import log_event
from ..sample_scenarios import SampleScenario
from ..scrub import scrub

router = APIRouter(prefix="/api/needs", tags=["needs"])

NEEDS = "needs"


@router.get("/scenarios", response_model=list[SampleScenario])
async def list_sample_scenarios() -> list[SampleScenario]:
    """Public example situations a visitor can pick to see how matching works.

    Unauthenticated on purpose: these are generic, pre-written sample prompts on
    the advice front door (spec section 14) — no member data, no identity. Each
    is plain text a user could equally have typed themselves; the
    `intended_mentor_id` is a build-time seed hint, never used to influence a
    real match (which is computed from the corpus at request time).
    """
    from ..sample_scenarios import all_scenarios

    return all_scenarios()


@router.post("", response_model=NeedMatchesResponse)
async def create_need(
    body: NeedCreate,
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> NeedMatchesResponse:
    """Scrub, interpret, and match a described situation.

    Requires auth (the need is per-member and its `user_id` is the verified
    caller). Free text is scrubbed before interpretation, storage, and any model
    call — raw PII never reaches the store or a prompt.
    """
    settings = request.app.state.settings
    text = body.text[: settings.max_need_chars]

    # 1. Scrub before anything else sees the text.
    cleaned = scrub(text)
    gemini = request.app.state.gemini

    # 2. Interpret: live Gemini when it actually runs, else the real local path.
    interpretation_source = "fallback"
    intent = None
    questions = []
    if gemini is not None:
        from ..matching import _interpret_with_gemini

        live = _interpret_with_gemini(gemini, cleaned.text, body.language, body.money_involved)
        if live is not None:
            intent, questions = live
            interpretation_source = "gemini"
    if intent is None:
        intent, questions = interpret_need(
            cleaned.text,
            language=body.language,
            category=body.category,
            money_involved=body.money_involved,
        )

    interpretation = NeedInterpretation(
        summary=intent.short_summary,
        intent=intent,
        clarifying_questions=questions,
        interpretation_source=interpretation_source,  # type: ignore[arg-type]
    )

    # 3. Retrieve + re-rank against the synthetic corpus.
    matches, no_strong_match, retrieval_source = match_mentors(
        all_mentors(request.app.state.store),
        intent,
        cleaned.text,
        gemini=gemini,
    )

    need_id = "need_" + uuid.uuid4().hex[:16]
    record = Need(
        id=need_id,
        user_id=user.uid,
        text_scrubbed=cleaned.text,
        category=body.category,
        interpretation=interpretation,
        no_strong_match=no_strong_match,
        is_synthetic=settings.is_demo,
    )
    request.app.state.store.set(NEEDS, need_id, record.model_dump())
    log_event(
        "need_created",
        need_id=need_id,
        goal_type=intent.goal_type,
        interpretation_source=interpretation_source,
        retrieval_source=retrieval_source,
        match_count=len(matches),
        no_strong_match=no_strong_match,
        distress_level=intent.distress_level,
        scrubbed=cleaned.changed,
    )

    notice = None
    if no_strong_match:
        notice = (
            "We did not find a confident match for this yet. The mentors below "
            "are the closest we have — try adding a detail or two, or explore "
            "the catalogue while you refine it."
        )

    return NeedMatchesResponse(
        need_id=need_id,
        interpretation=interpretation,
        matches=matches,
        no_strong_match=no_strong_match,
        retrieval_source=retrieval_source,  # type: ignore[arg-type]
        notice=notice,
    )


__all__ = ["router"]
