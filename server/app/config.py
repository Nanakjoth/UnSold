"""Validated environment configuration.

All runtime configuration comes from the environment (optionally a local `.env`
file for development). Required Google Cloud fields are enforced only when the
app runs in production mode; demo mode must stay runnable without cloud
credentials. Placeholder values such as ``REPLACE_WITH_...`` are rejected in
production so a template can never be deployed as real configuration.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PLACEHOLDER_MARKERS = ("REPLACE_WITH", "your-project")
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings, loaded from environment variables / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # --- Runtime mode -------------------------------------------------------
    app_mode: Literal["demo", "production"] = "demo"

    # --- Google Cloud -------------------------------------------------------
    google_cloud_project: str | None = None
    google_cloud_location: str | None = None
    firestore_db: str = "(default)"

    # --- Gemini / embeddings ------------------------------------------------
    gemini_model: str | None = None
    gemini_model_strong: str | None = None
    embed_model: str | None = None
    embed_dim: int | None = Field(default=None, ge=2, le=4096)

    # --- Feature flags ------------------------------------------------------
    enable_dlp: bool = False
    enable_app_check: bool = False

    # --- Product limits -----------------------------------------------------
    # Retention window for user-owned records that carry `expires_at` (used by
    # the moderation/review queue and documented in the privacy doc).
    data_retention_days: int = Field(default=30, ge=1, le=365)
    max_query_chars: int = Field(default=300, ge=10, le=2000)
    # Free-text limit for an advice "need" description before scrubbing.
    max_need_chars: int = Field(default=4000, ge=200, le=20000)
    rate_limit_per_minute: int = Field(default=20, ge=1, le=600)

    # --- Serving ------------------------------------------------------------
    web_dist: str = str(_REPO_ROOT / "web" / "dist")

    # --- Demo-only ----------------------------------------------------------
    # Optional fixed secret for demo tokens; when empty a process-derived one
    # is used. Never read or required in production mode.
    dev_token_secret: str | None = None

    # --- Derived ------------------------------------------------------------
    @property
    def is_demo(self) -> bool:
        return self.app_mode == "demo"

    @property
    def cloud_configured(self) -> bool:
        """True when the Google Cloud fields hold real (non-placeholder) values."""
        return all(
            _is_real(value)
            for value in (
                self.google_cloud_project,
                self.google_cloud_location,
                self.gemini_model,
                self.embed_model,
                self.embed_dim,
            )
        )

    @model_validator(mode="after")
    def _validate_production_config(self) -> Settings:
        if self.app_mode != "production":
            return self

        missing: list[str] = []
        placeholder: list[str] = []
        named = (
            ("GOOGLE_CLOUD_PROJECT", self.google_cloud_project),
            ("GOOGLE_CLOUD_LOCATION", self.google_cloud_location),
            ("GEMINI_MODEL", self.gemini_model),
            ("EMBED_MODEL", self.embed_model),
            ("EMBED_DIM", self.embed_dim),
        )
        for name, value in named:
            if value is None:
                missing.append(name)
            elif isinstance(value, str) and _is_placeholder(value):
                placeholder.append(name)

        if missing or placeholder:
            parts = []
            if missing:
                parts.append(f"missing required variables: {', '.join(missing)}")
            if placeholder:
                parts.append(
                    f"placeholder values must be replaced: {', '.join(placeholder)}"
                )
            raise ValueError(
                "APP_MODE=production requires complete Google Cloud configuration ("
                + "; ".join(parts)
                + "). Set them in the service environment or use APP_MODE=demo locally."
            )
        return self


def _is_placeholder(value: str) -> bool:
    return any(marker in value for marker in _PLACEHOLDER_MARKERS)


def _is_real(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != "" and not _is_placeholder(value)
    return True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide settings instance. Use ``Settings(...)`` directly in tests."""
    return Settings()
