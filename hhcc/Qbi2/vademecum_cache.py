"""Cache persistente para busquedas de vademecum QBI2 / Innovamed."""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from .cache import MySQLCache


@dataclass(frozen=True)
class VademecumCachePolicy:
    fresh_ttl: timedelta = timedelta(days=15)
    stale_ttl: timedelta = timedelta(days=75)
    lease_ttl: timedelta = timedelta(seconds=45)
    min_query_length: int = 2
    schema_version: int = 1
    refresh_stale_synchronously: bool = True
    critical_fields: tuple[str, ...] = (
        "regNo",
        "nombreProducto",
        "nombreDroga",
        "presentacion",
        "potencia",
        "descripcionPotencia",
        "formaFarmaceutica",
        "viaAdministracion",
        "codigoTipoExpendio",
        "descripcionTipoExpendio",
        "requiereAprobacion",
        "psicofarmaco",
        "estupefaciente",
        "ventaControlada",
        "requiereDuplicado",
        "cobertura",
    )


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    status: str
    selected_snapshot: dict[str, Any]
    live_item: dict[str, Any] | None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class CachedVademecumService:
    """Cachea solo busqueda/autocomplete, nunca emision de recetas."""

    def __init__(
        self,
        live_service: Any,
        *,
        cache: MySQLCache | None = None,
        policy: VademecumCachePolicy | None = None,
        provider: str = "qbi2",
        cliente_app_id: str | int | None = None,
        base_url: str | None = None,
        endpoint_path: str = "/apirecipe/GetMedicamento",
        endpoint_name: str = "GetMedicamento",
        search_method: str = "buscar",
        validate_by_regno_method: str | None = None,
    ) -> None:
        self.live_service = live_service
        self.cache = cache or MySQLCache()
        self.policy = policy or VademecumCachePolicy()
        self.provider = provider
        self.cliente_app_id = "" if cliente_app_id is None else str(cliente_app_id)
        self.base_url = base_url or ""
        self.endpoint_path = endpoint_path
        self.endpoint_name = endpoint_name
        self.search_method = search_method
        self.validate_by_regno_method = validate_by_regno_method

    def buscar(
        self,
        query: str,
        page: int = 1,
        extra_params: dict[str, Any] | None = None,
        *,
        allow_stale: bool = True,
        include_cache_metadata: bool = False,
    ) -> Any:
        normalized_query = normalize_query(query)
        if len(normalized_query) < self.policy.min_query_length:
            return self._with_cache_metadata(
                [],
                include_cache_metadata,
                {"hit": False, "stale": False, "status": "too_short"},
            )

        key_parts = self.key_parts(query, page=page, extra_params=extra_params)
        key = key_parts["cache_key"]
        cached = self.cache.get(key, allow_stale=allow_stale)
        if cached.hit and not cached.stale:
            return self._with_cache_metadata(
                cached.value,
                include_cache_metadata,
                {"hit": True, "stale": False, "key": key, **cached.metadata},
            )

        if cached.hit and cached.stale:
            return self._handle_stale_hit(
                key,
                key_parts,
                normalized_query,
                page,
                extra_params or {},
                cached.value,
                cached.metadata,
                include_cache_metadata,
            )

        return self._refresh_from_qbi2(
            key,
            key_parts,
            normalized_query,
            page,
            extra_params or {},
            include_cache_metadata=include_cache_metadata,
            was_stale=False,
        )

    def validar_medicamento_seleccionado(
        self,
        snapshot: dict[str, Any],
    ) -> ValidationResult:
        selected_snapshot = copy.deepcopy(snapshot)
        reg_no = extract_field(selected_snapshot, "regNo")
        if not reg_no:
            return ValidationResult(
                valid=False,
                status="invalid_snapshot",
                selected_snapshot=selected_snapshot,
                live_item=None,
                errors=["El snapshot seleccionado no tiene regNo."],
            )

        try:
            live_items = self._fetch_live_candidates_for_validation(selected_snapshot, str(reg_no))
        except Exception as exc:
            return ValidationResult(
                valid=False,
                status="provider_error",
                selected_snapshot=selected_snapshot,
                live_item=None,
                errors=[f"No se pudo revalidar contra QBI2 vivo: {exc}"],
            )

        matches = [
            item for item in live_items if str(extract_field(item, "regNo") or "") == str(reg_no)
        ]
        if not matches:
            return ValidationResult(
                valid=False,
                status="not_found",
                selected_snapshot=selected_snapshot,
                live_item=None,
                errors=["QBI2 vivo no encontro el regNo seleccionado."],
            )
        if len(matches) > 1:
            return ValidationResult(
                valid=False,
                status="ambiguous",
                selected_snapshot=selected_snapshot,
                live_item=None,
                errors=["QBI2 vivo devolvio mas de un candidato para el mismo regNo."],
            )

        live_item = copy.deepcopy(matches[0])
        warnings = compare_critical_fields(
            selected_snapshot,
            live_item,
            self.policy.critical_fields,
        )
        if warnings:
            return ValidationResult(
                valid=False,
                status="changed",
                selected_snapshot=selected_snapshot,
                live_item=live_item,
                warnings=warnings,
                errors=["El medicamento seleccionado cambio y requiere nueva seleccion."],
            )

        return ValidationResult(
            valid=True,
            status="valid",
            selected_snapshot=selected_snapshot,
            live_item=live_item,
        )

    def key_for_search(
        self,
        query: str,
        *,
        page: int = 1,
        extra_params: dict[str, Any] | None = None,
    ) -> str:
        return self.key_parts(query, page=page, extra_params=extra_params)["cache_key"]

    def key_parts(
        self,
        query: str,
        *,
        page: int = 1,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_query = normalize_query(query)
        normalized_params = normalize_params(extra_params or {})
        params_json = json.dumps(
            normalized_params,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        params_hash = hashlib.sha256(params_json.encode("utf-8")).hexdigest()
        base_hash = hashlib.sha256(self.base_url.encode("utf-8")).hexdigest()[:12]
        cache_key = ":".join(
            [
                self.provider,
                "vademecum",
                f"v{self.policy.schema_version}",
                f"clienteAppId={self.cliente_app_id}",
                f"base={base_hash}",
                f"path={self.endpoint_path}",
                f"q={normalized_query}",
                f"page={int(page)}",
                f"params={params_hash[:16]}",
            ]
        )
        return {
            "cache_key": cache_key,
            "normalized_query": normalized_query,
            "params_hash": params_hash,
            "page": int(page),
        }

    def _handle_stale_hit(
        self,
        key: str,
        key_parts: dict[str, Any],
        normalized_query: str,
        page: int,
        extra_params: dict[str, Any],
        stale_value: Any,
        stale_metadata: dict[str, Any],
        include_cache_metadata: bool,
    ) -> Any:
        lease = self.cache.try_acquire_refresh_lease(key, lease_ttl=self.policy.lease_ttl)
        if not lease.acquired:
            return self._with_cache_metadata(
                stale_value,
                include_cache_metadata,
                {"hit": True, "stale": True, "refresh": "locked", "key": key, **stale_metadata},
            )

        if not self.policy.refresh_stale_synchronously:
            self.cache.release_refresh_lease(key, lease.token)
            return self._with_cache_metadata(
                stale_value,
                include_cache_metadata,
                {"hit": True, "stale": True, "refresh": "deferred", "key": key, **stale_metadata},
            )

        try:
            return self._refresh_from_qbi2(
                key,
                key_parts,
                normalized_query,
                page,
                extra_params,
                include_cache_metadata=include_cache_metadata,
                was_stale=True,
                lease_token=lease.token,
            )
        except Exception as exc:
            self.cache.release_refresh_lease(key, lease.token, error=str(exc))
            return self._with_cache_metadata(
                stale_value,
                include_cache_metadata,
                {
                    "hit": True,
                    "stale": True,
                    "refresh": "provider_error",
                    "key": key,
                    **stale_metadata,
                },
            )

    def _refresh_from_qbi2(
        self,
        key: str,
        key_parts: dict[str, Any],
        normalized_query: str,
        page: int,
        extra_params: dict[str, Any],
        *,
        include_cache_metadata: bool,
        was_stale: bool,
        lease_token: str | None = None,
    ) -> Any:
        try:
            live_value = self._call_search(normalized_query, page, extra_params)
            status = infer_response_status(live_value)
            metadata = self._cache_metadata(key, key_parts, status)
            self.cache.set(
                key,
                live_value,
                self.policy.fresh_ttl,
                stale_ttl=self.policy.stale_ttl,
                metadata=metadata,
            )
        except Exception:
            raise

        return self._with_cache_metadata(
            live_value,
            include_cache_metadata,
            {"hit": False, "stale": False, "refreshed_from_stale": was_stale, **metadata},
        )

    def _cache_metadata(
        self,
        key: str,
        key_parts: dict[str, Any],
        status: str,
    ) -> dict[str, Any]:
        return {
            "key": key,
            "namespace": "vademecum",
            "provider": self.provider,
            "provider_endpoint": self.endpoint_name,
            "cliente_app_id": self.cliente_app_id,
            "normalized_query": key_parts["normalized_query"],
            "page": key_parts["page"],
            "params_hash": key_parts["params_hash"],
            "status": status,
            "schema_version": self.policy.schema_version,
            "fresh_ttl_seconds": int(self.policy.fresh_ttl.total_seconds()),
            "stale_ttl_seconds": int(self.policy.stale_ttl.total_seconds()),
        }

    def _call_search(
        self,
        normalized_query: str,
        page: int,
        extra_params: dict[str, Any],
    ) -> Any:
        method = getattr(self.live_service, self.search_method)
        return call_with_supported_kwargs(
            method,
            normalized_query,
            page=page,
            extra_params=extra_params,
            **extra_params,
        )

    def _fetch_live_candidates_for_validation(
        self,
        snapshot: dict[str, Any],
        reg_no: str,
    ) -> list[dict[str, Any]]:
        method = self._find_validation_method()
        if method is not None:
            return extract_items(call_with_supported_kwargs(method, reg_no, regNo=reg_no))

        query = build_validation_query(snapshot)
        if not query:
            return []
        response = self._call_search(normalize_query(query), 1, {})
        return extract_items(response)

    def _find_validation_method(self) -> Any | None:
        candidate_names = [
            self.validate_by_regno_method,
            "obtener_por_regno",
            "get_by_regno",
            "validar_regno",
            "buscar_por_regno",
        ]
        for name in candidate_names:
            if name and hasattr(self.live_service, name):
                return getattr(self.live_service, name)
        return None

    @staticmethod
    def _with_cache_metadata(
        value: Any,
        include_cache_metadata: bool,
        metadata: dict[str, Any],
    ) -> Any:
        if not include_cache_metadata:
            return value
        return {"data": value, "cache": metadata}


def normalize_query(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_params(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): normalize_params(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [normalize_params(item) for item in value]
    return value


def infer_response_status(value: Any) -> str:
    items = extract_items(value)
    return "empty" if len(items) == 0 else "ok"


def extract_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if not isinstance(value, dict):
        return []
    if extract_field(value, "regNo"):
        return [value]
    for key in ("items", "results", "resultados", "medicamentos", "data", "result"):
        child = value.get(key)
        if isinstance(child, list):
            return [item for item in child if isinstance(item, dict)]
        if isinstance(child, dict):
            nested = extract_items(child)
            if nested:
                return nested
    return []


def extract_field(item: dict[str, Any], field_name: str) -> Any:
    if field_name in item:
        return item[field_name]
    target = field_name.lower()
    for key, value in item.items():
        if str(key).lower() == target:
            return value
    return None


def build_validation_query(snapshot: dict[str, Any]) -> str:
    for field_name in ("display", "nombreProducto", "nombreDroga"):
        value = extract_field(snapshot, field_name)
        if value:
            return str(value)
    return ""


def compare_critical_fields(
    selected: dict[str, Any],
    live: dict[str, Any],
    critical_fields: tuple[str, ...],
) -> list[str]:
    warnings: list[str] = []
    for field_name in critical_fields:
        selected_value = extract_field(selected, field_name)
        live_value = extract_field(live, field_name)
        if selected_value is None or live_value is None:
            continue
        if canonical_value(selected_value) != canonical_value(live_value):
            warnings.append(
                f"{field_name} cambio: seleccionado={selected_value!r}, vivo={live_value!r}"
            )
    return warnings


def canonical_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return normalize_query(value)


def call_with_supported_kwargs(method: Any, *args: Any, **kwargs: Any) -> Any:
    signature = inspect.signature(method)
    parameters = signature.parameters
    accepts_var_kwargs = any(
        param.kind == inspect.Parameter.VAR_KEYWORD for param in parameters.values()
    )
    if accepts_var_kwargs:
        return method(*args, **kwargs)

    supported_kwargs = {key: value for key, value in kwargs.items() if key in parameters}
    return method(*args, **supported_kwargs)
