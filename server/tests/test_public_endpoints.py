"""Public trust surfaces: the Guardian playground + the aggregate stats feed.

The playground (POST /api/guardian/try) runs the REAL scrub + Guardian
pipeline on pasted text and stores nothing — these tests pin both the verdicts
and the absence of any persistence. The stats feed (GET /api/public/stats) is
aggregates only and stays honest: no accuracy claim until >= 30 gold labels
are human-reviewed (spec section 12), no agreement share below 3 honest
samples (spec 10.11), and an explicit "all mentors are synthetic" notice.
"""

from __future__ import annotations

import json

import pytest

from app.guardian import REDACTED_TEXT
from app.main import create_app
from app.routes.public import _guardian_try_limiter
from tests.conftest import make_settings

PITCH_TEXT = "Enroll now in my course at brightpath.com — limited seats, use my code SAVE20!"
BENIGN_TEXT = "Hi, I would like honest advice about switching careers."


@pytest.fixture(autouse=True)
def _fresh_guardian_try_budget():
    """The playground limiter is per-IP and every TestClient call shares an
    IP; reset it so tests never eat each other's 10/min budget."""
    _guardian_try_limiter.reset()
    yield
    _guardian_try_limiter.reset()


def _try(client, text: str):
    return client.post("/api/guardian/try", json={"text": text})


# --- POST /api/guardian/try --------------------------------------------------


def test_benign_message_is_allowed(client):
    r = _try(client, BENIGN_TEXT)
    assert r.status_code == 200
    body = r.json()
    assert body["action"] == "ALLOW"
    assert body["severity"] == 0
    assert body["is_pitch"] is False
    assert body["categories"] == []
    assert body["display_text"] == BENIGN_TEXT
    assert body["scrubbed"] is False


def test_obvious_pitch_is_blocked_and_redacted(client):
    r = _try(client, PITCH_TEXT)
    assert r.status_code == 200
    body = r.json()
    assert body["action"] == "BLOCK_AND_REDACT"
    assert body["severity"] == 3
    assert body["is_pitch"] is True  # severity >= 2
    assert body["categories"]  # a real category, not "NONE"
    assert body["display_text"] == REDACTED_TEXT  # what the recipient would see
    assert body["scrubbed"] is True  # brightpath.com was tokenised before screening


def test_pii_is_scrubbed_in_display_text(client):
    """ALLOW display is the scrubbed text — raw PII is never echoed back."""
    r = _try(client, "My name is Jordan Blake and I am switching careers.")
    assert r.status_code == 200
    body = r.json()
    assert body["action"] == "ALLOW"
    assert "Jordan Blake" not in body["display_text"]
    assert "[PERSON]" in body["display_text"]
    assert body["scrubbed"] is True


@pytest.mark.parametrize("text", ["", "   ", "\n\t "])
def test_empty_text_is_422(client, text):
    r = _try(client, text)
    assert r.status_code == 422


def test_missing_text_is_422(client):
    assert client.post("/api/guardian/try", json={}).status_code == 422


def test_over_500_chars_is_400_text_too_long(client):
    r = _try(client, "a" * 501)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "text_too_long"


def test_exactly_500_chars_is_accepted(client):
    assert _try(client, "a" * 500).status_code == 200


def test_nothing_submitted_to_the_playground_is_ever_stored(client):
    """The trust proof: no record of the text exists in any store collection."""
    r = _try(client, PITCH_TEXT)
    assert r.status_code == 200

    store = client.app.state.store
    dump = json.dumps(getattr(store, "_data", {}), default=str)
    assert PITCH_TEXT not in dump
    # Distinctive substrings must be absent too (not merely not-verbatim).
    assert "SAVE20!" not in dump
    assert "brightpath.com" not in dump


def test_source_label_is_honest(client):
    """Tests run without a live Gemini, so the label must say "fallback" —
    the same label the real fallback classifier reports."""
    from app.guardian import classify_fallback

    expected = classify_fallback(BENIGN_TEXT, "mentor").source
    assert expected == "fallback"  # never pretends a model ran
    assert _try(client, BENIGN_TEXT).json()["source"] == expected
    assert _try(client, PITCH_TEXT).json()["source"] == expected


def test_response_carries_an_honest_notice(client):
    body = _try(client, BENIGN_TEXT).json()
    assert body["notice"]
    assert "stored" in body["notice"] or "logged" in body["notice"]


def test_rate_limit_429_after_ten_within_a_minute(client):
    statuses = [_try(client, BENIGN_TEXT).status_code for _ in range(10)]
    assert statuses == [200] * 10
    blocked = _try(client, BENIGN_TEXT)
    assert blocked.status_code == 429
    assert blocked.headers.get("Retry-After") == "60"
    assert blocked.json()["error"]["code"] == "rate_limited"


# --- GET /api/public/stats ---------------------------------------------------


def test_public_stats_needs_no_auth_and_is_aggregate_only(client):
    r = client.get("/api/public/stats")
    assert r.status_code == 200
    body = r.json()
    # The response shape is exactly the aggregates — nothing per-record.
    assert set(body.keys()) == {"mentors", "guardian_eval", "agreement", "notice"}
    assert body["mentors"]["count"] >= 1  # demo seeding ran
    assert body["mentors"]["all_synthetic"] is True
    assert body["notice"]


def test_public_stats_agreement_hidden_below_three_samples(client):
    body = client.get("/api/public/stats").json()
    agreement = body["agreement"]
    assert isinstance(agreement["samples"], int)
    assert agreement["samples"] < 3
    assert agreement["shown"] is False
    assert agreement["share"] is None  # never a share without its samples


def test_public_stats_agreement_shown_after_three_samples(client):
    store = client.app.state.store
    for i in range(3):
        store.set(
            "session_feedback",
            f"fb{i}",
            {
                "id": f"fb{i}",
                "session_id": f"s{i}",
                "role": "mentee",
                "mentor_id": "m-x",
                "max_severity": 0,
                "felt_pitched": "no",
            },
        )
    agreement = client.get("/api/public/stats").json()["agreement"]
    assert agreement["shown"] is True
    assert agreement["samples"] == 3
    assert agreement["share"] == 1.0  # all three agree: severity 0 vs "no"


def test_public_stats_guardian_eval_never_overclaims(client):
    """Null when the eval artifacts are absent; otherwise well-formed and
    NEVER claiming accuracy while labels are unreviewed (spec section 12)."""
    body = client.get("/api/public/stats").json()
    ev = body["guardian_eval"]
    if ev is None:
        return  # honest absence — no run, no numbers
    assert ev["accuracy_claimed"] is (ev["labels_reviewed"] >= 30)
    assert 0 <= ev["labels_reviewed"] <= ev["total_labels"]
    if ev["labels_reviewed"] < 30:
        assert ev["accuracy_claimed"] is False
    if ev["test"] is not None:
        for field in ("precision", "recall", "f1"):
            assert isinstance(ev["test"][field], float)


# --- Both routes survive production mode -------------------------------------


def test_public_routes_registered_in_production_mode():
    """Guardian playground and stats are PUBLIC, not demo-only — the production
    route table must contain them (and still exclude /api/dev/*)."""
    production_settings = make_settings(
        app_mode="production",
        google_cloud_project="example-project-123",
        google_cloud_location="us-central1",
        gemini_model="test-model",
        embed_model="test-embed",
        embed_dim=768,
    )
    app = create_app(production_settings)
    paths = {route.path for route in app.routes}
    assert "/api/guardian/try" in paths
    assert "/api/public/stats" in paths
    assert not any("/dev/" in path for path in paths)
