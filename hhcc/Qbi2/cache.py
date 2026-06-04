"""Cache persistente QBI2 sobre MySQL.

La cache expira por clave y de forma lazy: no hay renovacion masiva cuando
vence un TTL. Cada busqueda decide si puede usar el valor fresco, si devuelve
stale, o si toma un lease para refrescar solo esa clave.
"""

from __future__ import annotations

import copy
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone

from .models import Qbi2CacheEntry


@dataclass(frozen=True)
class CacheResult:
    hit: bool
    value: Any | None = None
    stale: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CacheStats:
    keys: int
    fresh: int
    stale: int
    dead: int
    locked: int


@dataclass(frozen=True)
class RefreshLease:
    acquired: bool
    token: str | None = None


class MySQLCache:
    """Backend unico para desarrollo, testing y produccion."""

    def get(self, key: str, *, allow_stale: bool = False) -> CacheResult:
        now = timezone.now()
        entry = Qbi2CacheEntry.objects.filter(key_hash=hash_key(key)).first()
        if entry is None:
            return CacheResult(hit=False)

        metadata = self._metadata_for(entry)
        if now <= entry.fresh_until:
            return CacheResult(
                hit=True,
                value=copy.deepcopy(entry.value),
                stale=False,
                metadata=metadata,
            )

        if allow_stale and now <= entry.stale_until:
            return CacheResult(
                hit=True,
                value=copy.deepcopy(entry.value),
                stale=True,
                metadata=metadata,
            )

        return CacheResult(hit=False, metadata=metadata)

    def set(
        self,
        key: str,
        value: Any,
        fresh_ttl: timedelta,
        *,
        stale_ttl: timedelta,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        fresh_ttl = _validate_positive_ttl(fresh_ttl, "fresh_ttl")
        stale_ttl = _validate_positive_ttl(stale_ttl, "stale_ttl")
        now = timezone.now()
        metadata = copy.deepcopy(metadata or {})
        fields = {
            **self._entry_fields_from_metadata(key, metadata),
            "cache_key": key,
            "value": copy.deepcopy(value),
            "metadata": metadata,
            "fetched_at": now,
            "fresh_until": now + fresh_ttl,
            "stale_until": now + fresh_ttl + stale_ttl,
            "refresh_locked_until": None,
            "refresh_token": None,
            "refresh_started_at": None,
            "last_refresh_error": None,
        }
        Qbi2CacheEntry.objects.update_or_create(
            key_hash=hash_key(key),
            defaults=fields,
        )

    def delete(self, key: str) -> bool:
        deleted, _ = Qbi2CacheEntry.objects.filter(key_hash=hash_key(key)).delete()
        return deleted > 0

    def clear(self, *, namespace: str | None = None) -> int:
        qs = Qbi2CacheEntry.objects.all()
        if namespace is not None:
            qs = qs.filter(namespace=namespace)
        deleted, _ = qs.delete()
        return deleted

    def stats(self, *, namespace: str | None = None) -> CacheStats:
        now = timezone.now()
        qs = Qbi2CacheEntry.objects.all()
        if namespace is not None:
            qs = qs.filter(namespace=namespace)
        return CacheStats(
            keys=qs.count(),
            fresh=qs.filter(fresh_until__gte=now).count(),
            stale=qs.filter(fresh_until__lt=now, stale_until__gte=now).count(),
            dead=qs.filter(stale_until__lt=now).count(),
            locked=qs.filter(refresh_locked_until__gte=now).count(),
        )

    def try_acquire_refresh_lease(
        self,
        key: str,
        *,
        lease_ttl: timedelta = timedelta(seconds=45),
    ) -> RefreshLease:
        lease_ttl = _validate_positive_ttl(lease_ttl, "lease_ttl")
        now = timezone.now()
        token = uuid.uuid4().hex
        with transaction.atomic():
            entry = (
                Qbi2CacheEntry.objects.select_for_update()
                .filter(key_hash=hash_key(key))
                .first()
            )
            if entry is None:
                return RefreshLease(acquired=True, token=token)
            if entry.refresh_locked_until and entry.refresh_locked_until > now:
                return RefreshLease(acquired=False)
            entry.refresh_token = token
            entry.refresh_started_at = now
            entry.refresh_locked_until = now + lease_ttl
            entry.save(
                update_fields=[
                    "refresh_token",
                    "refresh_started_at",
                    "refresh_locked_until",
                    "updated_at",
                ]
            )
        return RefreshLease(acquired=True, token=token)

    def release_refresh_lease(
        self,
        key: str,
        token: str | None,
        *,
        error: str | None = None,
    ) -> None:
        if not token:
            return
        updates = {
            "refresh_locked_until": None,
            "refresh_token": None,
            "refresh_started_at": None,
            "last_refresh_error": error,
        }
        Qbi2CacheEntry.objects.filter(key_hash=hash_key(key), refresh_token=token).update(
            **updates
        )

    @staticmethod
    def _metadata_for(entry: Qbi2CacheEntry) -> dict[str, Any]:
        metadata = copy.deepcopy(entry.metadata or {})
        metadata.setdefault("key_hash", entry.key_hash)
        metadata.setdefault("fetched_at", entry.fetched_at.isoformat())
        metadata.setdefault("fresh_until", entry.fresh_until.isoformat())
        metadata.setdefault("stale_until", entry.stale_until.isoformat())
        metadata.setdefault("status", entry.status)
        if entry.last_refresh_error:
            metadata.setdefault("last_refresh_error", entry.last_refresh_error)
        return metadata

    @staticmethod
    def _entry_fields_from_metadata(key: str, metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            "namespace": str(metadata.get("namespace") or "vademecum"),
            "provider": str(metadata.get("provider") or "qbi2"),
            "endpoint": str(metadata.get("provider_endpoint") or metadata.get("endpoint") or ""),
            "cliente_app_id": str(metadata.get("cliente_app_id") or ""),
            "normalized_query": str(metadata.get("normalized_query") or "")[:255],
            "page": int(metadata.get("page") or 1),
            "params_hash": str(metadata.get("params_hash") or "")[:64],
            "schema_version": int(metadata.get("schema_version") or 1),
            "status": str(metadata.get("status") or "ok"),
        }


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _validate_positive_ttl(value: timedelta, name: str) -> timedelta:
    if not isinstance(value, timedelta):
        raise TypeError(f"{name} debe ser datetime.timedelta")
    if value <= timedelta(0):
        raise ValueError(f"{name} debe ser mayor que cero")
    return value

