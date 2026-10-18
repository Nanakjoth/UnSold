"""Deletion, retention, and private-field isolation tests (spec sections 8-9)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.retention import delete_user_data, expiry_from, purge_expired
from app.store import InMemoryStore


def test_delete_user_data_removes_all_owned_collections() -> None:
    store = InMemoryStore()
    store.set("users", "u1", {"uid": "u1"})
    store.set("saved_interests", "u1__bookbinding", {"user_id": "u1", "interest_id": "int_bookbinding"})
    store.set("saved_interests", "u2__origami", {"user_id": "u2", "interest_id": "int_origami"})
    store.set("discovery_feedback", "u1__x", {"user_id": "u1", "action": "save"})
    store.set("users", "u2", {"uid": "u2"})

    deleted = delete_user_data(store, "u1")

    assert deleted == {"users": 1, "saved_interests": 1, "discovery_feedback": 1}
    assert store.get("users", "u1") is None
    assert store.get("users", "u2") is not None
    assert store.get("saved_interests", "u2__origami") is not None


def test_delete_user_data_on_unknown_user_is_safe() -> None:
    store = InMemoryStore()
    assert delete_user_data(store, "ghost") == {}


def test_delete_user_data_cascades_through_advice_core(client, authed) -> None:
    """Deleting a member must take their need, session, messages, and feedback.

    Spec section 8: deletion deletes. Before A1-A3 added the advice collections,
    only the three discovery collections were cleared and a member's chat history
    silently survived their own delete request. This pins the full cascade.
    """
    s = authed("del-cascade")

    # A need.
    need = client.post(
        "/api/needs", json={"text": "I want advice about switching careers into design." * 3},
        headers=s.headers,
    ).json()
    need_id = need["need_id"]

    # A session with a message, a mentor reply, and an ended state.
    mentor_id = client.get("/api/mentors", headers=s.headers).json()["items"][0]["id"]
    sid = client.post(
        "/api/sessions", json={"mentor_id": mentor_id, "need_id": need_id},
        headers=s.headers,
    ).json()["id"]
    client.post(
        f"/api/sessions/{sid}/messages",
        json={"text": "I want advice about switching careers into design."},
        headers=s.headers,
    )
    client.post(f"/api/sessions/{sid}/mentor-reply", headers=s.headers)
    assert client.post(f"/api/sessions/{sid}/end", headers=s.headers).status_code == 200

    # Mentee feedback (so `session_feedback` has a row).
    fb = client.post(
        f"/api/sessions/{sid}/feedback",
        json={"role": "mentee", "mentee": {
            "helpfulness_1_5": 5, "felt_pitched": "no", "would_recommend": True,
        }},
        headers=s.headers,
    )
    assert fb.status_code == 200

    store = client.app.state.store

    def count(collection: str, field: str, value: str) -> int:
        return sum(1 for d in store.list(collection, limit=5000) if d.get(field) == value)

    # Sanity: every advice-core record really exists before the delete.
    assert store.get("needs", need_id) is not None
    assert store.get("sessions", sid) is not None
    assert count("session_messages", "session_id", sid) >= 1
    assert count("session_feedback", "session_id", sid) >= 1

    deleted = client.delete("/api/auth/session", headers=s.headers).json()["deleted"]

    # Everything the member owned is gone, and each collection is reported.
    assert deleted["needs"] >= 1
    assert deleted["sessions"] >= 1
    assert deleted["session_messages"] >= 1
    assert deleted["session_feedback"] >= 1
    assert store.get("needs", need_id) is None
    assert store.get("sessions", sid) is None
    assert count("session_messages", "session_id", sid) == 0
    assert count("session_feedback", "session_id", sid) == 0


def test_delete_user_data_leaves_other_members_sessions(client, authed) -> None:
    """A member's delete must not touch another member's session or messages."""
    a = authed("del-a")
    b = authed("del-b")

    def make_session(s):
        mentor_id = s.client.get("/api/mentors", headers=s.headers).json()["items"][0]["id"]
        sid = s.client.post(
            "/api/sessions", json={"mentor_id": mentor_id}, headers=s.headers
        ).json()["id"]
        s.client.post(
            f"/api/sessions/{sid}/messages",
            json={"text": "I want advice about switching careers into design."},
            headers=s.headers,
        )
        return sid

    sid_a, sid_b = make_session(a), make_session(b)
    store = client.app.state.store

    def count_messages(session_id: str) -> int:
        return sum(
            1
            for d in store.list("session_messages", limit=5000)
            if d.get("session_id") == session_id
        )

    a.client.delete("/api/auth/session", headers=a.headers)

    # B's session and messages survive; A's are gone.
    assert store.get("sessions", sid_b) is not None
    assert count_messages(sid_b) >= 1
    assert store.get("sessions", sid_a) is None
    assert count_messages(sid_a) == 0


def test_purge_expired_removes_only_expired() -> None:
    store = InMemoryStore()
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    store.set("review_queue", "r1", {"expires_at": past, "id": "r1"})
    store.set("review_queue", "r2", {"expires_at": future, "id": "r2"})
    store.set("review_queue", "r3", {"id": "r3"})  # no expiry: never purged here

    purged = purge_expired(store, "review_queue")

    assert purged == 1
    assert store.get("review_queue", "r1") is None
    assert store.get("review_queue", "r2") is not None
    assert store.get("review_queue", "r3") is not None


def test_expiry_from_is_future_iso() -> None:
    raw = expiry_from(30)
    parsed = datetime.fromisoformat(raw)
    assert parsed > datetime.now(timezone.utc)


def test_api_delete_session_reports_counts(client, authed) -> None:
    session = authed()
    client.post("/api/auth/session", headers=session.headers)
    response = client.delete("/api/auth/session", headers=session.headers)
    assert response.status_code == 200
    assert response.json()["deleted"]["users"] >= 1
    # After deletion the same token yields a fresh, new identity.
    fresh = client.post("/api/auth/session", headers=session.headers).json()
    assert fresh["uid"] == session.uid


def test_store_update_missing_doc_raises() -> None:
    store = InMemoryStore()
    try:
        store.update("users", "nope", {"a": 1})
        raise AssertionError("expected KeyError")
    except KeyError:
        pass
