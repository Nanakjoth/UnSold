"""Public mentor directory.

Only the public card projection is ever returned (old spec section 7: "private
fields must never be sent in the public-card API"). There is no route here that
reveals a mentor's private fields, stats internals, or identity — those surface
only through a session, and even then only the pseudonym.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from ..deps import limit
from ..errors import not_found
from ..mentor_corpus import all_mentors, get_mentor
from ..models import MentorCard, MentorListResponse

router = APIRouter(prefix="/api/mentors", tags=["mentors"])


@router.get("", response_model=MentorListResponse)
async def list_mentors(
    request: Request,
    domain: list[str] | None = Query(default=None),
    language: str | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
    _limited=Depends(limit),
) -> MentorListResponse:
    """Public mentor cards, optionally filtered by domain or language.

    Readable without an account so a person can see the shape of the directory
    before describing anything about themselves.
    """
    mentors = all_mentors(request.app.state.store)
    cards: list[MentorCard] = []
    for mentor in mentors:
        card = mentor.public_card
        if domain and not (set(domain) & set(card.domains)):
            continue
        if language and language not in card.languages:
            continue
        cards.append(mentor.to_card())
    return MentorListResponse(items=cards[:limit], total=len(cards))


@router.get("/{mentor_id}", response_model=MentorCard)
async def get_mentor_card(mentor_id: str, request: Request) -> MentorCard:
    """One mentor's public card. 404 for unknown ids."""
    mentor = get_mentor(request.app.state.store, mentor_id)
    if mentor is None:
        raise not_found("No mentor with that id.")
    return mentor.to_card()


__all__ = ["router"]
