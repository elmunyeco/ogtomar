from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from django.conf import settings
from django.utils import timezone

from .client import Qbi2Client


DEFAULT_LOTRIAL_REG_NO = "34959"


@dataclass(frozen=True)
class RecetaPocResult:
    payload: dict[str, Any]
    response: dict[str, Any] | list[Any] | str | None


def build_hml_receta_poc_payload(
    *,
    reg_no: str = DEFAULT_LOTRIAL_REG_NO,
    nombre_producto: str = "LOTRIAL",
    nombre_droga: str = "enalapril",
    presentacion: str = "10 mg comp.x 30",
    nro_doc: str | None = None,
    paciente_nombre: str = "Prueba",
    paciente_apellido: str = "Paciente",
    paciente_sexo: str = "M",
    paciente_fecha_nacimiento: str = "1980-01-01",
    diagnostico: str = "Hipertension arterial",
    posologia: str = "Tomar 1 comprimido por dia segun indicacion medica.",
    cantidad: int = 1,
    tratamiento: int = 0,
    medico_nombre: str = "Prueba",
    medico_apellido: str = "Medico",
    medico_matricula_tipo: str = "MN",
    medico_matricula_numero: str = "123456",
    medico_especialidad: str = "Cardiologia",
    medico_profesion: str = "Medico",
    medico_nro_doc: str = "11111111",
    medico_id_tributario: str = "20111111112",
    consultorio_nombre: str = "Consultorio HML Prueba",
    consultorio_direccion: str = "Gral. Las Heras 459",
    consultorio_email: str = "consultorio.prueba@example.com",
    consultorio_contacto: str = "1100000002",
) -> dict[str, Any]:
    """Payload HML con datos ficticios para entender el contrato de Receta.

    El unico dato clinico deliberadamente real del proveedor es `regNo`.
    """

    patient_doc = nro_doc or _fake_patient_doc()
    client_app_id = int(getattr(settings, "QBI2_CLIENT_APP_ID", 563))

    return {
        "clienteAppId": client_app_id,
        "diagnostico": diagnostico,
        "imprimirDiagnostico": "S",
        "indicaciones": "Control de presion arterial. PoC HML con datos ficticios.",
        "observaciones": "PoC de homologacion Qbi2. No usar como receta real.",
        "medicamentos": [
            {
                "nombreProducto": nombre_producto,
                "nombreDroga": nombre_droga,
                "presentacion": presentacion,
                "cantidad": cantidad,
                "permiteSustitucion": "",
                "regNo": reg_no,
                "tratamiento": tratamiento,
                "diagnostico": diagnostico,
                "posologia": posologia,
                "observaciones": "PoC HML",
                "forzarDuplicado": False,
            }
        ],
        "paciente": {
            "apellido": paciente_apellido,
            "nombre": paciente_nombre,
            "tipoDoc": "DNI",
            "nroDoc": patient_doc,
            "sexo": paciente_sexo,
            "fechaNacimiento": paciente_fecha_nacimiento,
            "email": "paciente.prueba@example.com",
            "telefono": "1100000000",
            "localidad": "Monte Grande",
            "provincia": "Buenos Aires",
            "domicilio": {
                "calle": "Calle Falsa",
                "numero": "123",
                "codigoPostal": "1842",
                "localidad": "Monte Grande",
                "provincia": "Buenos Aires",
                "pais": "Argentina",
            },
            "ocultarPaciente": False,
        },
        "medico": {
            "apellido": medico_apellido,
            "nombre": medico_nombre,
            "tipoDoc": "DNI",
            "nroDoc": medico_nro_doc,
            "especialidad": medico_especialidad,
            "sexo": "M",
            "fechaNacimiento": "1970-01-01",
            "email": "medico.prueba@example.com",
            "telefono": "1100000001",
            "idTributario": medico_id_tributario,
            "profesion": medico_profesion,
            "matricula": {
                "tipo": medico_matricula_tipo,
                "numero": medico_matricula_numero,
                "profesion": medico_profesion,
                "especialidad": medico_especialidad,
            },
            "sello": {
                "linea1": f"Dr. {medico_nombre} {medico_apellido}",
                "linea2": medico_especialidad,
                "linea3": f"{medico_matricula_tipo} {medico_matricula_numero}",
            },
        },
        "lugarAtencion": {
            "nombreConsultorio": consultorio_nombre,
            "datosContacto": consultorio_contacto,
            "email": consultorio_email,
            "domicilio": {
                "direccion": consultorio_direccion,
                "codigoPostal": "1842",
                "localidad": "Monte Grande",
                "provincia": "Buenos Aires",
                "pais": "Argentina",
            },
        },
    }


def emitir_receta_hml_poc(
    *,
    reg_no: str = DEFAULT_LOTRIAL_REG_NO,
    nro_doc: str | None = None,
    diagnostico: str = "Hipertension arterial",
    client: Qbi2Client | None = None,
) -> RecetaPocResult:
    payload = build_hml_receta_poc_payload(
        reg_no=reg_no,
        nro_doc=nro_doc,
        diagnostico=diagnostico,
    )
    response = (client or Qbi2Client()).post("/apirecipe/Receta", payload)
    return RecetaPocResult(payload=payload, response=response)


def emitir_receta_payload(payload: dict[str, Any], client: Qbi2Client | None = None) -> RecetaPocResult:
    response = (client or Qbi2Client()).post("/apirecipe/Receta", payload)
    return RecetaPocResult(payload=payload, response=response)


def summarize_receta_response(response: Any) -> dict[str, Any]:
    if not isinstance(response, dict):
        return {"raw_type": type(response).__name__}

    recetas = response.get("recetas") or []
    receta = recetas[0] if recetas else {}
    response_items = response.get("response") or []
    response_item = response_items[0] if response_items else {}

    return {
        "id": receta.get("id"),
        "idReceta": receta.get("idReceta"),
        "fecha": receta.get("fecha"),
        "s3Link": receta.get("s3Link"),
        "verificador": receta.get("verificador"),
        "idTransaccion": response.get("idTransaccion"),
        "errores": response.get("errores"),
        "status": response_item.get("status") if isinstance(response_item, dict) else None,
        "fechavencimiento": response_item.get("fechavencimiento") if isinstance(response_item, dict) else None,
    }


def _fake_patient_doc() -> str:
    now = timezone.localtime(timezone.now()) if settings.USE_TZ else datetime.now()
    return "99" + now.strftime("%H%M%S")
