from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.conf import settings

from .client import Qbi2Client


@dataclass(frozen=True)
class SpontaneousPocResult:
    operation: str
    endpoint: str
    payload: dict[str, Any]
    response: Any
    summary: dict[str, Any]


def build_spontaneous_payload(data: dict[str, Any], operation: str) -> tuple[str, dict[str, Any]]:
    if operation == "receta":
        return "/apirecipe/Receta", build_receta_payload(data)
    if operation == "practica":
        return "/apirecipe/prescribirPractica", build_practica_payload(data)
    raise ValueError("Operacion QBI2 no soportada para esta PoC.")


def emit_spontaneous_payload(
    data: dict[str, Any],
    operation: str,
    client: Qbi2Client | None = None,
) -> SpontaneousPocResult:
    endpoint, payload = build_spontaneous_payload(data, operation)
    response = (client or Qbi2Client()).post(endpoint, payload)
    summary = summarize_document_response(response, operation=operation)
    return SpontaneousPocResult(
        operation=operation,
        endpoint=endpoint,
        payload=payload,
        response=response,
        summary=summary,
    )


def anular_documento_hash(hash_id: str, operation: str = "receta", client: Qbi2Client | None = None) -> Any:
    hash_id = (hash_id or "").strip()
    if not hash_id:
        raise ValueError("El hash QBI2 es obligatorio para anular.")
    endpoint = "/apirecipe/Practica" if operation == "practica" else "/apirecipe/Receta"
    payload = {"clienteAppId": _client_app_id()}
    return (client or Qbi2Client()).delete(f"{endpoint}/{hash_id}", payload)


def build_receta_payload(data: dict[str, Any]) -> dict[str, Any]:
    diagnostico = _text(data, "diagnostico", "Hipertension arterial")
    medicamento = {
        "nombreProducto": _text(data, "nombreProducto", "LOTRIAL"),
        "nombreDroga": _text(data, "nombreDroga", "enalapril"),
        "presentacion": _text(data, "presentacion", "10 mg comp.x 30"),
        "cantidad": _int(data, "cantidad", 1),
        "permiteSustitucion": _text(data, "permiteSustitucion", ""),
        "regNo": _text(data, "regNo", "34959"),
        "tratamiento": _int(data, "tratamiento", 0),
        "diagnostico": diagnostico,
        "codigoDiagnostico": _text(data, "codigoDiagnostico", ""),
        "posologia": _text(data, "posologia", "Tomar segun indicacion medica."),
        "observaciones": _text(data, "itemObservaciones", ""),
        "forzarDuplicado": _bool(data, "forzarDuplicado", False),
    }

    payload = {
        "paciente": build_paciente(data),
        "medico": build_medico(data),
        "medicamentos": [medicamento],
        "diagnostico": diagnostico,
        "imprimirDiagnostico": _text(data, "imprimirDiagnostico", "S"),
        "indicaciones": _text(data, "indicaciones", ""),
        "observaciones": _text(data, "observaciones", ""),
        "fechaEmision": _text(data, "fechaEmision", ""),
        "lugarAtencion": build_lugar_atencion(data),
        "clienteAppId": _client_app_id(),
        "informacionExtra": build_informacion_extra(data),
    }
    _maybe_add_postdatadas(payload, data)
    return _strip_empty(payload)


def build_practica_payload(data: dict[str, Any]) -> dict[str, Any]:
    diagnostico = _text(data, "diagnostico", "Control cardiologico")
    practica = {
        "id": _maybe_int(_text(data, "practicaId", "")),
        "nombre": _text(data, "practicaNombre", ""),
        "codigo": _text(data, "practicaCodigoPropio", ""),
        "codSnomed": _text(data, "practicaCodSnomed", ""),
        "categoria": _text(data, "practicaCategoria", ""),
        "cantidad": _int(data, "practicaCantidad", 1),
        "diagnostico": diagnostico,
        "codigoDiagnostico": _text(data, "codigoDiagnostico", ""),
        "observaciones": _text(data, "itemObservaciones", ""),
        "descripcionLibre": _text(data, "practicaDescripcionLibre", ""),
    }

    payload = {
        "paciente": build_paciente(data),
        "medico": build_medico(data),
        "prescripcion": [_strip_empty(practica)],
        "diagnostico": diagnostico,
        "imprimirDiagnostico": _text(data, "imprimirDiagnostico", "S"),
        "indicaciones": _text(data, "indicaciones", ""),
        "observaciones": _text(data, "observaciones", ""),
        "fechaEmision": _text(data, "fechaEmision", ""),
        "confidencial": _bool(data, "confidencial", False),
        "lugarAtencion": build_lugar_atencion(data),
        "clienteAppId": _client_app_id(),
        "informacionExtra": build_informacion_extra(data),
    }
    _maybe_add_postdatadas(payload, data)
    return _strip_empty(payload)


def build_paciente(data: dict[str, Any]) -> dict[str, Any]:
    paciente = {
        "apellido": _text(data, "pacienteApellido", "Paciente"),
        "nombre": _text(data, "pacienteNombre", "Prueba"),
        "tipoDoc": _text(data, "pacienteTipoDoc", "DNI"),
        "nroDoc": _text(data, "pacienteNroDoc", "99999999"),
        "sexo": _text(data, "pacienteSexo", "M"),
        "fechaNacimiento": _text(data, "pacienteFechaNacimiento", "1980-01-01"),
        "cuil": _text(data, "pacienteCuil", ""),
        "email": _text(data, "pacienteEmail", "paciente.prueba@example.com"),
        "telefono": _text(data, "pacienteTelefono", "1100000000"),
        "localidad": _text(data, "pacienteLocalidad", "Monte Grande"),
        "provincia": _text(data, "pacienteProvincia", "Buenos Aires"),
        "pais": _text(data, "pacientePais", "AR"),
        "domicilio": build_domicilio(data, "paciente"),
        "cobertura": build_cobertura(data),
        "ocultarPaciente": _bool(data, "ocultarPaciente", False),
    }
    return _strip_empty(paciente)


def build_medico(data: dict[str, Any]) -> dict[str, Any]:
    nombre = _text(data, "medicoNombre", "Prueba")
    apellido = _text(data, "medicoApellido", "Medico")
    especialidad = _text(data, "medicoEspecialidad", "Cardiologia")
    matricula_tipo = _text(data, "medicoMatriculaTipo", "MN")
    matricula_numero = _text(data, "medicoMatriculaNumero", "123456")
    profesion = _text(data, "medicoProfesion", "Medico")

    medico = {
        "apellido": apellido,
        "nombre": nombre,
        "tipoDoc": _text(data, "medicoTipoDoc", "DNI"),
        "nroDoc": _text(data, "medicoNroDoc", "11111111"),
        "sexo": _text(data, "medicoSexo", "M"),
        "fechaNacimiento": _text(data, "medicoFechaNacimiento", "1970-01-01"),
        "email": _text(data, "medicoEmail", "medico.prueba@example.com"),
        "telefono": _text(data, "medicoTelefono", "1100000001"),
        "pais": _text(data, "medicoPais", "AR"),
        "profesion": profesion,
        "especialidad": especialidad,
        "firmalink": _text(data, "medicoFirmaLink", ""),
        "firmabase64": _text(data, "medicoFirmaBase64", ""),
        "matricula": {
            "tipo": matricula_tipo,
            "numero": matricula_numero,
            "provincia": _text(data, "medicoMatriculaProvincia", ""),
            "profesion": profesion,
            "especialidad": especialidad,
        },
        "sello": {
            "linea1": _text(data, "selloLinea1", f"Dr. {nombre} {apellido}"),
            "linea2": _text(data, "selloLinea2", especialidad),
            "linea3": _text(data, "selloLinea3", f"{matricula_tipo} {matricula_numero}"),
        },
        "idTributario": _text(data, "medicoIdTributario", "20111111112"),
        "idREFEPS": _text(data, "medicoIdRefeps", ""),
    }
    return _strip_empty(medico)


def build_lugar_atencion(data: dict[str, Any]) -> dict[str, Any]:
    lugar = {
        "nombreConsultorio": _text(data, "consultorioNombre", "Consultorio HML Prueba"),
        "domicilio": build_domicilio(data, "consultorio"),
        "datosContacto": _text(data, "consultorioContacto", "1100000002"),
        "email": _text(data, "consultorioEmail", "consultorio.prueba@example.com"),
        "logo": _text(data, "consultorioLogo", ""),
    }
    return _strip_empty(lugar)


def build_domicilio(data: dict[str, Any], prefix: str) -> dict[str, Any]:
    domicilio = {
        "calle": _text(data, f"{prefix}Calle", "Calle Falsa" if prefix == "paciente" else "Gral. Las Heras"),
        "numero": _text(data, f"{prefix}Numero", "123" if prefix == "paciente" else "459"),
        "piso": _text(data, f"{prefix}Piso", ""),
        "depto": _text(data, f"{prefix}Depto", ""),
        "codigoPostal": _text(data, f"{prefix}CodigoPostal", "1842"),
        "localidad": _text(data, f"{prefix}Localidad", "Monte Grande"),
        "municipio": _text(data, f"{prefix}Municipio", ""),
        "provincia": _text(data, f"{prefix}Provincia", "Buenos Aires"),
        "pais": _text(data, f"{prefix}Pais", "AR"),
        "observacion": _text(data, f"{prefix}Observacion", ""),
        "direccion": _text(data, f"{prefix}Direccion", ""),
    }
    return _strip_empty(domicilio)


def build_cobertura(data: dict[str, Any]) -> dict[str, Any]:
    cobertura = {
        "idFinanciador": _text(data, "idFinanciador", ""),
        "nroFinanciador": _text(data, "nroFinanciador", ""),
        "planId": _maybe_int(_text(data, "planId", "")),
        "plan": _text(data, "plan", ""),
        "numero": _text(data, "afiliadoNumero", ""),
        "dniTitular": _text(data, "dniTitular", ""),
    }
    return _strip_empty(cobertura)


def build_informacion_extra(data: dict[str, Any]) -> list[dict[str, str]]:
    raw = _text(data, "informacionExtra", "")
    items: list[dict[str, str]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if "=" in line:
            key, value = line.split("=", 1)
        elif ":" in line:
            key, value = line.split(":", 1)
        else:
            continue
        key = key.strip()
        value = value.strip()
        if key and value:
            items.append({"key": key, "value": value})
    return items


def summarize_document_response(response: Any, *, operation: str) -> dict[str, Any]:
    if not isinstance(response, dict):
        return {"operation": operation, "raw_type": type(response).__name__}

    document = _first_document(response, operation)
    response_items = response.get("response") or []
    response_item = response_items[0] if response_items and isinstance(response_items[0], dict) else {}

    return {
        "operation": operation,
        "id": document.get("id"),
        "idReceta": document.get("idReceta"),
        "numeroPrescripcion": document.get("numeroPrescripcion"),
        "fecha": document.get("fecha"),
        "s3Link": document.get("s3Link"),
        "verificador": document.get("verificador"),
        "idTransaccion": response.get("idTransaccion"),
        "errores": response.get("errores"),
        "status": response_item.get("status") if isinstance(response_item, dict) else None,
        "fechavencimiento": response_item.get("fechavencimiento") if isinstance(response_item, dict) else None,
    }


def _first_document(response: dict[str, Any], operation: str) -> dict[str, Any]:
    keys = (
        ("recetas", "receta", "documentos")
        if operation == "receta"
        else ("otrasRecetas", "prescripciones", "practicas", "recetas", "documentos")
    )
    for key in keys:
        value = response.get(key)
        if isinstance(value, list) and value and isinstance(value[0], dict):
            return value[0]
    return {}


def _maybe_add_postdatadas(payload: dict[str, Any], data: dict[str, Any]) -> None:
    cantidad = _int(data, "postdatadasCantidad", 0)
    dias = _int(data, "postdatadasDias", 0)
    fechas = [
        item.strip()
        for item in _text(data, "postdatadasFechas", "").replace(",", "\n").splitlines()
        if item.strip()
    ]
    if cantidad or dias or fechas:
        payload["recetasPostadatas"] = _strip_empty(
            {
                "cantidad": cantidad,
                "diasAPosdatar": dias,
                "fechas": fechas,
            }
        )


def _client_app_id() -> int | str:
    raw = str(getattr(settings, "QBI2_CLIENT_APP_ID", ""))
    return int(raw) if raw.isdigit() else raw


def _text(data: dict[str, Any], key: str, default: str = "") -> str:
    value = data.get(key)
    if value is None or value == "":
        return default
    return str(value).strip()


def _int(data: dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(data.get(key) or default)
    except (TypeError, ValueError):
        return default


def _maybe_int(value: str) -> int | str:
    value = (value or "").strip()
    if not value:
        return ""
    return int(value) if value.isdigit() else value


def _bool(data: dict[str, Any], key: str, default: bool = False) -> bool:
    value = data.get(key)
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "t", "yes", "s", "si", "on"}


def _strip_empty(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            cleaned_item = _strip_empty(item)
            if cleaned_item in ("", None, [], {}):
                continue
            cleaned[key] = cleaned_item
        return cleaned
    if isinstance(value, list):
        return [_strip_empty(item) for item in value if _strip_empty(item) not in ("", None, [], {})]
    return value
