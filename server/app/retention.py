"""Retention and deletion (spec section 8).

`delete_user_data` removes everything tied to one pseudonymous user across all
collections we own today, and reports exactly what was deleted so the route can
tell the user plainly. `purge_expired` implements the documented retention
window for time-stamped records that carry `expires_at` (used by the quality
review queue and, later, by Firestore TTL fields).

Nothing here silently keeps a copy: if a record type must survive deletion for
security or quality reasons, it must be listed in the README and in the API
response.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .observability import log_event
from .store import Store

# Collections where an `owner_uid`/`user_id` field marks user-owned records.
_OWNER_COLLECTIONS = ("users", "saved_interests", "discovery_feedback")

# Advice-core collections. These are not tagged with a generic `user_id`, so
# they need explicit handling: `needs.user_id` and `sessions.mentee_id` are the
# ownership fields, and messages/feedback hang off a session the user owns.
_NEEDS_COLLECTION = "needs"
_SESSIONS_COLLECTION = "sessions"
_MESSAGES_COLLECTION = "session_messages"
_FEEDBACK_COLLECTION = "session_feedback"


def delete_user_data(store: Store, uid: str) -> dict[str, int]:
    """Delete every record owned by `uid`. Returns per-collection delete counts.

    Ownership fields differ by collection (historically `owner_uid`, now
    `user_id` on the per-member collections), so both are checked. Advice-core
    records cascade: a session the user opened takes its messages and feedback
    with it, so nothing orphaned survives to be re-identified later.
    """
    deleted: dict[str, int] = {}

    for collection in _OWNER_COLLECTIONS:
        count = 0
        for field in ("owner_uid", "user_id"):
            count += store.delete_where(collection, field, uid)
        # The user document itself is keyed by uid rather than an owner field.
        if collection == "users":
            before = store.get(collection, uid)
            if before is not None:
                store.delete(collection, uid)
                count += 1
        if count:
            deleted[collection] = count

    # --- Advice core (A1-A3): needs + session cascade ------------------------
    needs = store.delete_where(_NEEDS_COLLECTION, "user_id", uid)
    if needs:
        deleted[_NEEDS_COLLECTION] = needs

    # Collect the user's session ids *before* deleting the sessions, so their
    # messages and feedback can be removed too.
    session_ids = [
        str(doc.get("id"))
        for doc in store.list(_SESSIONS_COLLECTION, limit=5000)
        if doc.get("mentee_id") == uid and doc.get("id")
    ]

    sessions = store.delete_where(_SESSIONS_COLLECTION, "mentee_id", uid)
    if sessions:
        deleted[_SESSIONS_COLLECTION] = sessions

    messages = 0
    feedback = 0
    for sid in session_ids:
        messages += store.delete_where(_MESSAGES_COLLECTION, "session_id", sid)
        feedback += store.delete_where(_FEEDBACK_COLLECTION, "session_id", sid)
    if messages:
        deleted[_MESSAGES_COLLECTION] = messages
    if feedback:
        deleted[_FEEDBACK_COLLECTION] = feedback

    log_event("user_data_deleted", uid=uid, collections=list(deleted), total=sum(deleted.values()))
    return deleted


def purge_expired(store: Store, collection: str, *, now: datetime | None = None) -> int:
    """Delete docs in `collection` whose `expires_at` is in the past."""
    current = now or datetime.now(timezone.utc)
    deleted = 0
    for doc in store.list(collection, limit=5000):
        raw = doc.get("expires_at")
        if raw is None:
            continue
        try:
            expires = datetime.fromisoformat(str(raw))
        except ValueError:
            continue
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires <= current:
            doc_id = doc.get("id") or doc.get("uid")
            if doc_id:
                store.delete(collection, doc_id)
                deleted += 1
    if deleted:
        log_event("retention_purge", collection=collection, deleted=deleted)
    return deleted


def expiry_from(days: int) -> str:
    """ISO timestamp `days` from now — for stamping `expires_at` on new records."""
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat(
        timespec="seconds"
    )
