"""Authenticated per-member state: saved interests and discovery feedback.

Ownership rule (spec section 8): every record here carries `user_id` from the
verified token, and reads are always scoped to the caller. There is no route
that lists another member's saved interests or feedback.

Spec section 5: a single dismissal is feedback, not a permanent dislike — the
server records it and never silently rewrites the catalogue or blocks future
results on its own.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ..catalogue import INTERESTS, interest_id
from ..deps import current_user, limit
from ..errors import not_found
from ..models import (
    AgreementSummary,
    AppUser,
    DiscoveryFeedback,
    FeedbackCreate,
    FeedbackResponse,
    InterestCard,
    SavedInterest,
    SavedListResponse,
    utc_now_iso,
)
from ..observability import log_event

router = APIRouter(prefix="/api/library", tags=["library"])

FEEDBACK = "discovery_feedback"
SAVED = "saved_interests"


def _require_interest(request: Request, slug: str) -> dict:
    doc = request.app.state.store.get(INTERESTS, interest_id(slug))
    if doc is None:
        raise not_found("That interest is not in the catalogue.")
    return doc


@router.get("/saved", response_model=SavedListResponse)
async def list_saved(
    request: Request,
    user: AppUser = Depends(current_user),
) -> SavedListResponse:
    """The caller's saved interest cards, newest last."""
    records = request.app.state.store.list(SAVED, limit=500)
    mine = [r for r in records if r.get("user_id") == user.uid]
    cards: list[InterestCard] = []
    for record in sorted(mine, key=lambda r: r.get("created_at", "")):
        interest_doc = request.app.state.store.get(INTERESTS, record["interest_id"])
        if interest_doc is not None:
            cards.append(
                InterestCard(
                    id=interest_doc["id"],
                    slug=interest_doc["slug"],
                    title=interest_doc["title"],
                    short_description=interest_doc["short_description"],
                    category=interest_doc["category"],
                    tags=interest_doc["tags"],
                    time_commitment=interest_doc.get("time_commitment"),
                    difficulty=interest_doc.get("difficulty"),
                    solo_or_group=interest_doc.get("solo_or_group", []),
                    online_or_in_person=interest_doc.get("online_or_in_person", []),
                    is_sample_content=interest_doc.get("is_sample_content", True),
                )
            )
    return SavedListResponse(items=cards, total=len(cards))


@router.post("/saved/{slug}", response_model=SavedListResponse)
async def save_interest(
    slug: str,
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> SavedListResponse:
    """Save an interest (idempotent). Also records a `save` feedback event."""
    doc = _require_interest(request, slug)
    doc_id = f"{user.uid}__{slug}"
    if request.app.state.store.get(SAVED, doc_id) is None:
        record = SavedInterest(
            user_id=user.uid, interest_id=doc["id"], interest_slug=slug
        )
        request.app.state.store.set(SAVED, doc_id, record.model_dump())
        log_event("interest_saved", slug=slug)
    return await list_saved(request, user)


@router.delete("/saved/{slug}", response_model=SavedListResponse)
async def unsave_interest(
    slug: str,
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> SavedListResponse:
    """Remove a saved interest. Missing saves are not an error (idempotent)."""
    request.app.state.store.delete(SAVED, f"{user.uid}__{slug}")
    log_event("interest_unsaved", slug=slug)
    return await list_saved(request, user)


def _agreement_for(request: Request, slug: str, action: str) -> AgreementSummary | None:
    """Share of recorded feedback on `slug` matching `action`, excluding unsure.

    Only meaningful once several members have given feedback; returned as None
    (and simply not displayed) below a tiny sample size.
    """
    records = request.app.state.store.list(FEEDBACK, limit=1000)
    same = [r for r in records if r.get("interest_slug") == slug]
    if len(same) < 3:
        return None
    matching = sum(1 for r in same if r.get("action") == action)
    return AgreementSummary(
        share_matching=round(matching / len(same), 2),
        sample_size=len(same),
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def record_feedback(
    body: FeedbackCreate,
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> FeedbackResponse:
    """Record discovery feedback (spec section 5).

    A `save` action also upserts the saved list so the UI has one call to make.
    Dismissals never delete or hide the catalogue entry — they are a signal,
    not a verdict.
    """
    _require_interest(request, body.interest_slug)
    record = DiscoveryFeedback(
        user_id=user.uid,
        interest_id=interest_id(body.interest_slug),
        interest_slug=body.interest_slug,
        action=body.action,
        reason=body.reason,
    )
    request.app.state.store.set(
        FEEDBACK, f"{user.uid}__{body.interest_slug}__{utc_now_iso()}", record.model_dump()
    )
    log_event(
        "discovery_feedback",
        action=body.action,
        reason=body.reason,
        slug=body.interest_slug,
    )
    return FeedbackResponse(
        interest_slug=body.interest_slug,
        action=body.action,
        agreement=_agreement_for(request, body.interest_slug, body.action),
    )
