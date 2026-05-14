from typing import Any
from urllib.parse import quote

from django.conf import settings
from django.core.exceptions import ValidationError

from .client import Qbi2Client


COMMON_LIST_KEYS = ("medicamentos", "items", "data", "result", "results", "medicines")


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


def normalize_vademecum_response(raw_response: Any) -> list[Any]:
    if raw_response is None:
        return []
    if isinstance(raw_response, list):
        return raw_response
    if isinstance(raw_response, dict):
        for key in COMMON_LIST_KEYS:
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
