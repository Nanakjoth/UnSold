"""Catalogue integrity and discovery-route tests (spec sections 5, 8, 13)."""

from __future__ import annotations

from app.catalogue import RELATIONSHIPS, build_interests, seed_catalogue
from app.models import RELATIONSHIP_TYPES
from app.store import InMemoryStore

VALID_CATEGORIES = {
    "Creative Practices",
    "Making & Repair",
    "Nature & Living Systems",
    "Movement & Play",
    "Music & Sound",
    "Food & Culture",
    "Design & Visual Thinking",
    "Games & Strategy",
    "Science & Everyday Experiments",
    "Community & Craft",
}


def test_catalogue_meets_size_target() -> None:
    interests = build_interests()
    assert 80 <= len(interests) <= 120, f"expected 80-120 entries, got {len(interests)}"


def test_catalogue_slugs_unique_and_well_formed() -> None:
    interests = build_interests()
    slugs = [i.slug for i in interests]
    assert len(set(slugs)) == len(slugs)
    for interest in interests:
        assert interest.slug.islower()
        assert " " not in interest.slug


def test_catalogue_categories_are_known() -> None:
    for interest in build_interests():
        assert interest.category in VALID_CATEGORIES, interest.slug


def test_catalogue_entries_are_marked_sample_content() -> None:
    for interest in build_interests():
        assert interest.is_sample_content is True


def test_catalogue_entries_have_required_fields() -> None:
    """Every entry must be usable by both people and models (spec section 8)."""
    for interest in build_interests():
        assert interest.short_description, interest.slug
        assert interest.long_description, interest.slug
        assert interest.beginner_step, interest.slug
        assert interest.tags, interest.slug
        assert interest.skills, interest.slug
        assert interest.materials, interest.slug
        assert interest.ways_of_thinking, interest.slug
        assert interest.accessibility_notes, interest.slug
        assert interest.solo_or_group, interest.slug
        assert interest.online_or_in_person, interest.slug
        assert interest.languages == ["en"], interest.slug
        assert interest.source_notes, interest.slug


def test_every_entry_participates_in_at_least_two_edges() -> None:
    store = InMemoryStore()
    seed_catalogue(store)
    records = store.list(RELATIONSHIPS, limit=1000)
    touched: set[str] = set()
    for record in records:
        assert record["type"] in RELATIONSHIP_TYPES
        touched.add(record["from_slug"])
        touched.add(record["to_slug"])
    slugs = {i.slug for i in build_interests()}
    assert touched == slugs, f"unlinked entries: {slugs - touched}"
    assert len(records) >= 150


def test_edge_endpoints_exist() -> None:
    store = InMemoryStore()
    seed_catalogue(store)
    slugs = {i.slug for i in build_interests()}
    for record in store.list(RELATIONSHIPS, limit=1000):
        assert record["from_slug"] in slugs
        assert record["to_slug"] in slugs


def test_embedded_edges_match_relationship_records() -> None:
    """Compact embedded edges must mirror the reviewable relationship records."""
    store = InMemoryStore()
    seed_catalogue(store)
    slugs = {i.slug for i in build_interests()}
    pairs = {
        (r["from_slug"], r["to_slug"]) for r in store.list(RELATIONSHIPS, limit=1000)
    }
    for interest in build_interests():
        for edge in interest.relationship_edges:
            assert (interest.slug, edge.to_slug) in pairs, (
                f"{interest.slug} -> {edge.to_slug} missing from reviewable records"
            )
        assert interest.slug in slugs


# --- Discovery routes --------------------------------------------------------


def test_list_interests_returns_page(client) -> None:
    response = client.get("/api/interests")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 80
    assert len(body["items"]) == body["limit"]
    assert body["search_source"] == "keyword"
    assert body["ai_search_available"] is False


def test_search_matches_keywords(client) -> None:
    response = client.get("/api/interests", params={"q": "paper"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] > 0
    # Every returned card should actually relate to paper via some field.
    slugs = {item["slug"] for item in body["items"]}
    assert "bookbinding" in slugs or "origami" in slugs or "paper-circuits" in slugs


def test_search_with_no_hits_is_empty_not_fabricated(client) -> None:
    response = client.get("/api/interests", params={"q": "zzzzunlikelyqueryzzzz"})
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []


def test_category_filter(client) -> None:
    response = client.get("/api/interests", params={"category": "Food & Culture"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] > 0
    assert all(item["category"] == "Food & Culture" for item in body["items"])


def test_beginner_filter(client) -> None:
    response = client.get("/api/interests", params={"beginner": "true"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] > 0
    assert all(item["difficulty"] == "beginner" for item in body["items"])


def test_mode_filter_online(client) -> None:
    response = client.get("/api/interests", params={"mode": "online"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] > 0
    assert all("online" in item["online_or_in_person"] for item in body["items"])


def test_pagination_is_stable(client) -> None:
    first = client.get("/api/interests", params={"limit": 10, "offset": 0}).json()
    second = client.get("/api/interests", params={"limit": 10, "offset": 10}).json()
    first_slugs = [i["slug"] for i in first["items"]]
    second_slugs = [i["slug"] for i in second["items"]]
    assert not set(first_slugs) & set(second_slugs)


def test_categories_endpoint_lists_facets(client) -> None:
    response = client.get("/api/interests/categories")
    assert response.status_code == 200
    items = response.json()["items"]
    assert {item["category"] for item in items} == VALID_CATEGORIES
    assert sum(item["count"] for item in items) >= 80


def test_detail_includes_expanded_relationships(client) -> None:
    response = client.get("/api/interests/bookbinding")
    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "bookbinding"
    assert body["related"], "expected at least one expanded relationship"
    for item in body["related"]:
        assert item["type"] in RELATIONSHIP_TYPES
        assert item["interest"]["slug"] != "bookbinding"
        assert "short_description" in item["interest"]


def test_detail_404_for_unknown_slug(client) -> None:
    response = client.get("/api/interests/not-a-real-interest")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_card_projection_has_no_long_text() -> None:
    """Cards carry scannable fields only; long content lives on the detail."""
    for interest in build_interests():
        card = interest.to_card()
        assert not hasattr(card, "long_description")
        assert not hasattr(card, "relationship_edges")
