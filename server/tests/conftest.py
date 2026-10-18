"""Shared test fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.rate_limit import RateLimiter


def make_settings(**overrides: object) -> Settings:
    """Build settings that ignore any local `.env` file, with safe test defaults."""
    defaults: dict[str, object] = {"web_dist": "__does_not_exist__"}
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)  # type: ignore[arg-type]


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest.fixture
def app(settings: Settings):
    from app.main import create_app

    return create_app(settings)


@pytest.fixture
def demo_app(app) -> app.__class__:  # kept for Phase 0 test compatibility
    return app


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        test_client.app.state.rate_limiter = RateLimiter(10_000)  # tests are chatty
        yield test_client


@pytest.fixture
def authed(client):
    """Helper returning a logged-in demo client plus its identity.

    `label` picks which demo identity to mint — tests that need two distinct
    members (e.g. for connection requests later) pass different labels.
    """

    class Session:
        def __init__(self, client, label: str) -> None:
            self.client = client
            response = client.post("/api/dev/demo-login", json={"label": label})
            assert response.status_code == 200, response.text
            payload = response.json()
            self.token = payload["token"]
            self.uid = payload["uid"]
            self.pseudonym = payload["pseudonym"]
            self.headers = {"Authorization": f"Bearer {self.token}"}

    def login(label: str = "default") -> Session:
        return Session(client, label)

    return login
