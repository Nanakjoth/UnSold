"""Configured Gemini access with an honest, deterministic fallback.

One principle throughout: the app must never pretend a model ran when it did
not (spec section 15). Every function here returns, alongside its result, a
``source`` of either ``"gemini"`` or ``"fallback"`` so callers can label output
and log provenance truthfully.

The live path uses the `google-genai` SDK against the Google Cloud project
configured in the environment. It is imported lazily, so demo mode and tests
run with no cloud credentials at all.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from .config import Settings
from .observability import log_event

T = TypeVar("T", bound=BaseModel)

_PROMPT_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def load_prompt(name: str) -> str:
    """Load a versioned prompt template from app/prompts/."""
    with open(os.path.join(_PROMPT_DIR, f"{name}.md"), encoding="utf-8") as handle:
        return handle.read()


@dataclass
class GenerationResult:
    """Result of a structured generation call, with honest provenance."""

    data: Any | None
    source: str  # "gemini" | "fallback"
    degraded: bool = False
    error_category: str | None = None


class GeminiClient:
    """Thin wrapper over the Google Gen AI SDK, configured by environment.

    Nothing is hardcoded: project, location, and model IDs all come from
    `Settings`. Malformed output is retried at most once, then handed back as a
    degraded result for the caller's deterministic fallback (spec section 10).
    """

    _T = None  # populated lazily to hold the genai TypeDict

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = None

    def _ensure_client(self):  # pragma: no cover - needs cloud credentials
        if self._client is not None:
            return self._client
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "google-genai is required for live AI. Install requirements or run demo mode."
            ) from exc
        # vertexai=True is required: without it the SDK treats project/location
        # as an API-key (Google AI) request and raises ValueError. "global" as
        # a location is supported natively (routes to aiplatform.googleapis.com).
        self._client = genai.Client(
            vertexai=True,
            project=self._settings.google_cloud_project,
            location=self._settings.google_cloud_location,
        )
        return self._client

    def structured(
        self, prompt_name: str, prompt_vars: dict[str, str], schema: type[T]
    ) -> GenerationResult:
        """Generate and validate JSON against `schema`. Never raises on failure."""
        model = self._settings.gemini_model
        template = load_prompt(prompt_name)
        prompt = template.format(**prompt_vars)

        for attempt in range(2):  # at most one retry (spec section 10.7)
            try:
                client = self._ensure_client()
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "temperature": 0.2,
                        "max_output_tokens": 1024,
                    },
                )
                payload = json.loads(response.text or "{}")
                validated = schema.model_validate(payload)
                log_event(
                    "gemini_call",
                    kind=prompt_name,
                    model=model,
                    attempt=attempt,
                    status="ok",
                )
                return GenerationResult(data=validated, source="gemini")
            except ValidationError as exc:
                last_error = "invalid_schema"
                log_event(
                    "gemini_call",
                    kind=prompt_name,
                    model=model,
                    attempt=attempt,
                    status="invalid_schema",
                )
            except Exception as exc:  # noqa: BLE001 - categorise, never re-raise
                last_error = type(exc).__name__
                log_event(
                    "gemini_call",
                    kind=prompt_name,
                    model=model,
                    attempt=attempt,
                    status="error",
                    error_type=type(exc).__name__,
                )
        return GenerationResult(
            data=None, source="fallback", degraded=True, error_category=last_error
        )

    def generate(
        self, prompt_name: str, prompt_vars: dict[str, str]
    ) -> GenerationResult:
        """Generate plain text for `prompt_name`. Never raises on failure.

        Returns ``GenerationResult(data=<text>, source="gemini")`` on success,
        or a ``source="fallback"`` result the caller can substitute its own
        deterministic template for. Used by the mentor simulator (section 10.12).
        """
        model = self._settings.gemini_model
        template = load_prompt(prompt_name)
        prompt = template.format(**prompt_vars)
        try:
            client = self._ensure_client()
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={"temperature": 0.7, "max_output_tokens": 512},
            )
            text = (response.text or "").strip()
            log_event(
                "gemini_call", kind=prompt_name, model=model, status="ok",
            )
            if not text:
                return GenerationResult(
                    data=None, source="fallback", degraded=True,
                    error_category="empty",
                )
            return GenerationResult(data=text, source="gemini")
        except Exception as exc:  # noqa: BLE001 - categorise, never re-raise
            log_event(
                "gemini_call", kind=prompt_name, model=model, status="error",
                error_type=type(exc).__name__,
            )
            return GenerationResult(
                data=None, source="fallback", degraded=True,
                error_category=type(exc).__name__,
            )

    def embed(self, texts: list[str]) -> list[list[float]] | None:
        """Embed a batch of texts. Returns None when unavailable."""
        model = self._settings.embed_model
        try:
            client = self._ensure_client()
            result = client.models.embed_contents(model=model, contents=texts)
            vectors = [list(v) for v in result.embeddings]
            if vectors and self._settings.embed_dim:
                # Dimension guard: stored vectors and the index must agree.
                if len(vectors[0]) != self._settings.embed_dim:
                    log_event(
                        "embed_dim_mismatch",
                        model=model,
                        got=len(vectors[0]),
                        expected=self._settings.embed_dim,
                    )
                    return None
            log_event("gemini_embed", model=model, count=len(texts), status="ok")
            return vectors
        except Exception as exc:  # noqa: BLE001
            log_event(
                "gemini_embed", model=model, count=len(texts), status="error",
                error_type=type(exc).__name__,
            )
            return None


def create_gemini(settings: Settings) -> GeminiClient | None:
    """Return a live client only when the environment is really configured."""
    if settings.cloud_configured:
        return GeminiClient(settings)
    return None
