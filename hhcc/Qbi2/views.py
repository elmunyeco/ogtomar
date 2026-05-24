import json

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.db import transaction
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from .client import Qbi2ConfigurationError, Qbi2HTTPError
from .models import SolicitudReceta
from .portal import create_prescription_request, find_patient_history, get_client_ip
from .recipes import build_hml_receta_poc_payload, build_receta_payload_from_solicitud, emitir_receta_payload, summarize_receta_response
from .services import VademecumService


def vademecum_page(request):
    return render(request, "Qbi2/vademecum.html")


def receta_poc_page(request):
    payload = build_hml_receta_poc_payload(nro_doc="99999999")
    return render(request, "Qbi2/receta_poc.html", {"payload": payload})


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
    from django.conf import settings

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
def buscar_vademecum(request):
    return _buscar_vademecum_response(request)


@require_GET
def buscar_vademecum_portal(request):
    return _buscar_vademecum_response(request)


def _buscar_vademecum_response(request):
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


@csrf_protect
@require_POST
def aprobar_solicitud_receta(request, solicitud_id):
    return _decidir_solicitud_receta(request, solicitud_id, aprobar=True)


@csrf_protect
@require_POST
def rechazar_solicitud_receta(request, solicitud_id):
    return _decidir_solicitud_receta(request, solicitud_id, aprobar=False)


def _decidir_solicitud_receta(request, solicitud_id, *, aprobar):
    observacion = request.POST.get("observacion_medico", "")
    next_url = request.POST.get("next") or "/receta-poc/solicitudes/"
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
