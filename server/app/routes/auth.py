"""Auth routes: pseudonymous session get-or-create, profile update, deletion."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ..deps import current_user, limit
from ..models import AppUser, SessionResponse, SessionUpdate, utc_now_iso
from ..observability import log_event
from ..retention import delete_user_data

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _to_response(user: AppUser) -> SessionResponse:
    return SessionResponse(
        uid=user.uid,
        pseudonym=user.pseudonym,
        language=user.language,
        is_synthetic=user.is_synthetic,
        created_at=user.created_at,
    )


@router.post("/session", response_model=SessionResponse)
async def create_or_get_session(
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> SessionResponse:
    """Get-or-create the caller's pseudonymous app session.

    The uid comes from the verified auth token only — never from the body.
    """
    return _to_response(user)


@router.patch("/session", response_model=SessionResponse)
async def update_session(
    update: SessionUpdate,
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> SessionResponse:
    """Update editable profile fields. Identity fields are not client-settable."""
    store = request.app.state.store
    changes: dict[str, object] = {}
    if update.language is not None and update.language != user.language:
        changes["language"] = update.language

    if changes:
        changes["updated_at"] = utc_now_iso()
        store.update("users", user.uid, changes)
        updated = AppUser.model_validate(store.get("users", user.uid))
        log_event("user_profile_updated", uid=user.uid, fields=sorted(changes))
        return _to_response(updated)
    return _to_response(user)


@router.delete("/session")
async def delete_session(
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> dict[str, object]:
    """Delete every record owned by the caller (spec section 8).

    Returns exactly what was deleted. Records kept for security/quality
    purposes are documented in the privacy doc — this prototype keeps none.
    """
    store = request.app.state.store
    deleted = delete_user_data(store, user.uid)
    return {"deleted": deleted, "total": sum(deleted.values())}
