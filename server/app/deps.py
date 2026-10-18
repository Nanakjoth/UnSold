"""Shared route dependencies: verified caller + rate limiting."""

from __future__ import annotations

from fastapi import Depends, Request

from .auth import VerifiedUser, get_or_create_user
from .models import AppUser
from .rate_limit import enforce_rate_limit


async def current_verified(request: Request) -> VerifiedUser:
    """Verify the Authorization header into a ``VerifiedUser``."""
    provider = request.app.state.auth_provider
    verified = await provider.verify(request)
    request.state.uid = verified.uid  # enables per-user rate limiting downstream
    return verified


async def current_user(
    request: Request,
    _verified: VerifiedUser = Depends(current_verified),
) -> AppUser:
    """Load (or provision on first visit) the caller's pseudonymous user record."""
    settings = request.app.state.settings
    return get_or_create_user(
        request.app.state.store, _verified.uid, is_synthetic=settings.is_demo
    )


# Apply as `Depends(limit)` alongside `Depends(current_user)`; ordering in the
# signature guarantees the caller is verified (and rate-limited by uid) first.
limit = enforce_rate_limit
