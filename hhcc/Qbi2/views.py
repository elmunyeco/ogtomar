import base64
import copy
import json
import re
import unicodedata
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from django.contrib import messages
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from .client import Qbi2ConfigurationError, Qbi2HTTPError
from .models import SolicitudReceta
from .portal import create_prescription_request, find_patient_history, get_client_ip
from .professional_profile import load_professional_profile, resolve_profile_asset
from .recipes import (
    build_hml_receta_poc_payload,
    build_receta_payload_from_solicitud,
    emitir_receta_payload,
    summarize_receta_response,
)
from .services import DiagnosticoService, FinanciadorService, PracticaService, VademecumService
from .spontaneous import (
    anular_documento_hash,
    build_spontaneous_payload,
    emit_spontaneous_payload,
)
from main.models import Paciente


ESPONTANEA_2_PATIENT_DOCUMENT = "23101065"


@require_GET
def qbi2_poc_home(request):
    return render(request, "Qbi2/poc_home.html")


@require_GET
def vademecum_legacy(request):
    return render(request, "Qbi2/vademecum_legacy.html")


def receta_poc_page(request):
    payload = build_hml_receta_poc_payload(nro_doc="99999999")
    return render(request, "Qbi2/receta_poc.html", {"payload": payload})


@ensure_csrf_cookie
def espontanea_poc_page(request):
    return render(
        request,
        "Qbi2/espontanea_poc.html",
        {
            "client_app_id": getattr(settings, "QBI2_CLIENT_APP_ID", ""),
            "base_url": getattr(settings, "QBI2_BASE_URL", ""),
        },
    )


@ensure_csrf_cookie
def espontanea_poc_2_page(request):
    defaults = _espontanea_2_defaults()
    return render(
        request,
        "Qbi2/espontanea_poc_2.html",
        {
            "patient": defaults["patient"],
            "doctor": defaults["doctor"],
            "coverage": defaults["coverage"],
            "initial_patient": {
                "patient": defaults["patient"],
                "coverage": defaults["coverage"],
            },
            "today": timezone.localdate().isoformat(),
        },
    )


@ensure_csrf_cookie
def pacientes_portal_page(request):
    return render(request, "Qbi2/pacientes_portal.html")


def solicitudes_receta_page(request):
    estado = request.GET.get("estado") or SolicitudReceta.Estado.PENDIENTE
    estados_validos = {choice[0] for choice in SolicitudReceta.Estado.choices}
    queryset = SolicitudReceta.objects.select_related("paciente", "historia_clinica", "aprobado_por")
    if estado != "todas" and estado in estados_validos:
        queryset = queryset.filter(estado=estado)
    elif estado != "todas":
        estado = SolicitudReceta.Estado.PENDIENTE
        queryset = queryset.filter(estado=estado)

    counts = {
        "pendiente": SolicitudReceta.objects.filter(estado=SolicitudReceta.Estado.PENDIENTE).count(),
        "aprobada": SolicitudReceta.objects.filter(estado=SolicitudReceta.Estado.APROBADA).count(),
        "rechazada": SolicitudReceta.objects.filter(estado=SolicitudReceta.Estado.RECHAZADA).count(),
        "emitida": SolicitudReceta.objects.filter(estado=SolicitudReceta.Estado.EMITIDA).count(),
        "error_emision": SolicitudReceta.objects.filter(estado=SolicitudReceta.Estado.ERROR_EMISION).count(),
        "todas": SolicitudReceta.objects.count(),
    }
    return render(
        request,
        "Qbi2/solicitudes_receta.html",
        {
            "solicitudes": queryset[:100],
            "estado": estado,
            "counts": counts,
            "estados": SolicitudReceta.Estado,
        },
    )


@require_GET
def health(request):
    return JsonResponse(
        {
            "status": "ok",
            "base_url": getattr(settings, "QBI2_BASE_URL", ""),
            "auth_mode": getattr(settings, "QBI2_AUTH_MODE", "auto"),
            "token_configured": bool(getattr(settings, "QBI2_BEARER_TOKEN", "")),
            "client_app_id_configured": bool(getattr(settings, "QBI2_CLIENT_APP_ID", "")),
            "vademecum_path": getattr(settings, "QBI2_VADEMECUM_PATH", ""),
        }
    )


@require_GET
def buscar_vademecum_legacy(request):
    query = request.GET.get("q") or request.GET.get("query") or ""
    raw = request.GET.get("raw") == "1"
    extra_params = {
        key.removeprefix("qbi2_"): value
        for key, value in request.GET.items()
        if key.startswith("qbi2_")
    }

    try:
        page = int(request.GET.get("page") or request.GET.get("pagina") or "1")
        result = VademecumService().buscar(query, page=page, extra_params=extra_params)
    except ValidationError as exc:
        return JsonResponse({"status": "error", "message": "; ".join(exc.messages)}, status=400)
    except ValueError:
        return JsonResponse({"status": "error", "message": "La pagina debe ser numerica."}, status=400)
    except Qbi2ConfigurationError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=503)
    except Qbi2HTTPError as exc:
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
                "provider_status": exc.status_code,
                "provider_payload": exc.payload,
            },
            status=502,
        )

    response = {
        "status": "success",
        "query": result["query"],
        "page": result["page"],
        "count": len(result["items"]),
        "pageInfo": result["page_info"],
        "items": result["items"],
    }
    if raw:
        response["raw"] = result["raw"]
    return JsonResponse(response)


@require_GET
def buscar_vademecum_portal(request):
    return buscar_vademecum_legacy(request)


@require_GET
def espontanea_catalogo_api(request, catalogo):
    query = request.GET.get("q", "")
    page = _positive_int(request.GET.get("page"), default=1)
    try:
        if catalogo == "medicamentos":
            result = VademecumService().buscar(
                query,
                page=page,
                extra_params=_qbi2_prefixed_params(request),
            )
        elif catalogo == "diagnosticos":
            result = DiagnosticoService().buscar(
                query,
                extra_params=_qbi2_prefixed_params(request),
            )
        elif catalogo == "financiadores":
            result = FinanciadorService().buscar(extra_params=_qbi2_prefixed_params(request))
        elif catalogo == "practicas":
            result = PracticaService().buscar(
                query,
                page=page,
                tipo=request.GET.get("tipo", ""),
                categoria=request.GET.get("categoria", ""),
                extra_params=_qbi2_prefixed_params(request),
            )
        else:
            return JsonResponse({"status": "error", "message": "Catalogo no soportado."}, status=404)
    except ValidationError as exc:
        return JsonResponse({"status": "error", "message": "; ".join(exc.messages)}, status=400)
    except Qbi2ConfigurationError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=503)
    except Qbi2HTTPError as exc:
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
                "provider_status": exc.status_code,
                "provider_payload": exc.payload,
            },
            status=502,
        )

    return JsonResponse(
        {
            "status": "success",
            "catalogo": catalogo,
            "count": len(result.get("items", []) or []),
            "items": result.get("items", []),
            "pageInfo": result.get("page_info"),
            "raw": result.get("raw"),
        }
    )


@require_GET
def espontanea_2_pacientes_api(request):
    """Search active HHCC patients and expose only fields needed by the recipe selector."""
    query = str(request.GET.get("q") or "").strip()
    compact_query = re.sub(r"[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", "", query)
    if len(compact_query) < 3:
        return JsonResponse(
            {"status": "error", "message": "Ingresá al menos 3 caracteres para buscar un paciente."},
            status=400,
        )

    filters = Q()
    for token in query.split():
        token_filter = Q(apellido__icontains=token) | Q(nombre__icontains=token)
        document_token = re.sub(r"\D", "", token)
        if document_token:
            token_filter |= Q(numDoc__icontains=document_token)
            if document_token.isdigit():
                token_filter |= Q(pk=int(document_token))
        filters &= token_filter

    patients = (
        Paciente.objects.select_related("idTipoDoc")
        .filter(filters, deBaja=False)
        .order_by("apellido", "nombre", "id")[:12]
    )
    items = []
    for patient_record in patients:
        patient_data = _espontanea_2_patient_data(patient_record)
        items.append(
            {
                "patient": patient_data["patient"],
                "coverage": patient_data["coverage"],
            }
        )
    return JsonResponse({"status": "success", "count": len(items), "items": items})


@csrf_protect
@require_POST
def espontanea_preview_api(request):
    data_or_response = _json_body(request)
    if isinstance(data_or_response, JsonResponse):
        return data_or_response
    operation = data_or_response.get("operation") or "receta"
    try:
        endpoint, payload = build_spontaneous_payload(data_or_response, operation)
    except (TypeError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    return JsonResponse({"status": "success", "operation": operation, "endpoint": endpoint, "payload": payload})


@csrf_protect
@require_POST
def espontanea_2_preview_api(request):
    """Build the simplified recipe payload without making a QBI2 write request."""
    data_or_response = _json_body(request)
    if isinstance(data_or_response, JsonResponse):
        return data_or_response

    try:
        safe_data = _espontanea_2_safe_data(data_or_response)
        endpoint, payload = build_spontaneous_payload(safe_data, "receta")
    except (TypeError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    except Qbi2ConfigurationError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=503)

    return JsonResponse(
        {
            "status": "success",
            "mode": "preview_only",
            "message": "Payload preparado localmente. No se emitió ninguna receta.",
            "operation": "receta",
            "endpoint": endpoint,
            "payload": _redact_profile_images(payload),
        }
    )


@csrf_protect
@require_POST
def espontanea_2_emit_api(request):
    """Emit from the simplified client, with patient and professional data owned by the server."""
    data_or_response = _json_body(request)
    if isinstance(data_or_response, JsonResponse):
        return data_or_response

    try:
        safe_data = _espontanea_2_safe_data(data_or_response)
        result = emit_spontaneous_payload(safe_data, "receta")
    except (TypeError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    except Qbi2ConfigurationError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=503)
    except Qbi2HTTPError as exc:
        endpoint, payload = build_spontaneous_payload(safe_data, "receta")
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
                "operation": "receta",
                "endpoint": endpoint,
                "payload": _redact_profile_images(payload),
                "provider_status": exc.status_code,
                "provider_payload": exc.payload,
            },
            status=502,
        )

    return JsonResponse(
        {
            "status": "success",
            "operation": result.operation,
            "endpoint": result.endpoint,
            "payload": _redact_profile_images(result.payload),
            "summary": result.summary,
            "response": result.response,
        }
    )


@csrf_protect
@require_POST
def espontanea_emitir_api(request):
    data_or_response = _json_body(request)
    if isinstance(data_or_response, JsonResponse):
        return data_or_response
    operation = data_or_response.get("operation") or "receta"
    try:
        result = emit_spontaneous_payload(data_or_response, operation)
    except (TypeError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    except Qbi2ConfigurationError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=503)
    except Qbi2HTTPError as exc:
        endpoint, payload = build_spontaneous_payload(data_or_response, operation)
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
                "operation": operation,
                "endpoint": endpoint,
                "payload": payload,
                "provider_status": exc.status_code,
                "provider_payload": exc.payload,
            },
            status=502,
        )

    return JsonResponse(
        {
            "status": "success",
            "operation": result.operation,
            "endpoint": result.endpoint,
            "payload": result.payload,
            "summary": result.summary,
            "response": result.response,
        }
    )


@csrf_protect
@require_POST
def espontanea_anular_api(request):
    data_or_response = _json_body(request)
    if isinstance(data_or_response, JsonResponse):
        return data_or_response
    hash_id = data_or_response.get("hash") or data_or_response.get("id") or ""
    operation = data_or_response.get("operation") or "receta"
    try:
        response = anular_documento_hash(hash_id, operation)
    except ValueError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    except Qbi2ConfigurationError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=503)
    except Qbi2HTTPError as exc:
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
                "provider_status": exc.status_code,
                "provider_payload": exc.payload,
            },
            status=502,
        )
    return JsonResponse({"status": "success", "response": response})


@csrf_protect
@require_POST
def emitir_receta_poc(request):
    try:
        form_data = json.loads(request.body.decode("utf-8") or "{}")
        payload = build_hml_receta_poc_payload(
            reg_no=form_data.get("regNo") or "34959",
            nombre_producto=form_data.get("nombreProducto") or "LOTRIAL",
            nombre_droga=form_data.get("nombreDroga") or "enalapril",
            presentacion=form_data.get("presentacion") or "10 mg comp.x 30",
            nro_doc=form_data.get("pacienteNroDoc"),
            paciente_nombre=form_data.get("pacienteNombre") or "Prueba",
            paciente_apellido=form_data.get("pacienteApellido") or "Paciente",
            paciente_sexo=form_data.get("pacienteSexo") or "M",
            paciente_fecha_nacimiento=form_data.get("pacienteFechaNacimiento") or "1980-01-01",
            diagnostico=form_data.get("diagnostico") or "Hipertension arterial",
            posologia=form_data.get("posologia") or "Tomar 1 comprimido por dia segun indicacion medica.",
            cantidad=int(form_data.get("cantidad") or 1),
            tratamiento=int(form_data.get("tratamiento") or 0),
            medico_nombre=form_data.get("medicoNombre") or "Prueba",
            medico_apellido=form_data.get("medicoApellido") or "Medico",
            medico_matricula_tipo=form_data.get("medicoMatriculaTipo") or "MN",
            medico_matricula_numero=form_data.get("medicoMatriculaNumero") or "123456",
            medico_especialidad=form_data.get("medicoEspecialidad") or "Cardiologia",
            medico_profesion=form_data.get("medicoProfesion") or "Medico",
            medico_nro_doc=form_data.get("medicoNroDoc") or "11111111",
            medico_id_tributario=form_data.get("medicoIdTributario") or "20111111112",
            consultorio_nombre=form_data.get("consultorioNombre") or "Consultorio HML Prueba",
            consultorio_direccion=form_data.get("consultorioDireccion") or "Gral. Las Heras 459",
            consultorio_email=form_data.get("consultorioEmail") or "consultorio.prueba@example.com",
            consultorio_contacto=form_data.get("consultorioContacto") or "1100000002",
        )
        result = emitir_receta_payload(payload)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        return JsonResponse({"status": "error", "message": f"Payload invalido: {exc}"}, status=400)
    except Qbi2ConfigurationError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=503)
    except Qbi2HTTPError as exc:
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
                "provider_status": exc.status_code,
                "provider_payload": exc.payload,
            },
            status=502,
        )

    return JsonResponse(
        {
            "status": "success",
            "summary": summarize_receta_response(result.response),
            "response": result.response,
        }
    )


@csrf_protect
@require_POST
def validar_paciente_portal(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Datos invalidos."}, status=400)

    paciente, historia = find_patient_history(
        apellido=data.get("apellido", ""),
        documento=data.get("documento", ""),
    )
    if not paciente or not historia:
        return JsonResponse({"status": "rejected", "message": "No tenes Historia Clinica"}, status=404)

    medicamentos = _selected_medications_from_portal_data(data)
    if not medicamentos:
        return JsonResponse({"status": "error", "message": "Elegí al menos un medicamento del vademécum."}, status=400)
    if len(medicamentos) > 10:
        return JsonResponse({"status": "error", "message": "Podés seleccionar hasta 10 medicamentos."}, status=400)
    diagnostico = (data.get("diagnostico") or "").strip()
    if not diagnostico:
        return JsonResponse({"status": "error", "message": "Ingresá el diagnóstico."}, status=400)

    grupos_medicamentos = list(_chunks(medicamentos, 2))
    solicitudes = []
    with transaction.atomic():
        for index, grupo in enumerate(grupos_medicamentos, start=1):
            solicitudes.append(
                create_prescription_request(
                    paciente,
                    historia,
                    grupo[0],
                    medicamentos=grupo,
                    receta_orden=index,
                    total_recetas=len(grupos_medicamentos),
                    total_medicamentos_paciente=len(medicamentos),
                    diagnostico=diagnostico,
                    request_ip=get_client_ip(request),
                    request_user_agent=request.META.get("HTTP_USER_AGENT", ""),
                )
            )

    receta_label = "receta" if len(solicitudes) == 1 else "recetas"

    return JsonResponse(
        {
            "status": "success",
            "message": f"Solicitud recibida. Se generaron {len(solicitudes)} {receta_label} pendientes de aprobacion medica.",
            "solicitud": {
                "id": solicitudes[0].id,
                "estado": solicitudes[0].estado,
            },
            "solicitudes": [
                {
                    "id": solicitud.id,
                    "estado": solicitud.estado,
                    "medicamentos": solicitud.auditoria.get("medicamentos", []),
                }
                for solicitud in solicitudes
            ],
            "paciente": {
                "id": paciente.id,
                "nombre": paciente.nombre,
                "apellido": paciente.apellido,
                "documento": paciente.numDoc,
            },
            "historia": {"id": historia.id},
        }
    )


@csrf_protect
@require_POST
def aprobar_solicitud_receta(request, solicitud_id):
    return _decidir_solicitud_receta(request, solicitud_id, aprobar=True)


@csrf_protect
@require_POST
def rechazar_solicitud_receta(request, solicitud_id):
    return _decidir_solicitud_receta(request, solicitud_id, aprobar=False)


def _espontanea_2_defaults(patient_record: Paciente | None = None) -> dict[str, Any]:
    """Professional defaults plus a patient profile read from the HHCC database."""
    if patient_record is None:
        patient_record = (
            Paciente.objects.select_related("idTipoDoc")
            .filter(numDoc=ESPONTANEA_2_PATIENT_DOCUMENT, apellido__iexact="Bergonzi", deBaja=False)
            .order_by("id")
            .first()
        )
    patient_data = _espontanea_2_patient_data(patient_record)
    patient = patient_data["patient"]
    coverage = patient_data["coverage"]
    profile = load_professional_profile()
    medico_profile = profile["medico"]
    matricula = _profile_section(medico_profile, "matricula")
    sello = _profile_section(medico_profile, "sello")
    firma = _profile_section(medico_profile, "firma")
    logo = _profile_section(medico_profile, "logo")
    consultorio = profile["consultorio"]
    consultorio_domicilio = _profile_section(consultorio, "domicilio")
    signature_base64 = _configured_image_base64(
        resolve_profile_asset(profile, _profile_text(firma, "archivo"))
    )
    logo_base64 = _configured_image_base64(
        resolve_profile_asset(profile, _profile_text(logo, "archivo"))
    )
    registration_type = _profile_text(matricula, "tipo")
    registration_number = _profile_text(matricula, "numero")
    doctor = {
        "name": _profile_text(medico_profile, "nombre"),
        "last_name": _profile_text(medico_profile, "apellido"),
        "specialty": _profile_text(medico_profile, "especialidad"),
        "profession": _profile_text(medico_profile, "profesion"),
        "registration_type": registration_type,
        "registration_number": registration_number,
        "registration_display": _profile_text(
            matricula,
            "display",
            f"{registration_type} {registration_number}".strip(),
        ),
        "seal_line_1": _profile_text(sello, "linea_1"),
        "seal_line_2": _profile_text(sello, "linea_2"),
        "seal_line_3": _profile_text(sello, "linea_3"),
        "signature_configured": bool(signature_base64),
        "logo_configured": bool(logo_base64),
    }
    payload = {
        "pacienteNombre": patient["name"],
        "pacienteApellido": patient["last_name"],
        "pacienteTipoDoc": patient["document_type"],
        "pacienteNroDoc": patient["document"],
        "pacienteSexo": patient["sex"],
        "pacienteFechaNacimiento": patient["birth_date"],
        "pacienteCuil": "",
        "pacienteEmail": patient["email"],
        "pacienteTelefono": patient["phone"],
        "pacienteLocalidad": patient["locality"],
        "pacienteProvincia": patient["province"],
        "pacientePais": "AR",
        "pacienteCalle": patient["street"],
        "pacienteNumero": patient["street_number"],
        "pacienteCodigoPostal": "",
        "idFinanciador": coverage["financier_id"],
        "nroFinanciador": "",
        "planId": coverage["plan_id"],
        "plan": coverage["payload_plan"],
        "afiliadoNumero": coverage["member_number"],
        "dniTitular": patient["document"],
        "medicoNombre": doctor["name"],
        "medicoApellido": doctor["last_name"],
        "medicoTipoDoc": _profile_text(medico_profile, "tipo_documento"),
        "medicoNroDoc": _profile_text(medico_profile, "numero_documento"),
        "medicoSexo": _profile_text(medico_profile, "sexo"),
        "medicoFechaNacimiento": _profile_text(medico_profile, "fecha_nacimiento"),
        "medicoEmail": _profile_text(medico_profile, "email"),
        "medicoTelefono": _profile_text(medico_profile, "telefono"),
        "medicoPais": _profile_text(medico_profile, "pais"),
        "medicoMatriculaTipo": doctor["registration_type"],
        "medicoMatriculaNumero": doctor["registration_number"],
        "medicoMatriculaProvincia": _profile_text(matricula, "provincia"),
        "medicoEspecialidad": doctor["specialty"],
        "medicoProfesion": doctor["profession"],
        "medicoIdTributario": _profile_text(medico_profile, "id_tributario"),
        "medicoIdRefeps": _profile_text(medico_profile, "id_refeps"),
        "medicoFirmaLink": _profile_text(firma, "link"),
        "medicoFirmaBase64": signature_base64,
        "medicoLogoInstitucion": logo_base64,
        "selloLinea1": doctor["seal_line_1"],
        "selloLinea2": doctor["seal_line_2"],
        "selloLinea3": doctor["seal_line_3"],
        "consultorioNombre": _profile_text(consultorio, "nombre"),
        "consultorioCalle": _profile_text(consultorio_domicilio, "calle"),
        "consultorioNumero": _profile_text(consultorio_domicilio, "numero"),
        "consultorioPiso": _profile_text(consultorio_domicilio, "piso"),
        "consultorioDepto": _profile_text(consultorio_domicilio, "depto"),
        "consultorioCodigoPostal": _profile_text(consultorio_domicilio, "codigo_postal"),
        "consultorioLocalidad": _profile_text(consultorio_domicilio, "localidad"),
        "consultorioMunicipio": _profile_text(consultorio_domicilio, "municipio"),
        "consultorioProvincia": _profile_text(consultorio_domicilio, "provincia"),
        "consultorioPais": _profile_text(consultorio_domicilio, "pais"),
        "consultorioContacto": _profile_text(consultorio, "contacto"),
        "consultorioEmail": _profile_text(consultorio, "email"),
        "consultorioLogo": _profile_text(consultorio, "logo"),
    }
    return {"patient": patient, "doctor": doctor, "coverage": coverage, "payload": payload}


def _espontanea_2_patient_data(patient_record: Paciente | None) -> dict[str, Any]:
    if patient_record is None:
        patient = {
            "id": None,
            "name": "",
            "last_name": "",
            "document_type": "",
            "document": "",
            "birth_date": "",
            "sex": "",
            "sex_label": "Sin especificar",
            "email": "",
            "phone": "",
            "street": "",
            "street_number": "",
            "locality": "",
            "province": "",
            "edit_url": "",
        }
        coverage = {
            "name": "Sin cobertura",
            "financier_id": "",
            "plan_id": "",
            "plan": "",
            "payload_plan": "",
            "member_number": "",
            "environment": "HHCC",
            "mapped": False,
        }
        return {"patient": patient, "coverage": coverage, "payload": {}}

    street, street_number = _split_street_address(patient_record.direccion or "")
    local_sex = (patient_record.sexo or "").upper()
    qbi2_sex = "M" if local_sex == "H" else "F" if local_sex == "M" else ""
    sex_label = "Masculino" if qbi2_sex == "M" else "Femenino" if qbi2_sex == "F" else "Sin especificar"
    document_type = (getattr(patient_record.idTipoDoc, "nombre", "") or "DNI").strip()
    raw_plan = (patient_record.plan or "").strip()
    financier_id, plan_id, payload_plan = _qbi2_coverage_mapping(patient_record.obraSocial, raw_plan)

    patient = {
        "id": patient_record.id,
        "name": (patient_record.nombre or "").strip(),
        "last_name": (patient_record.apellido or "").strip(),
        "document_type": document_type,
        "document": (patient_record.numDoc or "").strip(),
        "birth_date": patient_record.fechaNac.isoformat() if patient_record.fechaNac else "",
        "sex": qbi2_sex,
        "sex_label": sex_label,
        "email": (patient_record.mail or "").strip(),
        "phone": (patient_record.celular or patient_record.telefono or "").strip(),
        "street": street,
        "street_number": street_number,
        "locality": (patient_record.localidad or "").strip(),
        "province": "",
        "edit_url": reverse("editar_paciente", args=[patient_record.id]),
    }
    coverage = {
        "name": (patient_record.obraSocial or "").strip() or "Sin cobertura",
        "financier_id": financier_id,
        "plan_id": plan_id,
        "plan": raw_plan,
        "payload_plan": payload_plan,
        "member_number": (patient_record.afiliado or "").strip(),
        "environment": "HHCC",
        "mapped": bool(financier_id),
    }
    payload = {
        "pacienteNombre": patient["name"],
        "pacienteApellido": patient["last_name"],
        "pacienteTipoDoc": patient["document_type"],
        "pacienteNroDoc": patient["document"],
        "pacienteSexo": patient["sex"],
        "pacienteFechaNacimiento": patient["birth_date"],
        "pacienteCuil": "",
        "pacienteEmail": patient["email"],
        "pacienteTelefono": patient["phone"],
        "pacienteLocalidad": patient["locality"],
        "pacienteProvincia": patient["province"],
        "pacientePais": "AR",
        "pacienteCalle": patient["street"],
        "pacienteNumero": patient["street_number"],
        "pacienteCodigoPostal": "",
        "idFinanciador": coverage["financier_id"],
        "nroFinanciador": "",
        "planId": coverage["plan_id"],
        "plan": coverage["payload_plan"],
        "afiliadoNumero": coverage["member_number"],
        "dniTitular": patient["document"],
    }
    return {"patient": patient, "coverage": coverage, "payload": payload}


def _qbi2_coverage_mapping(raw_name: Any, raw_plan: Any) -> tuple[str, str, str]:
    normalized_name = _normalize_identifier(raw_name)
    plan = str(raw_plan or "").strip()
    plan_digits = re.sub(r"\D", "", plan)

    if normalized_name.split(" ", 1)[0:1] == ["OSDE"]:
        plan_ids = {"210": "42", "310": "43", "410": "44", "450": "45", "510": "46"}
        plan_id = plan_ids.get(plan_digits, "")
        return "28", plan_id, f"Plan{plan_digits}" if plan_id else plan
    if normalized_name.replace(" ", "") == "ACCORDSALUD":
        return "96", "", plan
    return "", "", plan


def _normalize_identifier(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").upper())
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", text)).strip()


def _espontanea_2_safe_data(data: dict[str, Any]) -> dict[str, Any]:
    diagnostico = str(data.get("diagnostico") or "").strip()
    if not diagnostico:
        raise ValueError("El diagnóstico es obligatorio.")
    if len(diagnostico) > 255:
        raise ValueError("El diagnóstico no puede superar los 255 caracteres.")
    codigo_diagnostico = str(data.get("codigoDiagnostico") or "").strip()
    try:
        patient_id = int(data.get("pacienteId"))
    except (TypeError, ValueError) as exc:
        raise ValueError("Seleccioná un paciente de la base de historias clínicas.") from exc
    patient_record = (
        Paciente.objects.select_related("idTipoDoc")
        .filter(pk=patient_id, deBaja=False)
        .first()
    )
    if patient_record is None:
        raise ValueError("El paciente seleccionado no existe o está dado de baja.")

    safe_data = {
        "medicamentos": _espontanea_2_safe_medications(data.get("medicamentos", [])),
        # QBI2 resolves a general CIE-10 code to its printable description.
        "diagnostico": codigo_diagnostico or diagnostico,
        "codigoDiagnostico": codigo_diagnostico,
        "imprimirDiagnostico": "S",
        "indicaciones": data.get("indicaciones", ""),
        "observaciones": data.get("observaciones", ""),
        "fechaEmision": _normalize_fecha_emision(data.get("fechaEmision", "")),
        "ocultarPaciente": data.get("ocultarPaciente", False),
    }
    safe_data.update(_espontanea_2_defaults(patient_record)["payload"])
    return safe_data


def _espontanea_2_safe_medications(raw_items: Any) -> list[dict[str, Any]]:
    """Whitelist clinical item fields and keep diagnosis only at recipe level."""
    if not isinstance(raw_items, list):
        raise ValueError("Los medicamentos deben enviarse como una lista.")

    safe_items: list[dict[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            raise ValueError("Cada medicamento debe ser un objeto.")
        safe_items.append(
            {
                "regNo": item.get("regNo", ""),
                "nombreProducto": item.get("nombreProducto", ""),
                "nombreDroga": item.get("nombreDroga", ""),
                "presentacion": item.get("presentacion", ""),
                "cantidad": item.get("cantidad", 1),
                "posologia": item.get("posologia", ""),
                "tratamiento": item.get("tratamiento", 0),
                "permiteSustitucion": item.get("permiteSustitucion", ""),
                "diagnostico": "",
                "codigoDiagnostico": "",
                "forzarDuplicado": False,
            }
        )
    return safe_items


def _redact_profile_images(payload: dict[str, Any]) -> dict[str, Any]:
    redacted = copy.deepcopy(payload)
    medico = redacted.get("medico")
    if not isinstance(medico, dict):
        return redacted
    for key, label in (("firmabase64", "firma PNG configurada"), ("logoInstitucion", "logo PNG configurado")):
        value = medico.get(key)
        if value:
            medico[key] = f"[{label}; {len(value)} caracteres Base64]"
    return redacted


def _normalize_fecha_emision(raw_value: Any) -> str:
    value = str(raw_value or "").strip()
    if not value:
        return ""
    try:
        selected = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("La fecha de emisión debe tener formato AAAA-MM-DD.") from exc
    if selected == timezone.localdate():
        return ""
    return f"{selected.isoformat()}T00:00:00Z"


def _configured_image_base64(raw_path: str) -> str:
    path = Path(raw_path).expanduser() if raw_path else None
    if not path or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
        return ""
    try:
        stat = path.stat()
    except OSError:
        return ""
    return _image_file_base64(str(path.resolve()), stat.st_mtime_ns)


def _profile_section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    return value if isinstance(value, dict) else {}


def _profile_text(data: dict[str, Any], key: str, default: str = "") -> str:
    value = data.get(key, default)
    return str(value if value is not None else "").strip()


@lru_cache(maxsize=8)
def _image_file_base64(path: str, _mtime_ns: int) -> str:
    try:
        return base64.b64encode(Path(path).read_bytes()).decode("ascii")
    except OSError:
        return ""


def _split_street_address(value: str) -> tuple[str, str]:
    match = re.match(r"^\s*(.*?)\s+(\d+[A-Za-z]?)\s*$", value or "")
    if not match:
        return (value or "").strip(), ""
    return match.group(1).strip().title(), match.group(2).strip()


def _positive_int(value: Any, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _qbi2_prefixed_params(request) -> dict[str, Any]:
    return {
        key.removeprefix("qbi2_"): value
        for key, value in request.GET.items()
        if key.startswith("qbi2_") and value not in ("", None)
    }


def _json_body(request) -> dict[str, Any] | JsonResponse:
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        return JsonResponse({"status": "error", "message": f"JSON invalido: {exc}"}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"status": "error", "message": "El cuerpo debe ser un objeto JSON."}, status=400)
    return data


def _selected_medications_from_portal_data(data):
    try:
        medicamentos = json.loads(data.get("medicamentosJson") or "[]")
        if not isinstance(medicamentos, list):
            medicamentos = []
    except json.JSONDecodeError:
        medicamentos = []

    selected = []
    seen = set()
    for item in medicamentos[:10]:
        if not isinstance(item, dict):
            continue
        medicamento = _complete_medication_from_portal_data(item)
        reg_no = (medicamento.get("regNo") or "").strip()
        if not reg_no or reg_no in seen:
            continue
        selected.append(medicamento)
        seen.add(reg_no)

    if selected:
        return selected

    medicamento = _selected_medication_from_portal_data(data)
    return [medicamento] if (medicamento.get("regNo") or "").strip() else []


def _selected_medication_from_portal_data(data):
    try:
        medicamento = json.loads(data.get("medicamentoJson") or "{}")
        if not isinstance(medicamento, dict):
            medicamento = {}
    except json.JSONDecodeError:
        medicamento = {}

    return _complete_medication_from_portal_data(medicamento, data)


def _complete_medication_from_portal_data(medicamento, data=None):
    data = data or {}
    fallback = {
        "regNo": data.get("regNo", ""),
        "nombreProducto": data.get("nombreProducto", ""),
        "nombreDroga": data.get("nombreDroga", ""),
        "presentacion": data.get("presentacion", ""),
    }
    for key, value in fallback.items():
        medicamento[key] = medicamento.get(key) or value
    return medicamento


def _chunks(items, size):
    for index in range(0, len(items), size):
        yield items[index:index + size]


def _decidir_solicitud_receta(request, solicitud_id, *, aprobar):
    observacion = request.POST.get("observacion_medico", "")
    next_url = request.POST.get("next") or "/qbi2-poc/medico/solicitudes/"
    diagnostico = (request.POST.get("diagnostico") or "").strip()
    posologia = (request.POST.get("posologia") or "Tomar segun indicacion medica.").strip()
    cantidad = int(request.POST.get("cantidad") or 1)
    tratamiento = int(request.POST.get("tratamiento") or 0)

    if aprobar and not diagnostico:
        messages.error(request, "El diagnostico es obligatorio para emitir la receta.")
        return HttpResponseRedirect(next_url)

    with transaction.atomic():
        solicitud = SolicitudReceta.objects.select_for_update().get(pk=solicitud_id)
        if solicitud.estado != SolicitudReceta.Estado.PENDIENTE:
            return HttpResponseRedirect(next_url)
        if aprobar:
            _emitir_solicitud_receta(
                solicitud,
                request.user,
                diagnostico=diagnostico,
                posologia=posologia,
                cantidad=cantidad,
                tratamiento=tratamiento,
                observacion=observacion,
            )
        else:
            solicitud.rechazar(request.user, observacion=observacion)
    return HttpResponseRedirect(next_url)


def _emitir_solicitud_receta(
    solicitud,
    user,
    *,
    diagnostico,
    posologia,
    cantidad,
    tratamiento,
    observacion="",
):
    payload = build_receta_payload_from_solicitud(
        solicitud,
        diagnostico=diagnostico,
        posologia=posologia,
        cantidad=cantidad,
        tratamiento=tratamiento,
    )
    try:
        result = emitir_receta_payload(payload)
    except Qbi2ConfigurationError as exc:
        solicitud.marcar_error_emision(
            user,
            diagnostico=diagnostico,
            posologia=posologia,
            observacion=observacion,
            payload=payload,
            error=str(exc),
        )
        return
    except Qbi2HTTPError as exc:
        solicitud.marcar_error_emision(
            user,
            diagnostico=diagnostico,
            posologia=posologia,
            observacion=observacion,
            payload=payload,
            response=exc.payload,
            error=str(exc),
        )
        return

    summary = summarize_receta_response(result.response)
    pdf_url = summary.get("s3Link")
    if pdf_url:
        solicitud.marcar_emitida(
            user,
            diagnostico=diagnostico,
            posologia=posologia,
            observacion=observacion,
            payload=result.payload,
            response=result.response,
            summary=summary,
        )
        return

    provider_errors = summary.get("errores") or "Qbi2 no devolvio PDF de receta."
    solicitud.marcar_error_emision(
        user,
        diagnostico=diagnostico,
        posologia=posologia,
        observacion=observacion,
        payload=result.payload,
        response=result.response,
        error=str(provider_errors),
    )
