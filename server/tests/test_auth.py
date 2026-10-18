"""Authentication, authorization, and demo isolation tests (spec sections 8-9)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import RateLimiter, make_settings


def test_protected_route_requires_token(client) -> None:
    response = client.post("/api/auth/session")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "missing_token"


def test_malformed_token_rejected(client) -> None:
    response = client.post(
        "/api/auth/session", headers={"Authorization": "Bearer not-a-token"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


def test_tampered_token_rejected(client) -> None:
    good = client.post("/api/dev/demo-login", json={"label": "default"}).json()["token"]
    tampered = good[:-6] + ("000000" if good[-6:] != "000000" else "111111")
    response = client.post(
        "/api/auth/session", headers={"Authorization": f"Bearer {tampered}"}
    )
    assert response.status_code == 401


def test_wrong_scheme_rejected(client) -> None:
    token = client.post("/api/dev/demo-login", json={"label": "default"}).json()["token"]
    response = client.post(
        "/api/auth/session", headers={"Authorization": f"Basic {token}"}
    )
    assert response.status_code == 401


def test_session_is_get_or_create_and_stable(authed) -> None:
    session = authed()
    first = session.client.post("/api/auth/session", headers=session.headers).json()
    second = session.client.post("/api/auth/session", headers=session.headers).json()
    assert first["uid"] == second["uid"] == session.uid
    assert first["pseudonym"] == second["pseudonym"]
    assert first["is_synthetic"] is True


def test_pseudonym_is_adjective_animal_number(authed) -> None:
    session = authed()
    pseudonym = session.client.post(
        "/api/auth/session", headers=session.headers
    ).json()["pseudonym"]
    parts = pseudonym.split("-")
    assert len(parts) == 3
    assert parts[2].isdigit()


def test_two_labels_get_distinct_identities(client) -> None:
    a = client.post("/api/dev/demo-login", json={"label": "a"}).json()
    b = client.post("/api/dev/demo-login", json={"label": "b"}).json()
    assert a["uid"] != b["uid"]
    assert a["pseudonym"] != b["pseudonym"]


def test_profile_update_sets_language(client, authed) -> None:
    session = authed()
    response = client.patch(
        "/api/auth/session",
        headers=session.headers,
        json={"language": "en-IN"},
    )
    assert response.status_code == 200
    assert response.json()["language"] == "en-IN"


def test_invalid_language_rejected(client, authed) -> None:
    session = authed()
    response = client.patch(
        "/api/auth/session", headers=session.headers, json={"language": "english"}
    )
    assert response.status_code == 422


def test_uid_is_never_client_claimable(client, authed) -> None:
    """A body-supplied uid must be ignored; identity comes from the token."""
    session = authed()
    response = client.post(
        "/api/auth/session",
        headers=session.headers,
        json={"uid": "attacker-chosen", "pseudonym": "sneaky-fox-123"},
    )
    assert response.status_code == 200
    assert response.json()["uid"] == session.uid
    assert response.json()["pseudonym"] != "sneaky-fox-123"


def test_user_cannot_read_another_users_data(client, authed) -> None:
    """Deleting one user's data must not touch another's."""
    a = authed("a")
    b = authed("b")
    a.client.post("/api/auth/session", headers=a.headers)
    b.client.post("/api/auth/session", headers=b.headers)

    deleted = a.client.delete("/api/auth/session", headers=a.headers).json()
    assert deleted["deleted"].get("users", 0) >= 1

    # B is unaffected and still resolvable.
    still_there = b.client.post("/api/auth/session", headers=b.headers)
    assert still_there.status_code == 200
    assert still_there.json()["uid"] == b.uid


def test_demo_routes_absent_in_production() -> None:
    production_settings = make_settings(
        app_mode="production",
        google_cloud_project="example-project-123",
        google_cloud_location="us-central1",
        gemini_model="test-model",
        embed_model="test-embed",
        embed_dim=768,
    )
    app = create_app(production_settings)
    assert not any("/dev/" in route.path for route in app.routes)


def test_production_app_constructs_without_credentials() -> None:
    """Building the app must not require cloud credentials (lazy Firebase init)."""
    production_settings = make_settings(
        app_mode="production",
        google_cloud_project="example-project-123",
        google_cloud_location="us-central1",
        gemini_model="test-model",
        embed_model="test-embed",
        embed_dim=768,
    )
    app = create_app(production_settings)
    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.get("/healthz").json() == {"ok": True}
        # Protected route rejects without ever touching Firebase.
        assert client.post("/api/auth/session").status_code == 401


def test_rate_limit_returns_429() -> None:
    settings = make_settings(rate_limit_per_minute=3)
    app = create_app(settings)
    with TestClient(app) as client:
        client.app.state.rate_limiter = RateLimiter(3)
        token = client.post("/api/dev/demo-login", json={"label": "default"}).json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        statuses = [
            client.post("/api/auth/session", headers=headers).status_code
            for _ in range(5)
        ]
    assert statuses.count(200) == 3
    assert statuses[-1] == 429


def test_rate_limit_is_per_caller_not_global() -> None:
    settings = make_settings(rate_limit_per_minute=2)
    app = create_app(settings)
    with TestClient(app) as client:
        client.app.state.rate_limiter = RateLimiter(2)
        a = client.post("/api/dev/demo-login", json={"label": "a"}).json()["token"]
        b = client.post("/api/dev/demo-login", json={"label": "b"}).json()["token"]
        ha, hb = {"Authorization": f"Bearer {a}"}, {"Authorization": f"Bearer {b}"}
        assert client.post("/api/auth/session", headers=ha).status_code == 200
        assert client.post("/api/auth/session", headers=ha).status_code == 200
        assert client.post("/api/auth/session", headers=ha).status_code == 429
        # Caller B is unaffected by A exhausting their own budget.
        assert client.post("/api/auth/session", headers=hb).status_code == 200
