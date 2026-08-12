from typing import Any
from urllib.parse import quote

from django.conf import settings
from django.core.exceptions import ValidationError

from .client import Qbi2Client


COMMON_LIST_KEYS = ("medicamentos", "items", "data", "result", "results", "medicines")
DIAGNOSTICO_LIST_KEYS = ("diagnosticos", "items", "data", "result", "results")
FINANCIADOR_LIST_KEYS = ("financiadores", "items", "data", "result", "results")
PRACTICA_LIST_KEYS = ("practicas", "items", "data", "result", "results")


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


class FinanciadorService:
    def __init__(self, client: Qbi2Client | None = None):
        self.client = client or Qbi2Client()

    def buscar(self, extra_params: dict[str, Any] | None = None) -> dict[str, Any]:
        raw_response = self.client.get("/apirecipe/GetFinanciadores", params=extra_params or {})
        items = normalize_list_response(raw_response, FINANCIADOR_LIST_KEYS)
        return {
            "items": [normalize_financiador(item) for item in items],
            "raw": raw_response,
        }


class PracticaService:
    def __init__(self, client: Qbi2Client | None = None):
        self.client = client or Qbi2Client()

    def buscar(
        self,
        query: str = "",
        page: int = 1,
        *,
        tipo: str = "",
        categoria: str = "",
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        query = (query or "").strip()
        if query and len(query) < 2:
            raise ValidationError("La busqueda de practica debe tener al menos 2 caracteres.")
        if page < 1:
            raise ValidationError("La pagina debe ser mayor o igual a 1.")

        params: dict[str, Any] = {
            "clienteAppId": getattr(settings, "QBI2_CLIENT_APP_ID", ""),
            "numeroPagina": page,
        }
        if query:
            params["search"] = query
        if tipo:
            params["tipo"] = tipo
        if categoria:
            params["categoria"] = categoria
        params.update(extra_params or {})

        raw_response = self.client.get("/apirecipe/GetPracticas", params=params)
        items = normalize_list_response(raw_response, PRACTICA_LIST_KEYS)
        return {
            "query": query,
            "page": page,
            "items": [normalize_practica(item) for item in items],
            "page_info": extract_page_info(raw_response),
            "raw": raw_response,
        }


def normalize_vademecum_response(raw_response: Any) -> list[Any]:
    return normalize_list_response(raw_response, COMMON_LIST_KEYS)


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


def normalize_financiador(item: Any) -> Any:
    if not isinstance(item, dict):
        return item

    planes = item.get("planes") if isinstance(item.get("planes"), list) else []
    nombre = item.get("nombreComercial") or item.get("nombre") or item.get("descripcion")
    return {
        "display": " - ".join(
            part
            for part in (
                str(item.get("idfinanciador") or item.get("idFinanciador") or item.get("id") or ""),
                str(item.get("nrofinanciador") or item.get("nroFinanciador") or ""),
                nombre or "",
            )
            if part
        ),
        "idfinanciador": item.get("idfinanciador") or item.get("idFinanciador") or item.get("id"),
        "nrofinanciador": item.get("nrofinanciador") or item.get("nroFinanciador"),
        "nombreComercial": nombre,
        "planes": [
            {
                "id": plan.get("id"),
                "nombre": plan.get("nombre") or plan.get("descripcion"),
            }
            for plan in planes
            if isinstance(plan, dict)
        ],
    }


def normalize_practica(item: Any) -> Any:
    if not isinstance(item, dict):
        return item

    nombre = item.get("practica") or item.get("nombre") or item.get("descripcion")
    nomenclador = item.get("nomenclador") if isinstance(item.get("nomenclador"), dict) else {}
    snomed = nomenclador.get("snomed")
    nbu = nomenclador.get("nbu")
    return {
        "display": " - ".join(
            part
            for part in (
                str(item.get("id") or ""),
                nombre or "",
                item.get("categoria") or "",
                item.get("tipo") or "",
                f"SNOMED {snomed}" if snomed else "",
                f"NBU {nbu}" if nbu else "",
            )
            if part
        ),
        "id": item.get("id"),
        "practica": nombre,
        "codigo": item.get("codigo") or item.get("codigoPractica"),
        "codSnomed": snomed,
        "nbu": nbu,
        "nomenclador": {
            "snomed": snomed,
            "nbu": nbu,
        },
        "categoria": item.get("categoria"),
        "tipo": item.get("tipo"),
    }
