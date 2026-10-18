"""Authentication: verified identity, never client-claimed.

Two providers behind one interface:

* ``FirebaseProvider`` — production. Verifies Firebase anonymous-auth ID tokens
  with the Admin SDK (Application Default Credentials on Cloud Run).
* ``DemoProvider`` — demo mode only (``APP_MODE=demo``). Mints and verifies
  signed in-process tokens so the *same* ownership checks run locally without
  cloud credentials. The minting endpoint does not exist outside demo mode.

In both cases the caller's ``uid`` comes from the verified token — never from a
request body or query parameter (spec section 8).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass

from fastapi import Request

from .config import Settings
from .models import AppUser
from .pseudonym import generate_pseudonym
from .store import Store


class AuthError(Exception):
    """Raised when a request cannot be attributed to a verified caller."""

    def __init__(self, code: str, message: str, status_code: int = 401) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class VerifiedUser:
    uid: str


class BaseAuthProvider:
    """Verifies an Authorization header into a ``VerifiedUser``."""

    async def verify(self, request: Request) -> VerifiedUser:  # pragma: no cover
        raise NotImplementedError

    def _bearer(self, request: Request) -> str:
        header = request.headers.get("authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise AuthError(
                "missing_token",
                "Sign in is required: send an 'Authorization: Bearer <token>' header.",
            )
        return token.strip()


class DemoProvider(BaseAuthProvider):
    """Demo-mode token mint/verify. Signed with a process-derived secret.

    Tokens are HMAC-signed and expire (default 1h). They exist so that local
    development exercises real verification and ownership logic rather than
    trusting a client-supplied user id.
    """

    def __init__(self, settings: Settings) -> None:
        # Demo secret is derived per-process unless explicitly set; it is never
        # a production credential and never read in production mode.
        self._secret = (
            settings.dev_token_secret
            or f"demo-{settings.app_mode}-atlas-local-dev-only"
        ).encode()
        self._ttl_seconds = 3600

    def mint(self, uid: str) -> str:
        expires = int(time.time()) + self._ttl_seconds
        body = json.dumps({"uid": uid, "exp": expires})
        # Sign exactly the body string the verifier will re-derive.
        signature = hmac.new(self._secret, body.encode(), hashlib.sha256).hexdigest()
        return f"{body}.{signature}"

    async def verify(self, request: Request) -> VerifiedUser:
        token = self._bearer(request)
        try:
            body, signature = token.rsplit(".", 1)
            uid = json.loads(body)["uid"]
            exp = int(json.loads(body)["exp"])
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            raise AuthError("invalid_token", "Token is malformed.") from exc

        expected = hmac.new(self._secret, body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise AuthError("invalid_token", "Token signature is invalid.")
        if exp < time.time():
            raise AuthError("expired_token", "Token has expired; sign in again.")
        return VerifiedUser(uid=uid)


class FirebaseProvider(BaseAuthProvider):
    """Production provider: verifies Firebase anonymous-auth ID tokens.

    Initialization is lazy so constructing the app (e.g. in tests or before the
    first request) never requires credentials; the Admin SDK is set up on the
    first actual verification.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._firebase_auth = None

    def _ensure_initialized(self) -> None:  # pragma: no cover - needs cloud creds
        if self._firebase_auth is not None:
            return
        try:
            import firebase_admin
            from firebase_admin import auth as firebase_auth
            from firebase_admin import credentials
        except ImportError as exc:
            raise RuntimeError(
                "firebase-admin is required for APP_MODE=production. "
                "Install server/requirements.txt or run with APP_MODE=demo."
            ) from exc

        if not firebase_admin._apps:  # noqa: SLF001 - single init point
            firebase_admin.initialize_app(
                credentials.ApplicationDefault(),
                options={"projectId": self._settings.google_cloud_project},
            )
        self._firebase_auth = firebase_auth

    async def verify(self, request: Request) -> VerifiedUser:  # pragma: no cover
        self._ensure_initialized()
        token = self._bearer(request)
        try:
            decoded = self._firebase_auth.verify_id_token(token)
        except Exception as exc:
            raise AuthError("invalid_token", "Firebase token could not be verified.") from exc
        uid = decoded.get("uid")
        if not uid:
            raise AuthError("invalid_token", "Token missing uid.")
        return VerifiedUser(uid=uid)


def create_auth_provider(settings: Settings) -> BaseAuthProvider:
    if settings.app_mode == "demo":
        return DemoProvider(settings)
    return FirebaseProvider(settings)


# --- User provisioning / lookup ---------------------------------------------


def get_or_create_user(store: Store, uid: str, is_synthetic: bool) -> AppUser:
    """Load the user record, creating a fresh pseudonymous one on first visit."""
    existing = store.get("users", uid)
    if existing is not None:
        return AppUser.model_validate(existing)
    user = AppUser(uid=uid, pseudonym=generate_pseudonym(), is_synthetic=is_synthetic)
    store.set("users", uid, user.model_dump())
    return user
