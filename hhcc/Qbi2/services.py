import unicodedata
from typing import Any
from urllib.parse import quote

from django.conf import settings
from django.core.exceptions import ValidationError

from .client import Qbi2Client


COMMON_LIST_KEYS = ("medicamentos", "items", "data", "result", "results", "medicines")
DIAGNOSTICO_LIST_KEYS = ("diagnosticos", "items", "data", "result", "results")


class VademecumService:
    def __init__(self, client: Qbi2Client | None = None):
        self.client = client or Qbi2Client()

    def buscar(
        self,
        query: str,
        page: int = 1,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        query = (query or "").strip()
        min_length = int(getattr(settings, "QBI2_VADEMECUM_MIN_QUERY_LENGTH", 2))
        if len(query) < min_length:
            raise ValidationError(f"La busqueda debe tener al menos {min_length} caracteres.")
        if page < 1:
            raise ValidationError("La pagina debe ser mayor o igual a 1.")

        params = self._build_search_params(page, extra_params or {})
        path = self._build_search_path(query)
        raw_response = self.client.get(path, params=params)
        items = normalize_vademecum_response(raw_response)

        return {
            "query": query,
            "page": page,
            "items": [normalize_medicamento(item) for item in items],
            "page_info": extract_page_info(raw_response),
            "raw": raw_response,
        }

    def buscar_relevante(
        self,
        query: str,
        *,
        start_page: int = 1,
        extra_params: dict[str, Any] | None = None,
        max_pages: int | None = None,
        max_results: int | None = None,
    ) -> dict[str, Any]:
        """Busca varias páginas y ordena producto antes que droga."""

        if start_page < 1:
            raise ValidationError("La pagina inicial debe ser mayor o igual a 1.")
        max_pages = max_pages or int(
            getattr(settings, "QBI2_VADEMECUM_RELEVANCE_MAX_PAGES", 10)
        )
        max_pages = max(1, min(max_pages, 20))
        if max_results is not None:
            max_results = max(1, min(max_results, 1000))

        first = self.buscar(query, page=start_page, extra_params=extra_params)
        provider_pages = _provider_page_count(first.get("page_info"), default=start_page)
        end_page = min(provider_pages, start_page + max_pages - 1)
        page_results = [first]
        for page in range(start_page + 1, end_page + 1):
            page_results.append(self.buscar(query, page=page, extra_params=extra_params))

        combined = []
        seen = set()
        for page_result in page_results:
            for item in page_result.get("items", []):
                if not isinstance(item, dict):
                    continue
                key = (item.get("regNo") or "").strip() or (
                    item.get("nombreProducto"),
                    item.get("nombreDroga"),
                    item.get("presentacion"),
                )
                if key in seen:
                    continue
                seen.add(key)
                combined.append(item)

        ranked = sorted(combined, key=lambda item: _medication_relevance(item, query))
        returned = ranked if max_results is None else ranked[:max_results]
        return {
            "query": first["query"],
            "page": start_page,
            "items": returned,
            "page_info": {
                "numeroPagina": start_page,
                "cantidadPaginas": provider_pages,
                "paginasConsultadas": list(range(start_page, end_page + 1)),
                "tieneMasResultados": end_page < provider_pages,
                "proximaPagina": end_page + 1 if end_page < provider_pages else None,
                "resultadosRevisados": len(combined),
                "resultadosDevueltos": len(returned),
                "resultadosOmitidos": len(ranked) - len(returned),
            },
        }

    def _build_search_path(self, query: str) -> str:
        path_template = getattr(settings, "QBI2_VADEMECUM_PATH", "/apirecipe/GetMedicamento/{search}")
        encoded_query = quote(query, safe="")
        if "{search}" in path_template:
            return path_template.replace("{search}", encoded_query)
        return f"{path_template.rstrip('/')}/{encoded_query}"

    def _build_search_params(self, page: int, extra_params: dict[str, Any]) -> dict[str, Any]:
        page_param = getattr(settings, "QBI2_VADEMECUM_PAGE_PARAM", "numeroPagina")
        client_id_param = getattr(settings, "QBI2_CLIENT_APP_ID_PARAM", "clienteAppId")
        include_client_id = getattr(settings, "QBI2_INCLUDE_CLIENT_APP_ID_IN_VADEMECUM", True)

        params: dict[str, Any] = {page_param: page}
        client_app_id = getattr(settings, "QBI2_CLIENT_APP_ID", "")
        if include_client_id and client_app_id:
            params[client_id_param] = client_app_id
        params.update(extra_params)
        return params


class DiagnosticoService:
    def __init__(self, client: Qbi2Client | None = None):
        self.client = client or Qbi2Client()

    def buscar(self, query: str, extra_params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = (query or "").strip()
        if len(query) < 3:
            raise ValidationError("La busqueda de diagnostico debe tener al menos 3 caracteres.")

        params = {"text": query}
        client_app_id = getattr(settings, "QBI2_CLIENT_APP_ID", "")
        if client_app_id:
            params["clienteAppId"] = client_app_id
        params.update(extra_params or {})

        raw_response = self.client.get("/apirecipe/GetDiagnostico", params=params)
        items = normalize_list_response(raw_response, DIAGNOSTICO_LIST_KEYS)
        return {
            "query": query,
            "items": [normalize_diagnostico(item) for item in items],
            "raw": raw_response,
        }


def normalize_vademecum_response(raw_response: Any) -> list[Any]:
    return normalize_list_response(raw_response, COMMON_LIST_KEYS)


def _provider_page_count(page_info: Any, *, default: int) -> int:
    if not isinstance(page_info, dict):
        return default
    try:
        return max(default, int(page_info.get("cantidadPaginas") or default))
    except (TypeError, ValueError):
        return default


def _search_text(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or "").casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char)).strip()


def _medication_relevance(item: dict[str, Any], query: str) -> tuple[Any, ...]:
    needle = _search_text(query)
    product = _search_text(item.get("nombreProducto"))
    drug = _search_text(item.get("nombreDroga"))
    if product == needle:
        rank = 0
    elif product.startswith(needle):
        rank = 1
    elif drug == needle:
        rank = 2
    elif drug.startswith(needle):
        rank = 3
    elif needle in product:
        rank = 4
    elif needle in drug:
        rank = 5
    else:
        rank = 6
    return (
        rank,
        product,
        drug,
        _search_text(item.get("presentacion")),
        str(item.get("regNo") or ""),
    )


def normalize_list_response(raw_response: Any, list_keys: tuple[str, ...]) -> list[Any]:
    if raw_response is None:
        return []
    if isinstance(raw_response, list):
        return raw_response
    if isinstance(raw_response, dict):
        for key in list_keys:
            value = raw_response.get(key)
            if isinstance(value, list):
                return value
        for value in raw_response.values():
            if isinstance(value, list):
                return value
    return [raw_response]


def extract_page_info(raw_response: Any) -> dict[str, Any] | None:
    if isinstance(raw_response, dict) and isinstance(raw_response.get("pageInfo"), dict):
        return raw_response["pageInfo"]
    return None


def normalize_medicamento(item: Any) -> Any:
    if not isinstance(item, dict):
        return item

    nombre_producto = item.get("nombreProducto") or ""
    nombre_droga = item.get("nombreDroga") or ""
    presentacion = item.get("presentacion") or ""
    display_parts = [part for part in (nombre_producto, nombre_droga, presentacion) if part]

    return {
        "display": " - ".join(display_parts),
        "nombreProducto": item.get("nombreProducto"),
        "nombreDroga": item.get("nombreDroga"),
        "presentacion": item.get("presentacion"),
        "regNo": item.get("regNo"),
        "tieneCobertura": item.get("tieneCobertura"),
        "requiereAprobacion": item.get("requiereAprobacion"),
        "descuento": item.get("descuento"),
        "psicofarmaco": item.get("psicofarmaco"),
        "estupefaciente": item.get("estupefaciente"),
        "ventaControlada": item.get("ventaControlada"),
        "hiv": item.get("hiv"),
        "requiereDuplicado": item.get("requiereDuplicado"),
        "potencia": item.get("potencia"),
        "descripcionPotencia": item.get("descripcionPotencia"),
        "formaFarmaceutica": item.get("formaFarmaceutica"),
        "viaAdministracion": item.get("viaAdministracion"),
        "codigoTipoExpendio": item.get("codigoTipoExpendio"),
        "descripcionTipoExpendio": item.get("descripcionTipoExpendio"),
    }


def normalize_diagnostico(item: Any) -> Any:
    if not isinstance(item, dict):
        return item

    codigo = item.get("coddiagnostico") or item.get("codigoDiagnostico") or item.get("codigo")
    descripcion = item.get("descdiagnostico") or item.get("descripcion") or item.get("nombre")
    return {
        "display": " - ".join(part for part in (codigo, descripcion) if part),
        "iddiagnostico": item.get("iddiagnostico") or item.get("id"),
        "coddiagnostico": codigo,
        "descdiagnostico": descripcion,
    }
