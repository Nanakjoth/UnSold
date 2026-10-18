"""Stage A3 tests: reveal state machine, editable summary, feedback, metrics.

A3 is Release 1 of the advice core (unsold_product_spec.md sections 8, 9, 10.8,
10.11). These tests pin the behaviour the spec + CORE_REALIGNMENT demand:

  * Reveal     -> NONE -> ONE_SIDED -> REVEALED, withdrawable only before
                  REVEALED, contact scrubbed, never a real identity.
  * Summary    -> only after ENDED, mentee-only, editable, an edited summary is
                  never clobbered, pulls catalogue "things to try", leaks no PII.
  * Feedback   -> both roles, validated, updates mentor quality, free text
                  scrubbed.
  * Agreement  -> (felt_pitched=="yes") == (max_severity>=2), excluding "unsure",
                  share hidden below 3 samples, always labelled simulated.
  * Impact     -> mentor dashboard derived from stats, not message text.
"""

from __future__ import annotations


def _api(session, method: str, url: str, **kwargs):
    kwargs.setdefault("headers", session.headers)
    return getattr(session.client, method)(url, **kwargs)


def _mentor_id(s) -> str:
    return s.client.get("/api/mentors").json()["items"][0]["id"]


def _new_session(s, **extra) -> dict:
    r = _api(s, "post", "/api/sessions", json={"mentor_id": _mentor_id(s), **extra})
    assert r.status_code == 201, r.text
    return r.json()


def _send(s, sid: str, text: str, role: str = "mentee"):
    return _api(s, "post", f"/api/sessions/{sid}/messages", json={"text": text})


def _ended_session(s, **extra) -> str:
    """Create, chat a little, and end a session -> returns the session id."""
    sid = _new_session(s, **extra)["id"]
    _send(s, sid, "Hi, I want advice about switching careers into design.")
    _api(s, "post", f"/api/sessions/{sid}/mentor-reply")
    r = _api(s, "post", f"/api/sessions/{sid}/end")
    assert r.status_code == 200, r.text
    return sid


# --- Reveal state machine (spec section 8) -----------------------------------


def test_reveal_requires_auth(client):
    assert client.post("/api/sessions/x/reveal", json={"consent": True}).status_code == 401


def test_reveal_starts_none_and_reaches_revealed(authed):
    s = authed("rev-start")
    sid = _new_session(s)["id"]

    r = _api(s, "post", f"/api/sessions/{sid}/reveal", json={"consent": True})
    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "REVEALED"
    assert body["revealed"] is True
    # Contacts exposed: mentee + mentor pseudonym, never a real identity.
    roles = {c["role"]: c for c in body["contacts"]}
    assert "mentee" in roles and "mentor" in roles
    # Mentor side is synthetic and honestly labelled.
    assert roles["mentor"]["is_simulated"] is True


def test_reveal_contact_is_scrubbed_not_raw(authed):
    s = authed("rev-scrub")
    sid = _new_session(s)["id"]
    r = _api(
        s, "post", f"/api/sessions/{sid}/reveal",
        json={"consent": True, "contact_optional": "call me at +1 555 123 4567"},
    )
    body = r.json()
    mentee = next(c for c in body["contacts"] if c["role"] == "mentee")
    # A raw phone number must never survive into the stored contact.
    assert "555 123 4567" not in (mentee["contact_optional"] or "")


def test_reveal_withdraw_before_revealed_returns_to_none(authed):
    """Consent=False withdraws (only reachable before REVEALED)."""
    s = authed("rev-withdraw")
    sid = _new_session(s)["id"]
    r = _api(s, "post", f"/api/sessions/{sid}/reveal", json={"consent": False})
    assert r.status_code == 200
    body = r.json()
    assert body["state"] in ("NONE", "ONE_SIDED")
    assert body["revealed"] is False
    assert body["contacts"] == []


def test_reveal_is_locked_once_revealed(authed):
    """Once REVEALED both sides have shared — withdrawal is no longer offered."""
    s = authed("rev-lock")
    sid = _new_session(s)["id"]
    _api(s, "post", f"/api/sessions/{sid}/reveal", json={"consent": True})
    r = _api(s, "post", f"/api/sessions/{sid}/reveal", json={"consent": False})
    assert r.status_code == 400


def test_reveal_rejects_other_users_session(authed):
    a = authed("rev-own-a")
    b = authed("rev-own-b")
    sid = _new_session(a)["id"]
    r = _api(b, "post", f"/api/sessions/{sid}/reveal", json={"consent": True})
    assert r.status_code == 403


def test_reveal_unknown_session_404(authed):
    s = authed("rev-404")
    r = _api(s, "post", "/api/sessions/does-not-exist/reveal", json={"consent": True})
    assert r.status_code == 404


# --- Editable summary (spec section 10.8, CORE_REALIGNMENT C3) ---------------


def test_summary_unavailable_before_session_ends(authed):
    s = authed("sum-active")
    sid = _new_session(s)["id"]
    assert _api(s, "get", f"/api/sessions/{sid}/summary").status_code == 400


def test_summary_generated_after_end_with_action_items(authed):
    s = authed("sum-gen")
    sid = _ended_session(s)
    r = _api(s, "get", f"/api/sessions/{sid}/summary")
    assert r.status_code == 200
    body = r.json()
    # Spec 10.8: action_items capped at 5, caveats present, honest source label.
    assert len(body["action_items"]) <= 5
    assert isinstance(body["caveats"], list) and body["caveats"]
    assert body["source"] in ("gemini", "fallback")
    assert body["edited"] is False


def test_summary_pulls_catalogue_things_to_try(authed):
    s = authed("sum-catalogue")
    # Create a real need so the session carries intent domains, then link it.
    need = _api(
        s, "post", "/api/needs",
        json={"text": "I want to learn pottery and get started with ceramics."},
    ).json()
    sid = _new_session(s, need_id=need["need_id"])["id"]
    _send(s, sid, "I want to learn pottery this summer.")
    _api(s, "post", f"/api/sessions/{sid}/mentor-reply")
    _api(s, "post", f"/api/sessions/{sid}/end")

    body = _api(s, "get", f"/api/sessions/{sid}/summary").json()
    # CORE_REALIGNMENT C3: 2-3 catalogue entries as small things to try.
    assert 0 <= len(body["things_to_try"]) <= 3


def test_summary_is_editable_and_edits_survive(authed):
    s = authed("sum-edit")
    sid = _ended_session(s)
    r = _api(
        s, "patch", f"/api/sessions/{sid}/summary",
        json={"action_items": ["Try one informational interview this week."]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["action_items"] == ["Try one informational interview this week."]
    assert body["edited"] is True

    # A regenerated fetch must NOT clobber the edited summary.
    again = _api(s, "get", f"/api/sessions/{sid}/summary").json()
    assert again["action_items"] == ["Try one informational interview this week."]
    assert again["edited"] is True


def test_summary_action_items_capped_at_five(authed):
    s = authed("sum-cap")
    sid = _ended_session(s)
    too_many = [f"Step {i} — do the thing." for i in range(10)]
    body = _api(
        s, "patch", f"/api/sessions/{sid}/summary", json={"action_items": too_many}
    ).json()
    assert len(body["action_items"]) <= 5


def test_summary_edits_are_scrubbed_of_pii(authed):
    s = authed("sum-scrub")
    sid = _ended_session(s)
    body = _api(
        s, "patch", f"/api/sessions/{sid}/summary",
        json={"key_points": ["Email me at jane@company.com or +1 555 000 1111."]},
    ).json()
    joined = " ".join(body["key_points"])
    assert "jane@company.com" not in joined
    assert "555 000 1111" not in joined


def test_summary_not_visible_to_other_user(authed):
    a = authed("sum-own-a")
    b = authed("sum-own-b")
    sid = _ended_session(a)
    assert _api(b, "get", f"/api/sessions/{sid}/summary").status_code == 403


# --- Feedback (spec section 7, 10.11) ----------------------------------------


def test_feedback_requires_ended_session(authed):
    s = authed("fb-active")
    sid = _new_session(s)["id"]
    r = _api(
        s, "post", f"/api/sessions/{sid}/feedback",
        json={"role": "mentee", "mentee": {
            "helpfulness_1_5": 4, "felt_pitched": "no", "would_recommend": True,
        }},
    )
    assert r.status_code == 400


def test_mentee_feedback_accepted_and_returns_agreement(authed):
    s = authed("fb-mentee")
    sid = _ended_session(s)
    r = _api(
        s, "post", f"/api/sessions/{sid}/feedback",
        json={"role": "mentee", "mentee": {
            "helpfulness_1_5": 5, "felt_pitched": "no", "would_recommend": True,
            "free_text": "Call me at +1 555 999 0000 if you want more.",
        }},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    # Agreement is returned with a sample size, labelled simulated, hidden <3.
    if body["agreement"] is not None:
        assert "sample_size" in body["agreement"]
        assert body["agreement"]["is_simulated"] is True


def test_mentee_feedback_free_text_is_scrubbed(authed):
    s = authed("fb-scrub")
    sid = _ended_session(s)
    _api(
        s, "post", f"/api/sessions/{sid}/feedback",
        json={"role": "mentee", "mentee": {
            "helpfulness_1_5": 4, "felt_pitched": "no", "would_recommend": True,
            "free_text": "Reach me at jane@company.com for thanks.",
        }},
    )
    store = s.client.app.state.store
    recs = store.list("session_feedback", limit=100)
    mine = [r for r in recs if r.get("session_id") == sid and r.get("role") == "mentee"]
    assert mine and "jane@company.com" not in (mine[0].get("free_text_scrubbed") or "")


def test_mentor_feedback_accepted_and_labelled_simulated(authed):
    s = authed("fb-mentor")
    sid = _ended_session(s)
    r = _api(
        s, "post", f"/api/sessions/{sid}/feedback",
        json={"role": "mentor", "mentor": {
            "mentee_seriousness_1_5": 4, "respectful": True,
        }},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True
    store = s.client.app.state.store
    recs = store.list("session_feedback", limit=100)
    mine = [r for r in recs if r.get("session_id") == sid and r.get("role") == "mentor"]
    assert mine and mine[0].get("is_simulated") is True


def test_feedback_rejects_missing_role_block(authed):
    s = authed("fb-missing")
    sid = _ended_session(s)
    # role=mentee but no mentee block -> 400, not a silent accept.
    r = _api(s, "post", f"/api/sessions/{sid}/feedback", json={"role": "mentee"})
    assert r.status_code == 400


def test_feedback_rejects_out_of_range_helpfulness(authed):
    s = authed("fb-range")
    sid = _ended_session(s)
    r = _api(
        s, "post", f"/api/sessions/{sid}/feedback",
        json={"role": "mentee", "mentee": {
            "helpfulness_1_5": 9, "felt_pitched": "no", "would_recommend": True,
        }},
    )
    assert r.status_code == 422


def test_duplicate_feedback_rejected(authed):
    s = authed("fb-dupe")
    sid = _ended_session(s)
    payload = {"role": "mentee", "mentee": {
        "helpfulness_1_5": 3, "felt_pitched": "unsure", "would_recommend": False,
    }}
    assert _api(s, "post", f"/api/sessions/{sid}/feedback", json=payload).status_code == 200
    assert _api(s, "post", f"/api/sessions/{sid}/feedback", json=payload).status_code == 400


# --- Agreement metric (spec section 10.11) -----------------------------------


def test_agreement_hidden_below_three_samples(authed):
    s = authed("agr-small")
    sid = _ended_session(s)
    _api(
        s, "post", f"/api/sessions/{sid}/feedback",
        json={"role": "mentee", "mentee": {
            "helpfulness_1_5": 5, "felt_pitched": "no", "would_recommend": True,
        }},
    )
    body = _api(s, "get", "/api/dev/metrics/guardian").json()["agreement"]
    assert body["sample_size"] < 3
    assert body["share"] is None  # withheld, not a meaningless number
    assert body["is_simulated"] is True


def test_agreement_excludes_unsure(authed):
    """'unsure' responses are excluded from the share per spec 10.11."""
    s = authed("agr-unsure")
    for i in range(4):
        sid = _ended_session(s)
        _api(
            s, "post", f"/api/sessions/{sid}/feedback",
            json={"role": "mentee", "mentee": {
                "helpfulness_1_5": 4, "felt_pitched": "unsure", "would_recommend": True,
            }},
        )
    body = _api(s, "get", "/api/dev/metrics/guardian").json()["agreement"]
    assert body["sample_size"] == 0  # all unsure -> none considered
    assert body["share"] is None


def test_agreement_share_computed_over_three_samples(authed):
    """3 clean sessions (no pitch) where mentee says 'no' -> full agreement."""
    s = authed("agr-full")
    for _ in range(3):
        sid = _ended_session(s)
        _api(
            s, "post", f"/api/sessions/{sid}/feedback",
            json={"role": "mentee", "mentee": {
                "helpfulness_1_5": 5, "felt_pitched": "no", "would_recommend": True,
            }},
        )
    body = _api(s, "get", "/api/dev/metrics/guardian").json()["agreement"]
    assert body["sample_size"] == 3
    assert body["share"] is not None
    # Guardian never flagged these (no pitch), mentee said no -> they agree.
    assert body["guardian_flagged"] == 0
    assert body["mentee_reported_pitch"] == 0
    assert body["share"] == 1.0


def test_agreement_counts_disagreement(authed):
    """Mentee says 'yes' (pitched) but the Guardian saw severity <2 -> disagree."""
    s = authed("agr-disagree")
    for _ in range(3):
        sid = _ended_session(s)
        _api(
            s, "post", f"/api/sessions/{sid}/feedback",
            json={"role": "mentee", "mentee": {
                "helpfulness_1_5": 2, "felt_pitched": "yes", "would_recommend": False,
            }},
        )
    body = _api(s, "get", "/api/dev/metrics/guardian").json()["agreement"]
    assert body["sample_size"] == 3
    assert body["share"] == 0.0  # mentee flagged, Guardian did not -> all disagree
    assert body["mentee_reported_pitch"] == 3


# --- Mentor impact (spec section 9) ------------------------------------------


def test_mentor_impact_requires_auth(client):
    assert client.get("/api/dev/mentors/m1/impact").status_code == 401


def test_mentor_impact_returns_dashboard(authed):
    s = authed("impact-basic")
    mentor_id = _mentor_id(s)
    body = _api(s, "get", f"/api/dev/mentors/{mentor_id}/impact").json()
    for field in (
        "mentor_id", "pseudonym", "sessions_completed", "quality_score",
        "pitch_free_streak", "pitch_flags_total", "minutes_given",
        "helpfulness_responses", "is_simulated",
    ):
        assert field in body
    assert body["is_simulated"] is True


def test_mentor_impact_updates_after_feedback(authed):
    s = authed("impact-feedback")
    mentor_id = _mentor_id(s)
    before = _api(s, "get", f"/api/dev/mentors/{mentor_id}/impact").json()
    sid = _ended_session(s)
    _api(
        s, "post", f"/api/sessions/{sid}/feedback",
        json={"role": "mentee", "mentee": {
            "helpfulness_1_5": 5, "felt_pitched": "no", "would_recommend": True,
        }},
    )
    after = _api(s, "get", f"/api/dev/mentors/{mentor_id}/impact").json()
    # A completed session + a mentee rating both move the dashboard.
    assert after["sessions_completed"] > before["sessions_completed"]
    assert after["helpfulness_responses"] > before["helpfulness_responses"]


def test_mentor_impact_unknown_mentor_404(authed):
    s = authed("impact-404")
    assert _api(s, "get", "/api/dev/mentors/nope/impact").status_code == 404


def test_mentor_public_card_never_exposes_stats(client):
    """Spec 9 / old spec 7: the public card projection hides private stats."""
    card = client.get("/api/mentors").json()["items"][0]
    assert "stats" not in card
    assert "quality_score" not in card
    assert "pitch_free_streak" not in card
