"""Tests for the sample mentee scenarios (spec section 14 demo seed data).

Two guarantees:
1. `GET /api/needs/scenarios` serves all ten public sample prompts (no auth).
2. Every scenario's text, run through the real interpreter + matcher, ranks its
   intended focus mentor #1 — so clicking a scenario demonstrably surfaces that
   mentor rather than an arbitrary one.
"""

from __future__ import annotations

from app.mentor_corpus import MENTORS
from app.matching import interpret_need, match_mentors
from app.sample_scenarios import SCENARIOS
from app.scrub import scrub


def test_scenarios_endpoint_is_public_and_serves_ten(client):
    response = client.get("/api/needs/scenarios")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 10
    for item in items:
        # Each is a plain, sample-content prompt with a domain + intended mentor.
        assert item["is_sample_content"] is True
        assert item["text"].strip()
        assert item["domain"].strip()
        assert item["intended_mentor_id"].startswith("m-")


def test_scenarios_cover_the_five_focus_mentors():
    intended = {s.intended_mentor_id for s in SCENARIOS}
    # The five focus mentors, each reached by two scenarios.
    assert intended == {
        "m-ai-career-focused-lynx",
        "m-ai-learn-steady-sparrow",
        "m-founder-tech-bold-turtle",
        "m-founder-nontech-grounded-quail",
        "m-meditation-quiet-wren",
    }
    for mid in intended:
        assert any(m.id == mid for m in MENTORS), f"{mid} missing from corpus"


def test_every_scenario_surfaces_its_intended_mentor_rank_one():
    for sc in SCENARIOS:
        cleaned = scrub(sc.text).text
        intent, _ = interpret_need(cleaned, money_involved=sc.money_involved)
        matches, no_strong, _src = match_mentors(MENTORS, intent, cleaned, top_n=5)
        ids = [m.mentor.id for m in matches]
        assert ids, f"no matches for {sc.id}"
        assert ids[0] == sc.intended_mentor_id, (
            f"{sc.id}: expected {sc.intended_mentor_id} #1, got {ids[0]} (order {ids})"
        )
        assert no_strong is False


def test_mentor_corpus_has_thirty_five():
    # 30 base + 5 focus mentors.
    assert len(MENTORS) == 35
