"""Saved interests and discovery feedback tests (spec sections 5, 8-9)."""

from __future__ import annotations


def test_saved_requires_auth(client) -> None:
    assert client.get("/api/library/saved").status_code == 401
    assert client.post("/api/library/saved/bookbinding").status_code == 401


def test_save_and_list_and_unsave(client, authed) -> None:
    session = authed()
    saved = client.post("/api/library/saved/bookbinding", headers=session.headers)
    assert saved.status_code == 200
    slugs = [item["slug"] for item in saved.json()["items"]]
    assert slugs == ["bookbinding"]

    listed = client.get("/api/library/saved", headers=session.headers).json()
    assert [item["slug"] for item in listed["items"]] == ["bookbinding"]

    unsaved = client.delete("/api/library/saved/bookbinding", headers=session.headers)
    assert unsaved.status_code == 200
    assert unsaved.json()["items"] == []


def test_save_is_idempotent(client, authed) -> None:
    session = authed()
    client.post("/api/library/saved/bookbinding", headers=session.headers)
    second = client.post("/api/library/saved/bookbinding", headers=session.headers)
    assert [item["slug"] for item in second.json()["items"]] == ["bookbinding"]


def test_unsave_missing_is_not_an_error(client, authed) -> None:
    session = authed()
    response = client.delete("/api/library/saved/bookbinding", headers=session.headers)
    assert response.status_code == 200


def test_saving_unknown_interest_is_404(client, authed) -> None:
    session = authed()
    response = client.post("/api/library/saved/not-real", headers=session.headers)
    assert response.status_code == 404


def test_saved_lists_are_per_member(client, authed) -> None:
    """One member's saved list must never leak into another's (spec section 8)."""
    a = authed("a")
    b = authed("b")
    client.post("/api/library/saved/bookbinding", headers=a.headers)
    client.post("/api/library/saved/origami", headers=b.headers)

    a_items = client.get("/api/library/saved", headers=a.headers).json()["items"]
    b_items = client.get("/api/library/saved", headers=b.headers).json()["items"]
    assert [i["slug"] for i in a_items] == ["bookbinding"]
    assert [i["slug"] for i in b_items] == ["origami"]


def test_feedback_requires_auth(client) -> None:
    response = client.post(
        "/api/library/feedback",
        json={"interest_slug": "bookbinding", "action": "dismiss"},
    )
    assert response.status_code == 401


def test_feedback_records_and_confirms(client, authed) -> None:
    session = authed()
    response = client.post(
        "/api/library/feedback",
        headers=session.headers,
        json={
            "interest_slug": "bookbinding",
            "action": "dismiss",
            "reason": "not_relevant",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["interest_slug"] == "bookbinding"
    assert body["action"] == "dismiss"
    # Fewer than 3 samples: agreement is honestly withheld.
    assert body["agreement"] is None


def test_feedback_rejects_unknown_interest(client, authed) -> None:
    session = authed()
    response = client.post(
        "/api/library/feedback",
        headers=session.headers,
        json={"interest_slug": "not-real", "action": "dismiss"},
    )
    assert response.status_code == 404


def test_feedback_rejects_invalid_action(client, authed) -> None:
    session = authed()
    response = client.post(
        "/api/library/feedback",
        headers=session.headers,
        json={"interest_slug": "bookbinding", "action": "hate"},
    )
    assert response.status_code == 422


def test_agreement_summary_appears_with_enough_samples(client, authed) -> None:
    """Once three members give feedback, the share is returned (labelled)."""
    for label in ("a", "b", "c"):
        session = authed(label)
        client.post(
            "/api/library/feedback",
            headers=session.headers,
            json={"interest_slug": "bookbinding", "action": "save"},
        )
    d = authed("d")
    response = client.post(
        "/api/library/feedback",
        headers=d.headers,
        json={"interest_slug": "bookbinding", "action": "save"},
    )
    agreement = response.json()["agreement"]
    assert agreement is not None
    assert agreement["sample_size"] == 4
    assert agreement["share_matching"] == 1.0
    assert "Simulated" in agreement["label"]


def test_dismissal_never_hides_the_catalogue_entry(client, authed) -> None:
    """A dismissal is a signal, not a verdict (spec section 5)."""
    session = authed()
    client.post(
        "/api/library/feedback",
        headers=session.headers,
        json={"interest_slug": "bookbinding", "action": "dismiss"},
    )
    listing = client.get("/api/interests", params={"q": "bookbinding"}).json()
    assert any(item["slug"] == "bookbinding" for item in listing["items"])


def test_deleting_account_removes_saved_and_feedback(client, authed) -> None:
    session = authed()
    client.post("/api/library/saved/bookbinding", headers=session.headers)
    client.post(
        "/api/library/feedback",
        headers=session.headers,
        json={"interest_slug": "origami", "action": "want_to_try"},
    )
    deleted = client.delete("/api/auth/session", headers=session.headers).json()
    assert deleted["deleted"]["saved_interests"] == 1
    assert deleted["deleted"]["discovery_feedback"] == 1
    # A fresh session for the same token starts empty.
    fresh = client.get("/api/library/saved", headers=session.headers).json()
    assert fresh["items"] == []
