"""Public catalogue routes: browse, search, categories, and interest detail.

Everything here is readable without an account (spec section 4: explore the
catalogue before signing up). Responses never include user data; the only
per-user state (saved, feedback) lives behind authenticated routes.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from ..catalogue import INTERESTS, card_from_doc, expand_related, search_interests
from ..deps import limit
from ..errors import not_found
from ..models import (
    CategoryCount,
    CategoryListResponse,
    Interest,
    InterestCard,
    InterestDetail,
    InterestListResponse,
)
from ..observability import log_event

router = APIRouter(prefix="/api/interests", tags=["interests"])

_PAGE_SIZE = 24  # spec section 5: enough cards to browse, small enough to scan


def _all_interests(request: Request) -> list[Interest]:
    docs = request.app.state.store.list(INTERESTS, limit=500)
    return [Interest.model_validate(doc) for doc in docs]


@router.get("", response_model=InterestListResponse)
async def list_interests(
    request: Request,
    q: str = Query(default="", max_length=300),
    category: list[str] | None = Query(default=None),
    difficulty: str | None = Query(default=None, pattern="^(beginner|intermediate)$"),
    beginner: bool | None = Query(default=None),
    mode: str | None = Query(default=None, pattern="^(solo|group|online|in_person)$"),
    tag: list[str] | None = Query(default=None),
    limit: int = Query(default=_PAGE_SIZE, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _limited=Depends(limit),
) -> InterestListResponse:
    """Keyword search + filters over the sample catalogue.

    `mode` accepts solo/group/online/in_person; the first two map to
    `solo_or_group`, the latter two to `online_or_in_person`.
    """
    solo_or_group = mode if mode in ("solo", "group") else None
    online_or_in_person = mode if mode in ("online", "in_person") else None

    results = search_interests(
        _all_interests(request),
        query=q.strip(),
        categories=category,
        difficulty=difficulty,
        beginner_friendly=beginner,
        solo_or_group=solo_or_group,
        online_or_in_person=online_or_in_person,
        tags=tag,
    )
    page = results[offset : offset + limit]
    settings = request.app.state.settings

    if q.strip():
        log_event(
            "interest_search",
            result_count=len(results),
            query_chars=len(q.strip()),
        )

    return InterestListResponse(
        items=[card_from_doc(interest.model_dump()) for _score, interest in page],
        total=len(results),
        limit=limit,
        offset=offset,
        ai_search_available=settings.cloud_configured,
    )


@router.get("/categories", response_model=CategoryListResponse)
async def list_categories(request: Request) -> CategoryListResponse:
    """Category facet counts (spec section 5: honest, catalogue-backed filters)."""
    counts: dict[str, int] = {}
    for interest in _all_interests(request):
        counts[interest.category] = counts.get(interest.category, 0) + 1
    items = [
        CategoryCount(category=name, count=counts[name])
        for name in sorted(counts, key=lambda n: (-counts[n], n))
    ]
    return CategoryListResponse(items=items)


@router.get("/{slug}", response_model=InterestDetail)
async def get_interest(slug: str, request: Request) -> InterestDetail:
    """Full catalogue entry with expanded, labelled relationships."""
    doc = request.app.state.store.get(INTERESTS, f"int_{slug}")
    if doc is None:
        raise not_found("That interest is not in the catalogue.")
    interest = Interest.model_validate(doc)
    return InterestDetail(
        **interest.model_dump(),
        related=expand_related(request.app.state.store, interest),
    )
