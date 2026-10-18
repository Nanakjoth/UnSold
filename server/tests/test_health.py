"""Health and public-config endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_healthz_returns_ok_only(demo_app) -> None:
    with TestClient(demo_app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_healthz_leaks_no_configuration(demo_app) -> None:
    with TestClient(demo_app) as client:
        body = client.get("/healthz").text
    for secret_fragment in ("project", "model", "key", "token", "embed"):
        assert secret_fragment not in body.lower()


def test_config_reports_demo_mode_and_no_secrets(demo_app) -> None:
    with TestClient(demo_app) as client:
        response = client.get("/api/config")
    assert response.status_code == 200
    payload = response.json()
    assert payload["demo"] is True
    assert payload["app_mode"] == "demo"
    assert payload["ai_available"] is False
    assert payload["notice"]
    assert "project" not in payload
    assert "GOOGLE_CLOUD" not in response.text


def test_unknown_api_route_is_json_404(demo_app) -> None:
    with TestClient(demo_app) as client:
        response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_root_without_built_spa_returns_helpful_page(demo_app) -> None:
    with TestClient(demo_app) as client:
        response = client.get("/some/client/route")
    assert response.status_code == 503
    assert "Frontend not built" in response.text


def test_demo_routes_not_registered_in_production_shape() -> None:
    """Production-mode apps must expose no demo/dev surface at all."""
    from app.main import create_app
    from tests.conftest import make_settings

    production_settings = make_settings(
        app_mode="production",
        google_cloud_project="example-project-123",
        google_cloud_location="us-central1",
        gemini_model="test-model",
        embed_model="test-embed",
        embed_dim=768,
    )
    app = create_app(production_settings)
    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"ok": True}
        assert client.get("/api/config").json()["demo"] is False
        # No dev-only surface exists yet; assert the route table stays that way.
        assert not any("/dev/" in route.path for route in app.routes)
