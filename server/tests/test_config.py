"""Configuration validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from tests.conftest import make_settings


def test_demo_mode_needs_no_cloud_configuration() -> None:
    settings = make_settings(app_mode="demo")
    assert settings.is_demo is True
    assert settings.cloud_configured is False


def test_production_mode_requires_cloud_variables() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_settings(app_mode="production")
    message = str(excinfo.value)
    assert "GOOGLE_CLOUD_PROJECT" in message
    assert "GEMINI_MODEL" in message
    assert "EMBED_DIM" in message


def test_production_mode_rejects_placeholder_values() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_settings(
            app_mode="production",
            google_cloud_project="your-project-id",
            google_cloud_location="us-central1",
            gemini_model="REPLACE_WITH_CURRENT_FAST_MODEL_ID",
            embed_model="REPLACE_WITH_CURRENT_EMBEDDING_MODEL_ID",
            embed_dim=768,
        )
    assert "placeholder" in str(excinfo.value)


def test_production_mode_accepts_complete_configuration() -> None:
    settings = make_settings(
        app_mode="production",
        google_cloud_project="example-project-123",
        google_cloud_location="us-central1",
        gemini_model="example-model",
        embed_model="example-embed",
        embed_dim=768,
    )
    assert settings.is_demo is False
    assert settings.cloud_configured is True


def test_invalid_mode_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make_settings(app_mode="staging")


def test_limits_are_bounded() -> None:
    with pytest.raises(ValidationError):
        make_settings(max_query_chars=2)
    with pytest.raises(ValidationError):
        make_settings(rate_limit_per_minute=0)
    with pytest.raises(ValidationError):
        make_settings(data_retention_days=10_000)


def test_embed_dim_is_bounded() -> None:
    with pytest.raises(ValidationError):
        make_settings(embed_dim=1)


def test_defaults_match_documented_values() -> None:
    settings = make_settings()
    assert settings.max_query_chars == 300
    assert settings.rate_limit_per_minute == 20
    assert settings.data_retention_days == 30
    assert settings.firestore_db == "(default)"
