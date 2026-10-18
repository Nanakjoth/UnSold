"""Catalogue service: seed building, keyword search, relationship expansion.

The catalogue is sample content (spec section 8: `is_sample_content=true` on
every seeded entry). Search here is deterministic keyword matching; the Gemini
intent layer (spec section 13, Stage 3) replaces the *query* side when a model
is configured, and every response labels which source produced it.

Edges live in the `interest_relationships` collection as explicit, reviewable
records, and are also embedded as a compact outgoing list on each interest
document so the detail route expands related entries in one extra read.
"""

from __future__ import annotations

import re
from typing import Any

from .catalogue_entries import EDGES, ENTRIES
from .models import (
    EmbeddedEdge,
    Interest,
    InterestCard,
    RelatedInterest,
    RelationshipType,
)
from .store import Store

INTERESTS = "interests"
RELATIONSHIPS = "interest_relationships"

_WORD = re.compile(r"[a-z0-9]+")


def interest_id(slug: str) -> str:
    """Stable, human-readable document id for a catalogue entry."""
    return f"int_{slug}"


def relationship_id(from_slug: str, to_slug: str, kind: str) -> str:
    return f"rel_{from_slug}__{to_slug}__{kind}"


def build_interests() -> list[Interest]:
    """Construct the full catalogue from the seed module."""
    outgoing: dict[str, list[EmbeddedEdge]] = {entry["slug"]: [] for entry in ENTRIES}
    for from_slug, to_slug, kind, _note in EDGES:
        if from_slug in outgoing:
            outgoing[from_slug].append(
                EmbeddedEdge(to_slug=to_slug, type=kind, note=_note)
            )

    interests: list[Interest] = []
    for entry in ENTRIES:
        data = dict(entry)
        slug = data["slug"]
        interests.append(
            Interest(
                id=interest_id(slug),
                relationship_edges=outgoing.get(slug, []),
                **data,
            )
        )
    return interests


def seed_catalogue(store: Store) -> dict[str, int]:
    """Idempotently load the catalogue and its relationship records."""
    interests = build_interests()
    for interest in interests:
        store.set(INTERESTS, interest.id, interest.model_dump())

    seen: set[str] = set()
    edges_written = 0
    for from_slug, to_slug, kind, note in EDGES:
        if (from_slug, to_slug) in seen:
            continue  # one record per ordered pair; duplicates would confuse review
        seen.add((from_slug, to_slug))
        record = {
            "from_slug": from_slug,
            "to_slug": to_slug,
            "type": kind,
            "note": note,
            "is_sample_content": True,
        }
        store.set(RELATIONSHIPS, relationship_id(from_slug, to_slug, kind), record)
        edges_written += 1
    return {"interests": len(interests), "relationships": edges_written}


# --- Search ------------------------------------------------------------------


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _score(interest: Interest, query_tokens: list[str]) -> float:
    """Deterministic keyword score; title > tags > descriptions > other fields."""
    if not query_tokens:
        return 0.0
    title = set(_tokens(interest.title))
    tags = set(_tokens(" ".join(interest.tags)))
    descriptions = set(
        _tokens(interest.short_description + " " + interest.long_description)
    )
    other = set(
        _tokens(
            " ".join(interest.materials + interest.skills + interest.ways_of_thinking)
            + " "
            + interest.category
        )
    )
    score = 0.0
    for token in query_tokens:
        if token in title:
            score += 3.0
        if token in tags:
            score += 2.0
        if token in descriptions:
            score += 1.0
        if token in other:
            score += 0.5
    return score / len(query_tokens)


def _has_all(values: list[str], required: list[str]) -> bool:
    return all(item in values for item in required)


def search_interests(
    interests: list[Interest],
    *,
    query: str = "",
    categories: list[str] | None = None,
    difficulty: str | None = None,
    beginner_friendly: bool | None = None,
    solo_or_group: str | None = None,
    online_or_in_person: str | None = None,
    tags: list[str] | None = None,
) -> list[tuple[float, Interest]]:
    """Filter then score the catalogue. Returns (score, interest) pairs.

    An empty query returns every match with score 0 (browse mode). A query with
    no keyword hits returns an empty list — the caller decides how to present
    that honestly (spec section 13: never claim an AI recommendation ran).
    """
    query_tokens = _tokens(query)
    results: list[tuple[float, Interest]] = []
    for interest in interests:
        if categories and interest.category not in categories:
            continue
        if difficulty and interest.difficulty != difficulty:
            continue
        if beginner_friendly is not None:
            is_beginner = interest.difficulty == "beginner"
            if is_beginner != beginner_friendly:
                continue
        if solo_or_group and solo_or_group not in interest.solo_or_group:
            continue
        if online_or_in_person and online_or_in_person not in interest.online_or_in_person:
            continue
        if tags and not _has_all(interest.tags, tags):
            continue
        score = _score(interest, query_tokens)
        if query_tokens and score <= 0.0:
            continue
        results.append((score, interest))

    results.sort(key=lambda pair: (-pair[0], pair[1].title.lower()))
    return results


# --- Relationship expansion --------------------------------------------------


def expand_related(store: Store, interest: Interest) -> list[RelatedInterest]:
    """Expand one interest's outgoing edges into full related cards."""
    related: list[RelatedInterest] = []
    for edge in interest.relationship_edges:
        target = store.get(INTERESTS, interest_id(edge.to_slug))
        if target is None:
            continue
        related.append(
            RelatedInterest(type=edge.type, note=edge.note, interest=_card_of(target))
        )
    return related


def _card_of(doc: dict[str, Any]) -> InterestCard:
    return InterestCard(
        id=doc["id"],
        slug=doc["slug"],
        title=doc["title"],
        short_description=doc["short_description"],
        category=doc["category"],
        tags=doc["tags"],
        time_commitment=doc.get("time_commitment"),
        difficulty=doc.get("difficulty"),
        solo_or_group=doc.get("solo_or_group", []),
        online_or_in_person=doc.get("online_or_in_person", []),
        is_sample_content=doc.get("is_sample_content", True),
    )


def card_from_doc(doc: dict[str, Any]) -> InterestCard:
    """Public card projection from a stored interest document."""
    return _card_of(doc)


def edge_type_valid(kind: str) -> bool:
    return kind in RelationshipType.__args__  # type: ignore[attr-defined]
