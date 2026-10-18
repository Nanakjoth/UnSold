"""Repository layer over Firestore with a deterministic in-memory fallback.

Demo mode and tests use ``InMemoryStore`` so the whole product runs without
cloud credentials, while the same interface backs the production
``FirestoreStore``. Application code never touches a Firestore client directly
— it always goes through ``Store`` — so authorization and serialization stay
in one place.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Protocol

from .config import Settings
from .observability import log_event


class Store(Protocol):
    def get(self, collection: str, doc_id: str) -> dict[str, Any] | None: ...

    def set(self, collection: str, doc_id: str, data: dict[str, Any]) -> None: ...

    def update(self, collection: str, doc_id: str, data: dict[str, Any]) -> None: ...

    def transact(
        self,
        collection: str,
        doc_id: str,
        mutate: Callable[[dict[str, Any]], dict[str, Any] | None],
    ) -> dict[str, Any] | None:
        """Atomically read-modify-write one document.

        `mutate` receives a copy of the current document and returns the new
        document to persist, or ``None`` to abort without writing. Returns the
        persisted document, ``None`` if the document does not exist, or
        ``None`` when aborted (callers distinguish via the pre-state).

        Used by operations where a lost update would corrupt state — most
        critically the mutual-reveal consent machine (spec section 8:
        "updates transactionally so simultaneous clicks cannot create
        inconsistent consent state").
        """
        ...

    def delete(self, collection: str, doc_id: str) -> None: ...

    def list(self, collection: str, limit: int = 100) -> list[dict[str, Any]]: ...

    def delete_where(
        self, collection: str, field: str, value: Any, *, limit: int = 1000
    ) -> int: ...

    def delete_collection(self, collection: str) -> int: ...


class InMemoryStore:
    """Dict-backed store. Deterministic, thread-safe, process-local.

    Used for APP_MODE=demo and all tests. Data is intentionally volatile —
    restarting the server clears it, which suits a synthetic-data prototype.
    """

    def __init__(self) -> None:
        self._data: dict[str, dict[str, dict[str, Any]]] = {}
        self._lock = threading.RLock()

    def get(self, collection: str, doc_id: str) -> dict[str, Any] | None:
        with self._lock:
            doc = self._data.get(collection, {}).get(doc_id)
            return dict(doc) if doc is not None else None

    def set(self, collection: str, doc_id: str, data: dict[str, Any]) -> None:
        with self._lock:
            self._data.setdefault(collection, {})[doc_id] = dict(data)

    def update(self, collection: str, doc_id: str, data: dict[str, Any]) -> None:
        with self._lock:
            existing = self._data.get(collection, {}).get(doc_id)
            if existing is None:
                raise KeyError(f"{collection}/{doc_id} does not exist")
            existing.update(data)

    def transact(
        self,
        collection: str,
        doc_id: str,
        mutate: Callable[[dict[str, Any]], dict[str, Any] | None],
    ) -> dict[str, Any] | None:
        # The whole read-modify-write runs under the store lock, so concurrent
        # consent clicks serialize and the second caller sees the first write.
        with self._lock:
            existing = self._data.get(collection, {}).get(doc_id)
            if existing is None:
                return None
            updated = mutate(dict(existing))
            if updated is None:
                return None
            self._data[collection][doc_id] = dict(updated)
            return dict(updated)

    def delete(self, collection: str, doc_id: str) -> None:
        with self._lock:
            self._data.get(collection, {}).pop(doc_id, None)

    def list(self, collection: str, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            docs = list(self._data.get(collection, {}).values())
        return [dict(doc) for doc in docs[:limit]]

    def delete_where(
        self, collection: str, field: str, value: Any, *, limit: int = 1000
    ) -> int:
        with self._lock:
            bucket = self._data.get(collection, {})
            doomed = [k for k, v in bucket.items() if v.get(field) == value][:limit]
            for key in doomed:
                del bucket[key]
        return len(doomed)

    def delete_collection(self, collection: str) -> int:
        with self._lock:
            count = len(self._data.get(collection, {}))
            self._data.pop(collection, None)
        return count


class FirestoreStore:
    """Firestore-backed store. Requires ADC and an existing database.

    The client is created lazily on first use, so constructing the store (or the
    app) never requires credentials. Server SDK access uses IAM/ADC — no client
    rules substitute for the authorization checks performed in the route layer
    (spec section 8).
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = None

    def _ensure_client(self):  # pragma: no cover - needs cloud creds
        if self._client is not None:
            return self._client
        try:
            from google.cloud import firestore
        except ImportError as exc:
            raise RuntimeError(
                "google-cloud-firestore is required outside demo mode."
            ) from exc
        self._client = firestore.Client(
            project=self._settings.google_cloud_project,
            database=self._settings.firestore_db,
        )
        return self._client

    def _col(self, collection: str):  # pragma: no cover - exercised in cloud only
        return self._ensure_client().collection(collection)

    def get(self, collection: str, doc_id: str) -> dict[str, Any] | None:  # pragma: no cover
        snapshot = self._col(collection).document(doc_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        data["id"] = snapshot.id
        return data

    def set(self, collection: str, doc_id: str, data: dict[str, Any]) -> None:  # pragma: no cover
        self._col(collection).document(doc_id).set(data)

    def update(self, collection: str, doc_id: str, data: dict[str, Any]) -> None:  # pragma: no cover
        self._col(collection).document(doc_id).update(data)

    def transact(
        self,
        collection: str,
        doc_id: str,
        mutate: Callable[[dict[str, Any]], dict[str, Any] | None],
    ) -> dict[str, Any] | None:  # pragma: no cover - exercised in cloud only
        from google.cloud import firestore

        client = self._ensure_client()
        ref = client.collection(collection).document(doc_id)
        transaction = client.transaction()

        @firestore.transactional
        def _step(transaction_, reference):
            snapshot = transaction_.get(reference)
            if not snapshot.exists:
                return None
            data = snapshot.to_dict() or {}
            data["id"] = snapshot.id
            updated = mutate(data)
            if updated is None:
                return None
            stored = {k: v for k, v in updated.items() if k != "id"}
            transaction_.set(reference, stored)
            return updated

        return _step(transaction, ref)

    def delete(self, collection: str, doc_id: str) -> None:  # pragma: no cover
        self._col(collection).document(doc_id).delete()

    def list(self, collection: str, limit: int = 100) -> list[dict[str, Any]]:  # pragma: no cover
        docs: list[dict[str, Any]] = []
        for snapshot in self._col(collection).limit(limit).stream():
            data = snapshot.to_dict() or {}
            data["id"] = snapshot.id
            docs.append(data)
        return docs

    def delete_where(
        self, collection: str, field: str, value: Any, *, limit: int = 1000
    ) -> int:  # pragma: no cover
        from google.cloud.firestore_v1.base_query import FieldFilter

        query = (
            self._col(collection)
            .where(filter=FieldFilter(field, "==", value))
            .limit(limit)
            .stream()
        )
        batch = self._ensure_client().batch()
        count = 0
        for snapshot in query:
            batch.delete(snapshot.reference)
            count += 1
        if count:
            batch.commit()
        return count

    def delete_collection(self, collection: str) -> int:  # pragma: no cover
        docs = list(self._col(collection).limit(500).stream())
        batch = self._ensure_client().batch()
        for snapshot in docs:
            batch.delete(snapshot.reference)
        if docs:
            batch.commit()
        return len(docs)


def create_store(settings: Settings) -> Store:
    """In-memory for demo; Firestore when a real cloud configuration exists."""
    if settings.app_mode == "demo" or not settings.cloud_configured:
        if settings.app_mode != "demo":
            log_event("store_fallback", reason="cloud_not_configured", mode="demo")
        return InMemoryStore()
    return FirestoreStore(settings)
