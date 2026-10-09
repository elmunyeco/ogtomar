import base64
import copy
import json
import re
import uuid
from collections import Counter
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Max, Min, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from .client import (
    Qbi2ConfigurationError,
    Qbi2HTTPError,
    qbi2_error_details,
    qbi2_error_text,
)
from .limits import recipe_medication_limits, validate_recipe_medication_count
from .models import EmisionSolicitudReceta, SolicitudReceta
from .history_filters import filter_history, history_range
from .notifications import (
    PrescriptionNotificationError,
    build_prescription_email_draft,
    download_prescription_pdf,
    prescription_draft_filename,
)
from .portal import (
    clear_patient_login_failures,
    create_prescription_request,
    end_patient_session,
    find_patient_history,
    get_client_ip,
    get_patient_from_session,
    patient_portal_eligibility,
    patient_login_is_blocked,
    register_patient_login_failure,
    start_patient_session,
)
from .professional_profile import (
    load_patient_portal_policy,
    load_professional_profile,
    resolve_profile_asset,
)
from .rcta import build_rcta_payload, emit_rcta_payload, summarize_receta_response
from .services import DiagnosticoService, FinanciadorService, VademecumService
from main.forms import PacientePortalForm
from main.models import Paciente


@ensure_csrf_cookie
def receta_medico_page(request):
    defaults = _receta_defaults()
    medication_limits = recipe_medication_limits()
    return render(
        request,
        "Qbi2/receta_medico.html",
        {
            "patient": defaults["patient"],
            "doctor": defaults["doctor"],
            "coverage": defaults["coverage"],
            "initial_patient": {
                "patient": defaults["patient"],
                "coverage": defaults["coverage"],
            },
            "today": timezone.localdate().isoformat(),
            "medication_limits": medication_limits,
            "pending_count": SolicitudReceta.objects.filter(estado=SolicitudReceta.Estado.PENDIENTE).count(),
        },
    )


@ensure_csrf_cookie
def paciente_login_page(request):
    paciente = get_patient_from_session(request)
    if paciente:
        return redirect("recetas:paciente_receta_nueva")

    error = ""
    documento = ""
    apellido = ""
    if request.method == "POST":
        documento = request.POST.get("documento", "")
        apellido = request.POST.get("apellido", "")
        block_minutes = int(getattr(settings, "QBI2_PATIENT_LOGIN_BLOCK_MINUTES", 10))
        if patient_login_is_blocked(documento):
            error = f"Demasiados intentos. Volvé a intentar en {block_minutes} minutos."
        else:
            paciente, _ = find_patient_history(apellido=apellido, documento=documento)
            if paciente:
                clear_patient_login_failures(documento)
                start_patient_session(request, paciente)
                return redirect("recetas:paciente_receta_nueva")
            if register_patient_login_failure(documento):
                error = f"Demasiados intentos. Volvé a intentar en {block_minutes} minutos."
            else:
                error = "Los datos ingresados no coinciden con un paciente activo."

    return render(
        request,
        "Qbi2/pacientes_login.html",
        {"error": error, "documento": documento, "apellido": apellido},
    )


@require_POST
def paciente_logout(request):
    end_patient_session(request)
    return redirect("recetas:paciente_login")


@ensure_csrf_cookie
def pacientes_portal_page(request):
    paciente = get_patient_from_session(request)
    if not paciente:
        return redirect("recetas:paciente_login")
    eligibility = _patient_portal_status(paciente)
    return render(
        request,
        "Qbi2/pacientes_portal.html",
        {
            "paciente": paciente,
            "perfil_form": PacientePortalForm(instance=paciente),
            "medication_limits": recipe_medication_limits(),
            "eligibility": eligibility,
        },
    )


def solicitudes_receta_page(request):
    # Consume unrelated flash notices so editing a patient does not pollute history.
    operation_errors = [
        message for message in messages.get_messages(request)
        if message.extra_tags == "recipe_validation" and request.GET.get("resultado")
    ]
    medication_limits = recipe_medication_limits()
    estado = request.GET.get("estado") or SolicitudReceta.Estado.PENDIENTE
    estados_validos = {choice[0] for choice in SolicitudReceta.Estado.choices}
    base_queryset = SolicitudReceta.objects.select_related(
        "paciente", "historia_clinica", "aprobado_por"
    ).prefetch_related("emisiones").filter(hidden_from_history_at__isnull=True)
    date_filter = history_range(request.GET)
    queryset = filter_history(base_queryset, date_filter)
    if estado != "todas" and estado in estados_validos:
        queryset = queryset.filter(estado=estado)
    elif estado != "todas":
        estado = SolicitudReceta.Estado.PENDIENTE
        queryset = queryset.filter(estado=estado)

    filter_params = {
        "modo": date_filter["mode"], "periodo": date_filter["period"],
        "desde": date_filter["start_text"], "hasta": date_filter["end_text"],
    }
    pending_query = urlencode({**filter_params, "estado": "pendiente"})
    history_query = urlencode({**filter_params, "estado": "todas"})
    current_query = urlencode({**filter_params, "estado": estado})
    page = Paginator(queryset, 20).get_page(request.GET.get("pagina"))
    solicitudes = list(page.object_list)
    pending = base_queryset.filter(estado=SolicitudReceta.Estado.PENDIENTE)
    pending_in_range = filter_history(pending, date_filter).count()
    pending_summary = pending.aggregate(total=Count("pk"), first=Min("created_at"), last=Max("created_at"))
    pending_outside = pending_summary["total"] - pending_in_range
    all_pending_query = ""
    if pending_outside:
        first_date = timezone.localtime(pending_summary["first"]).date()
        last_date = timezone.localtime(pending_summary["last"]).date()
        all_pending_query = urlencode({
            "estado": "pendiente", "modo": "fechas",
            "desde": first_date.isoformat(), "hasta": last_date.isoformat(),
        })
    for solicitud in solicitudes:
        medicamentos = solicitud.auditoria.get("medicamentos") or [
            {
                "regNo": solicitud.medicamento_reg_no,
                "nombreProducto": solicitud.medicamento_nombre_producto,
                "nombreDroga": solicitud.medicamento_nombre_droga,
                "presentacion": solicitud.medicamento_presentacion,
            }
        ]
        solicitud.medicamentos_json = json.dumps(
            medicamentos[:medication_limits.max_medications],
            ensure_ascii=False,
        )
        solicitud.error_detalle = qbi2_error_details(
            solicitud.respuesta_qbi2,
            fallback=solicitud.error_qbi2,
        )
        solicitud.tiene_documentos_emitidos = any(
            emision.estado == EmisionSolicitudReceta.Estado.EMITIDA
            for emision in solicitud.emisiones.all()
        )

    resultado_solicitud = None
    try:
        resultado_id = int(request.GET.get("resultado") or 0)
    except (TypeError, ValueError):
        resultado_id = 0
    if resultado_id > 0:
        resultado_solicitud = base_queryset.filter(pk=resultado_id).first()
        if resultado_solicitud:
            resultado_solicitud.error_detalle = qbi2_error_details(
                resultado_solicitud.respuesta_qbi2,
                fallback=resultado_solicitud.error_qbi2,
            )
            resultado_solicitud.tiene_documentos_emitidos = any(
                emision.estado == EmisionSolicitudReceta.Estado.EMITIDA
                for emision in resultado_solicitud.emisiones.all()
            )

    return render(
        request,
        "Qbi2/solicitudes_receta.html",
        {
            "solicitudes": solicitudes,
            "operation_errors": operation_errors,
            "is_queue": True,
            "estado": estado,
            "date_filter": date_filter,
            "pending_count": pending_in_range,
            "pending_outside": pending_outside,
            "all_pending_query": all_pending_query,
            "pending_query": pending_query,
            "history_query": history_query,
            "current_query": current_query,
            "return_url": f'{reverse("recetas:medico_solicitudes")}?{current_query}&pagina={page.number}',
            "page": page,
            "state_choices": SolicitudReceta.Estado.choices,
            "estados": SolicitudReceta.Estado,
            "resultado_solicitud": resultado_solicitud,
            "medication_limits": medication_limits,
        },
    )


@require_GET
def buscar_vademecum_portal(request):
    paciente = get_patient_from_session(request)
    if not paciente:
        return _patient_api_auth_error()
    eligibility_error = _patient_request_eligibility_error(
        paciente,
        require_canonical_coverage=False,
    )
    if eligibility_error is not None:
        return eligibility_error
    query = request.GET.get("q") or request.GET.get("query") or ""
    start_page = _positive_int(request.GET.get("scanPage"), default=1)
    try:
        result = VademecumService().buscar_relevante(
            query,
            start_page=start_page,
            extra_params=_qbi2_prefixed_params(request),
        )
    except ValidationError as exc:
        return JsonResponse({"status": "error", "message": "; ".join(exc.messages)}, status=400)
    except Qbi2ConfigurationError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=503)
    except Qbi2HTTPError as exc:
        return JsonResponse(
            {
                "status": "error",
                "message": qbi2_error_text(
                    exc.payload,
                    fallback=str(exc),
                    status_code=exc.status_code,
                ),
                "provider_status": exc.status_code,
                "provider_payload": exc.payload,
            },
            status=502,
        )
    return JsonResponse(
        {
            "status": "success",
            "query": result["query"],
            "count": len(result["items"]),
            "pageInfo": result["page_info"],
            "items": result["items"],
        }
    )


@require_GET
def buscar_financiadores_portal(request):
    if not get_patient_from_session(request):
        return _patient_api_auth_error()
    return _financier_catalog_response(request)


def _financier_catalog_response(request):
    try:
        result = FinanciadorService().listar(
            request.GET.get("q", ""),
            financier_id=request.GET.get("id"),
        )
    except ValidationError as exc:
        return JsonResponse({"status": "error", "message": "; ".join(exc.messages)}, status=400)
    except Qbi2ConfigurationError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=503)
    except Qbi2HTTPError as exc:
        return JsonResponse(
            {
                "status": "error",
                "message": qbi2_error_text(exc.payload, fallback=str(exc), status_code=exc.status_code),
                "provider_status": exc.status_code,
                "provider_payload": exc.payload,
            },
            status=502,
        )
    return JsonResponse({"status": "success", "count": len(result["items"]), "items": result["items"]})


@require_GET
def catalogo_api(request, catalogo):
    query = request.GET.get("q", "")
    page = _positive_int(request.GET.get("page"), default=1)
    try:
        if catalogo == "medicamentos":
            start_page = _positive_int(request.GET.get("scanPage"), default=page)
            result = VademecumService().buscar_relevante(
                query,
                start_page=start_page,
                extra_params=_qbi2_prefixed_params(request),
            )
        elif catalogo == "diagnosticos":
            result = DiagnosticoService().buscar(
                query,
                extra_params=_qbi2_prefixed_params(request),
            )
        elif catalogo == "financiadores":
            return _financier_catalog_response(request)
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
                "message": qbi2_error_text(
                    exc.payload,
                    fallback=str(exc),
                    status_code=exc.status_code,
                ),
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
def receta_pacientes_api(request):
    """Search active HHCC patients and expose only fields needed by the recipe selector."""
    raw_patient_id = str(request.GET.get("id") or "").strip()
    query = str(request.GET.get("q") or "").strip()
    if raw_patient_id:
        try:
            patient_id = int(raw_patient_id)
        except ValueError:
            return JsonResponse({"status": "error", "message": "El ID de paciente no es válido."}, status=400)
        patients = Paciente.objects.select_related("idTipoDoc").filter(pk=patient_id, deBaja=False)
    else:
        patients_or_response = _search_recipe_patients(query)
        if isinstance(patients_or_response, JsonResponse):
            return patients_or_response
        patients = patients_or_response

    items = []
    for patient_record in patients:
        patient_data = _recipe_patient_data(patient_record)
        items.append(
            {
                "patient": patient_data["patient"],
                "coverage": patient_data["coverage"],
            }
        )
    return JsonResponse({"status": "success", "count": len(items), "items": items})


def _search_recipe_patients(query: str):
    compact_query = re.sub(r"[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", "", query)
    if len(compact_query) < 3:
        return JsonResponse(
            {"status": "error", "message": "Ingresar al menos 3 caracteres para buscar un paciente."},
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

    return (
        Paciente.objects.select_related("idTipoDoc")
        .filter(filters, deBaja=False)
        .order_by("apellido", "nombre", "id")[:12]
    )


@csrf_protect
@require_POST
def receta_preview_api(request):
    """Build the simplified recipe payload without making a QBI2 write request."""
    data_or_response = _json_body(request)
    if isinstance(data_or_response, JsonResponse):
        return data_or_response

    try:
        safe_data = _safe_recipe_data(data_or_response)
        endpoint, payload = build_rcta_payload(safe_data)
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
def receta_emit_api(request):
    """Persist and emit from the simplified medical client exactly once."""
    data_or_response = _json_body(request)
    if isinstance(data_or_response, JsonResponse):
        return data_or_response

    try:
        safe_data = _safe_recipe_data(data_or_response)
        client_request_id = _client_request_id(data_or_response.get("clientRequestId"))
    except (TypeError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)

    previous = SolicitudReceta.objects.prefetch_related("emisiones").filter(
        client_request_id=client_request_id
    ).first()
    if previous:
        return _spontaneous_emission_response(previous, replayed=True)

    patient = Paciente.objects.filter(pk=data_or_response.get("pacienteId"), deBaja=False).first()
    historia = patient.historias_clinicas.order_by("-fechaAlta", "-id").first() if patient else None
    if not patient or not historia:
        return JsonResponse(
            {"status": "error", "message": "El paciente debe tener una historia clínica activa."},
            status=400,
        )

    first_medication = safe_data["medicamentos"][0]
    try:
        with transaction.atomic():
            solicitud = SolicitudReceta.objects.create(
                paciente=patient,
                historia_clinica=historia,
                client_request_id=client_request_id,
                medicamento_reg_no=str(first_medication.get("regNo") or "").strip(),
                medicamento_nombre_producto=str(first_medication.get("nombreProducto") or "").strip(),
                medicamento_nombre_droga=str(first_medication.get("nombreDroga") or "").strip(),
                medicamento_presentacion=str(first_medication.get("presentacion") or "").strip(),
                diagnostico=str(data_or_response.get("diagnostico") or "").strip(),
                request_ip=get_client_ip(request),
                request_user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000],
                auditoria={
                    "source": "emision-medica-espontanea",
                    "medicamento": first_medication,
                    "medicamentos": safe_data["medicamentos"],
                },
            )
    except IntegrityError:
        # A concurrent request with the same key must reuse the first attempt.
        previous = SolicitudReceta.objects.prefetch_related("emisiones").filter(
            client_request_id=client_request_id
        ).first()
        if previous:
            return _spontaneous_emission_response(previous, replayed=True)
        raise

    outcome = _perform_rcta_emission(
        solicitud,
        request.user,
        recipe_data=safe_data,
        diagnostico=str(data_or_response.get("diagnostico") or "").strip(),
        posologia="",
        observacion=str(data_or_response.get("observaciones") or "").strip(),
    )
    return _spontaneous_emission_response(
        solicitud,
        result=outcome.get("result"),
        provider_status=outcome.get("provider_status"),
    )


def _client_request_id(raw_value):
    value = str(raw_value or "").strip() or str(uuid.uuid4())
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{8,64}", value):
        raise ValueError("La clave de la operación no es válida.")
    return value


def _spontaneous_emission_response(solicitud, *, result=None, provider_status=None, replayed=False):
    response = solicitud.respuesta_qbi2 if isinstance(solicitud.respuesta_qbi2, dict) else {}
    summary = result.summary if result is not None else summarize_receta_response(response)
    endpoint = result.endpoint if result is not None else "/apirecipe/Receta"
    payload = result.payload if result is not None else solicitud.payload_qbi2
    base = {
        "operation": "receta",
        "endpoint": endpoint,
        "payload": _redact_profile_images(payload or {}),
        "summary": summary,
        "response": response,
        "request_id": solicitud.client_request_id,
        "replayed": replayed,
        "solicitud": {"id": solicitud.id, "estado": solicitud.estado},
    }
    if solicitud.estado == SolicitudReceta.Estado.EMITIDA:
        return JsonResponse({"status": "success", **base})

    has_documents = solicitud.emisiones.filter(
        estado=EmisionSolicitudReceta.Estado.EMITIDA
    ).exists()
    base.update(
        {
            "status": "partial" if has_documents else "error",
            "message": solicitud.error_qbi2 or "No se pudo emitir la receta.",
            "provider_status": provider_status,
            "provider_payload": response,
        }
    )
    return JsonResponse(base, status=409 if has_documents or replayed else 502)
@csrf_protect
@require_POST
def validar_paciente_portal(request):
    paciente = get_patient_from_session(request)
    if not paciente:
        return _patient_api_auth_error()

    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Datos invalidos."}, status=400)

    use_coverage = _uses_recipe_coverage(data.get("usarCobertura", True))
    eligibility_error = _patient_request_eligibility_error(
        paciente,
        require_canonical_coverage=use_coverage,
    )
    if eligibility_error is not None:
        return eligibility_error

    historia = paciente.historias_clinicas.order_by("-fechaAlta", "-id").first()
    if not historia:
        return JsonResponse({"status": "rejected", "message": "No tenes Historia Clinica"}, status=404)

    medicamentos = _selected_medications_from_portal_data(data)
    try:
        validate_recipe_medication_count(len(medicamentos))
    except ValueError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    with transaction.atomic():
        solicitud = create_prescription_request(
            paciente,
            historia,
            medicamentos[0],
            medicamentos=medicamentos,
            total_medicamentos_paciente=len(medicamentos),
            diagnostico="",
            use_coverage=use_coverage,
            request_ip=get_client_ip(request),
            request_user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

    return JsonResponse(
        {
            "status": "success",
            "message": "Solicitud recibida. El médico revisará el pedido completo antes de emitir.",
            "solicitud": {
                "id": solicitud.id,
                "estado": solicitud.estado,
            },
            "solicitudes": [
                {
                    "id": solicitud.id,
                    "estado": solicitud.estado,
                    "medicamentos": solicitud.auditoria.get("medicamentos", []),
                }
            ],
        }
    )


@csrf_protect
@require_POST
def actualizar_perfil_paciente(request):
    paciente = get_patient_from_session(request)
    if not paciente:
        return _patient_api_auth_error()

    form = PacientePortalForm(request.POST, instance=paciente)
    if not form.is_valid():
        first_error = next(
            (str(error) for errors in form.errors.values() for error in errors),
            "Revisar los datos ingresados.",
        )
        return JsonResponse(
            {
                "status": "error",
                "message": first_error,
                "errors": {field: list(errors) for field, errors in form.errors.items()},
            },
            status=400,
        )
    form.save()
    return JsonResponse({"status": "success", "message": "Tus datos se actualizaron correctamente."})


def _patient_portal_status(paciente, *, use_coverage=True):
    try:
        policy = load_patient_portal_policy()
        return patient_portal_eligibility(
            paciente,
            max_attention_age_years=policy["max_attention_age_years"],
            use_coverage=use_coverage,
        )
    except Qbi2ConfigurationError:
        return {
            "can_request": False, "configuration_error": True,
            "blockers": [{"code": "portal_unavailable", "message": "El portal tiene un problema de configuración y no puede recibir pedidos. Contactá al consultorio."}],
        }


@require_GET
def paciente_habilitacion_api(request):
    paciente = get_patient_from_session(request)
    if not paciente:
        return _patient_api_auth_error()
    eligibility = _patient_portal_status(paciente, use_coverage=_uses_recipe_coverage(request.GET.get("usarCobertura", "true")))
    response = JsonResponse({"status": "success", "eligibility": eligibility})
    response["Cache-Control"] = "no-store"
    return response


def _patient_request_eligibility_error(paciente, *, require_canonical_coverage=True):
    eligibility = _patient_portal_status(paciente, use_coverage=require_canonical_coverage)
    blockers = eligibility["blockers"]
    if blockers:
        status_code = 503 if eligibility.get("configuration_error") else (403 if eligibility.get("attention_expired") else 409)
        return JsonResponse({
            "status": "error", "code": blockers[0]["code"],
            "message": "\n".join(item["message"] for item in blockers),
            "eligibility": eligibility,
        }, status=status_code)
    return None


@csrf_protect
@require_POST
def aprobar_solicitud_receta(request, solicitud_id):
    return _decidir_solicitud_receta(request, solicitud_id, aprobar=True)


@csrf_protect
@require_POST
def rechazar_solicitud_receta(request, solicitud_id):
    return _decidir_solicitud_receta(request, solicitud_id, aprobar=False)


@csrf_protect
@require_POST
def quitar_error_historial(request, solicitud_id):
    with transaction.atomic():
        solicitud = get_object_or_404(
            SolicitudReceta.objects.select_for_update(), pk=solicitud_id,
        )
        if solicitud.estado != SolicitudReceta.Estado.ERROR_EMISION:
            return HttpResponse("Sólo se pueden quitar del historial las recetas con error.", status=409)
        if solicitud.hidden_from_history_at is None:
            solicitud.hidden_from_history_at = timezone.now()
            solicitud.auditoria = {
                **solicitud.auditoria,
                "history_removed_by": request.user.pk,
            }
            solicitud.save(update_fields=["hidden_from_history_at", "auditoria", "updated_at"])
    messages.success(request, f"La solicitud #{solicitud.id} se quitó del historial.")
    # Reuse the allowlisted local return path, without redisplaying the removed item.
    target = _solicitudes_result_url(request.POST.get("next", "?estado=error_emision"), solicitud.id)
    query = dict(parse_qsl(urlsplit(target).query))
    query.pop("resultado", None)
    return HttpResponseRedirect(f'{reverse("recetas:medico_solicitudes")}?{urlencode(query)}')


@csrf_protect
@require_POST
def reabrir_solicitud_receta(request, solicitud_id):
    with transaction.atomic():
        solicitud = get_object_or_404(
            SolicitudReceta.objects.select_for_update(),
            pk=solicitud_id,
        )
        if not solicitud.reabrir_para_reintento(request.user):
            messages.error(
                request,
                f"La solicitud #{solicitud.id} no está en estado de error y no fue modificada.",
            )
            return redirect("recetas:medico_solicitudes")

    messages.success(
        request,
        f"La solicitud #{solicitud.id} volvió a Pendientes. Corregir los datos necesarios y revisar antes de emitir.",
    )
    return HttpResponseRedirect(
        f'{reverse("recetas:medico_solicitudes")}?estado=pendiente#solicitud-{solicitud.id}'
    )


@require_GET
def preparar_correo_receta(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudReceta.objects.select_related("paciente").prefetch_related("emisiones"),
        pk=solicitud_id,
        estado=SolicitudReceta.Estado.EMITIDA,
    )
    emisiones = [
        emision
        for emision in solicitud.emisiones.all()
        if emision.estado == EmisionSolicitudReceta.Estado.EMITIDA
        and emision.qbi2_pdf_url
    ]
    pdf_sources = [
        (
            emision.qbi2_id_receta or f"{solicitud.pk}-{emision.orden}",
            emision.qbi2_pdf_url,
        )
        for emision in emisiones
    ]
    if not pdf_sources and solicitud.qbi2_pdf_url:
        pdf_sources = [(solicitud.qbi2_id_receta or solicitud.pk, solicitud.qbi2_pdf_url)]
    if not pdf_sources:
        return HttpResponse("La receta emitida no tiene un PDF disponible.", status=409)

    try:
        pdfs = [
            (identifier, download_prescription_pdf(pdf_url))
            for identifier, pdf_url in pdf_sources
        ]
    except PrescriptionNotificationError as exc:
        return HttpResponse(str(exc), status=502)

    draft = build_prescription_email_draft(solicitud, pdfs)
    response = HttpResponse(draft, content_type="message/rfc822")
    response["Content-Disposition"] = (
        f'attachment; filename="{prescription_draft_filename(solicitud)}"'
    )
    return response


def _receta_defaults(patient_record: Paciente | None = None) -> dict[str, Any]:
    """Professional defaults plus a patient profile read from the HHCC database."""
    patient_data = _recipe_patient_data(patient_record)
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


def _recipe_patient_data(patient_record: Paciente | None) -> dict[str, Any]:
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
        }
        return {"patient": patient, "coverage": coverage, "payload": {}}

    street, street_number = _split_street_address(patient_record.direccion or "")
    local_sex = (patient_record.sexo or "").upper()
    qbi2_sex = "M" if local_sex == "H" else "F" if local_sex == "M" else ""
    sex_label = "Masculino" if qbi2_sex == "M" else "Femenino" if qbi2_sex == "F" else "Sin especificar"
    document_type = (getattr(patient_record.idTipoDoc, "nombre", "") or "DNI").strip()
    raw_plan = (patient_record.plan or "").strip()

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
        "financier_id": patient_record.qbi2_financiador_id or "",
        "plan_id": patient_record.qbi2_plan_id or "",
        "plan": raw_plan,
        "payload_plan": raw_plan,
        "member_number": (patient_record.afiliado or "").strip(),
        "environment": "HHCC",
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


def _safe_recipe_data(data: dict[str, Any]) -> dict[str, Any]:
    diagnostico = str(data.get("diagnostico") or "").strip()
    if not diagnostico:
        raise ValueError("El diagnóstico es obligatorio.")
    if len(diagnostico) > 255:
        raise ValueError("El diagnóstico no puede superar los 255 caracteres.")
    codigo_diagnostico = str(data.get("codigoDiagnostico") or "").strip()
    try:
        patient_id = int(data.get("pacienteId"))
    except (TypeError, ValueError) as exc:
        raise ValueError("Seleccionar un paciente de la base de historias clínicas.") from exc
    patient_record = (
        Paciente.objects.select_related("idTipoDoc")
        .filter(pk=patient_id, deBaja=False)
        .first()
    )
    if patient_record is None:
        raise ValueError("El paciente seleccionado no existe o está dado de baja.")

    safe_data = {
        "medicamentos": _safe_recipe_medications(data.get("medicamentos", [])),
        # QBI2 resolves a general CIE-10 code to its printable description.
        "diagnostico": codigo_diagnostico or diagnostico,
        "codigoDiagnostico": codigo_diagnostico,
        "imprimirDiagnostico": "S",
        "indicaciones": data.get("indicaciones", ""),
        "observaciones": data.get("observaciones", ""),
        "fechaEmision": _normalize_fecha_emision(data.get("fechaEmision", "")),
        "ocultarPaciente": data.get("ocultarPaciente", False),
    }
    patient_payload = _receta_defaults(patient_record)["payload"]
    if not _uses_recipe_coverage(data.get("usarCobertura", True)):
        for field in (
            "idFinanciador",
            "nroFinanciador",
            "planId",
            "plan",
            "afiliadoNumero",
            "dniTitular",
        ):
            patient_payload.pop(field, None)
    safe_data.update(patient_payload)
    return safe_data


def _uses_recipe_coverage(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return True
    return str(value).strip().lower() in {"1", "true", "t", "yes", "s", "si", "on"}


def _safe_recipe_medications(raw_items: Any) -> list[dict[str, Any]]:
    """Whitelist clinical item fields and keep diagnosis only at recipe level."""
    if not isinstance(raw_items, list):
        raise ValueError("Los medicamentos deben enviarse como una lista.")
    validate_recipe_medication_count(len(raw_items))

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


def _recipe_data_from_solicitud(
    solicitud: SolicitudReceta,
    *,
    diagnostico: str,
    posologia: str,
    cantidad: int,
    tratamiento: int,
    medicamentos: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Adapt a patient request to the same server-owned input used by the medical form."""
    auditoria = solicitud.auditoria if isinstance(solicitud.auditoria, dict) else {}
    raw_medications = medicamentos or auditoria.get("medicamentos")
    if not isinstance(raw_medications, list) or not raw_medications:
        raw_medications = [
            {
                "regNo": solicitud.medicamento_reg_no,
                "nombreProducto": solicitud.medicamento_nombre_producto,
                "nombreDroga": solicitud.medicamento_nombre_droga,
                "presentacion": solicitud.medicamento_presentacion,
            }
        ]

    medications = [
        {
            "regNo": item.get("regNo", ""),
            "nombreProducto": item.get("nombreProducto", ""),
            "nombreDroga": item.get("nombreDroga", ""),
            "presentacion": item.get("presentacion", ""),
            "cantidad": cantidad,
            "posologia": posologia,
            "tratamiento": tratamiento,
        }
        for item in raw_medications
        if isinstance(item, dict)
    ]
    return _safe_recipe_data(
        {
            "pacienteId": solicitud.paciente_id,
            "usarCobertura": auditoria.get("usar_cobertura", True),
            "diagnostico": diagnostico,
            "medicamentos": medications,
        }
    )


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
    for item in medicamentos:
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


def _patient_api_auth_error():
    return JsonResponse(
        {"status": "error", "message": "Tu sesión venció. Volvé a ingresar."},
        status=401,
    )


def _solicitudes_result_url(next_url, solicitud_id):
    """Return to the selected tray while keeping the attempted request visible."""
    valid_states = {choice[0] for choice in SolicitudReceta.Estado.choices} | {"todas"}
    query = dict(parse_qsl(urlsplit(next_url).query))
    estado = query.get("estado")
    if estado not in valid_states:
        estado = SolicitudReceta.Estado.PENDIENTE
    preserved = {key: query[key] for key in ("modo", "periodo", "desde", "hasta", "pagina") if key in query}
    return (
        f'{reverse("recetas:medico_solicitudes")}?'
        f'{urlencode({**preserved, "estado": estado, "resultado": solicitud_id})}'
        "#resultado-emision"
    )


def _decidir_solicitud_receta(request, solicitud_id, *, aprobar):
    observacion = request.POST.get("observacion_medico", "")
    next_url = request.POST.get("next") or "/recetas/medico/solicitudes/"
    diagnostico = (request.POST.get("diagnostico") or "").strip()
    posologia = (request.POST.get("posologia") or "Tomar segun indicacion medica.").strip()
    cantidad = _positive_int(request.POST.get("cantidad"), default=1)
    try:
        tratamiento = max(0, int(request.POST.get("tratamiento") or 0))
    except (TypeError, ValueError):
        tratamiento = 0
    medicamentos = None
    if aprobar and "medicamentosJson" in request.POST:
        medicamentos = _selected_medications_from_portal_data(request.POST)
        try:
            validate_recipe_medication_count(len(medicamentos))
        except ValueError as exc:
            messages.error(request, str(exc), extra_tags="recipe_validation")
            return HttpResponseRedirect(_solicitudes_result_url(next_url, solicitud_id))

    if aprobar and not diagnostico:
        messages.error(request, "El diagnostico es obligatorio para emitir la receta.", extra_tags="recipe_validation")
        return HttpResponseRedirect(_solicitudes_result_url(next_url, solicitud_id))

    with transaction.atomic():
        solicitud = SolicitudReceta.objects.select_for_update().get(pk=solicitud_id)
        if solicitud.estado != SolicitudReceta.Estado.PENDIENTE:
            messages.error(
                request,
                f"La solicitud #{solicitud.id} ya no está pendiente y no fue procesada nuevamente.",
                extra_tags="recipe_validation",
            )
            return HttpResponseRedirect(_solicitudes_result_url(next_url, solicitud.id))
        if aprobar:
            if medicamentos is not None:
                medicamento = medicamentos[0]
                auditoria = dict(solicitud.auditoria or {})
                auditoria["medicamento"] = medicamento
                auditoria["medicamentos"] = medicamentos
                auditoria["medicamentos_editados_por_medico"] = True
                solicitud.medicamento_reg_no = (medicamento.get("regNo") or "").strip()
                solicitud.medicamento_nombre_producto = (medicamento.get("nombreProducto") or "").strip()
                solicitud.medicamento_nombre_droga = (medicamento.get("nombreDroga") or "").strip()
                solicitud.medicamento_presentacion = (medicamento.get("presentacion") or "").strip()
                solicitud.auditoria = auditoria
                solicitud.save(
                    update_fields=[
                        "medicamento_reg_no",
                        "medicamento_nombre_producto",
                        "medicamento_nombre_droga",
                        "medicamento_presentacion",
                        "auditoria",
                        "updated_at",
                    ]
                )
            emitted = _emitir_solicitud_receta(
                solicitud,
                request.user,
                diagnostico=diagnostico,
                posologia=posologia,
                cantidad=cantidad,
                tratamiento=tratamiento,
                observacion=observacion,
            )
            if emitted:
                messages.success(
                    request,
                    f"La solicitud #{solicitud.id} fue emitida correctamente.",
                )
            else:
                messages.error(
                    request,
                    f"La solicitud #{solicitud.id} no pudo emitirse. Revisar el detalle informado por RCTA.",
                )
            next_url = _solicitudes_result_url(next_url, solicitud.id)
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
    auditoria = solicitud.auditoria if isinstance(solicitud.auditoria, dict) else {}
    medicamentos = auditoria.get("medicamentos")
    if not isinstance(medicamentos, list) or not medicamentos:
        medicamentos = [
            {
                "regNo": solicitud.medicamento_reg_no,
                "nombreProducto": solicitud.medicamento_nombre_producto,
                "nombreDroga": solicitud.medicamento_nombre_droga,
                "presentacion": solicitud.medicamento_presentacion,
            }
        ]
    medicamentos = [item for item in medicamentos if isinstance(item, dict)]
    try:
        recipe_data = _recipe_data_from_solicitud(
            solicitud,
            diagnostico=diagnostico,
            posologia=posologia,
            cantidad=cantidad,
            tratamiento=tratamiento,
            medicamentos=medicamentos,
        )
    except (Qbi2ConfigurationError, ValueError) as exc:
        payload = {}
        response_payload = getattr(exc, "payload", {}) or {}
        error_text = qbi2_error_text(
            response_payload,
            fallback=str(exc),
            status_code=getattr(exc, "status_code", None),
        )
        EmisionSolicitudReceta.objects.create(
            solicitud=solicitud,
            orden=1,
            total=1,
            medicamentos=medicamentos,
            estado=EmisionSolicitudReceta.Estado.ERROR,
            payload_qbi2=payload,
            respuesta_qbi2=response_payload,
            error_qbi2=error_text,
        )
        solicitud.marcar_error_emision(
            user,
            diagnostico=diagnostico,
            posologia=posologia,
            observacion=observacion,
            payload=payload,
            response=response_payload,
            error=error_text,
        )
        return False
    outcome = _perform_rcta_emission(
        solicitud,
        user,
        recipe_data=recipe_data,
        diagnostico=diagnostico,
        posologia=posologia,
        observacion=observacion,
    )
    return outcome["ok"]


def _perform_rcta_emission(
    solicitud,
    user,
    *,
    recipe_data,
    diagnostico,
    posologia,
    observacion="",
):
    """Make one provider call, persist every document and verify its coverage."""
    requested_medications = recipe_data.get("medicamentos") or []
    solicitud.emisiones.all().delete()
    payload: dict[str, Any] = {}
    try:
        _, payload = build_rcta_payload(recipe_data)
        result = emit_rcta_payload(recipe_data)
    except (Qbi2ConfigurationError, ValueError, Qbi2HTTPError) as exc:
        response_payload = getattr(exc, "payload", {}) or {}
        error_text = qbi2_error_text(
            response_payload,
            fallback=str(exc),
            status_code=getattr(exc, "status_code", None),
        )
        EmisionSolicitudReceta.objects.create(
            solicitud=solicitud,
            orden=1,
            total=1,
            medicamentos=requested_medications,
            estado=EmisionSolicitudReceta.Estado.ERROR,
            payload_qbi2=payload,
            respuesta_qbi2=response_payload,
            error_qbi2=error_text,
        )
        solicitud.marcar_error_emision(
            user,
            diagnostico=diagnostico,
            posologia=posologia,
            observacion=observacion,
            payload=payload,
            response=response_payload,
            error=error_text,
        )
        return {
            "ok": False,
            "error": error_text,
            "provider_status": getattr(exc, "status_code", None),
        }

    emisiones = _replace_emission_records(solicitud, result.payload, result.response)
    failed_documents = [
        emision for emision in emisiones
        if emision.estado != EmisionSolicitudReceta.Estado.EMITIDA
    ]
    provider_errors = result.summary.get("errores") or [
        emision.error_qbi2 for emision in failed_documents
    ]
    completeness_error = _emission_completeness_error(
        requested_medications,
        result.response,
        emisiones,
    )
    error_text = str(provider_errors) if provider_errors else completeness_error
    if error_text:
        solicitud.marcar_error_emision(
            user,
            diagnostico=diagnostico,
            posologia=posologia,
            observacion=observacion,
            payload=result.payload,
            response=result.response,
            error=error_text,
        )
        return {"ok": False, "error": error_text, "result": result}

    solicitud.marcar_emitida(
        user,
        diagnostico=diagnostico,
        posologia=posologia,
        observacion=observacion,
        payload=result.payload,
        response=result.response,
        summary=result.summary,
    )
    return {"ok": True, "result": result}


def _emission_completeness_error(requested_medications, response, emisiones):
    limits = recipe_medication_limits()
    if not emisiones:
        return "RCTA no devolvió ningún documento de receta."
    if len(emisiones) > limits.max_documents:
        return (
            f"RCTA devolvió {len(emisiones)} documentos; la operación admite "
            f"como máximo {limits.max_documents}. No reemitir automáticamente."
        )

    requested = Counter(
        str(item.get("regNo") or "").strip()
        for item in requested_medications
        if isinstance(item, dict) and str(item.get("regNo") or "").strip()
    )
    issued = Counter()
    response_items = response.get("response") if isinstance(response, dict) else None
    if isinstance(response_items, list):
        for response_item in response_items:
            medications = response_item.get("medicamentos") if isinstance(response_item, dict) else None
            if not isinstance(medications, list):
                continue
            issued.update(
                str(item.get("regNo") or "").strip()
                for item in medications
                if isinstance(item, dict) and str(item.get("regNo") or "").strip()
            )
    if requested == issued:
        return ""

    missing = list((requested - issued).elements())
    unexpected = list((issued - requested).elements())
    details = [
        f"RCTA informó {sum(issued.values())} de {sum(requested.values())} medicamentos solicitados."
    ]
    if missing:
        details.append(f"Faltan RegNo: {', '.join(missing)}.")
    if unexpected:
        details.append(f"RegNo no solicitados: {', '.join(unexpected)}.")
    details.append("Los documentos devueltos quedaron guardados; no reemitir automáticamente.")
    return " ".join(details)


def _replace_emission_records(solicitud, payload, response):
    """Persist every prescription document returned by one RCTA request."""
    documents = []
    response_items = []
    if isinstance(response, dict):
        raw_documents = (
            response.get("recetas")
            or response.get("receta")
            or response.get("documentos")
            or []
        )
        if isinstance(raw_documents, dict):
            raw_documents = [raw_documents]
        if isinstance(raw_documents, list):
            documents = [item for item in raw_documents if isinstance(item, dict)]
        raw_response_items = response.get("response") or []
        if isinstance(raw_response_items, list):
            response_items = [item for item in raw_response_items if isinstance(item, dict)]

    if not documents:
        return []

    solicitud.emisiones.all().delete()
    total = len(documents)
    emisiones = []
    for index, document in enumerate(documents, start=1):
        response_item = response_items[index - 1] if index <= len(response_items) else {}
        medicamentos = response_item.get("medicamentos") or []
        pdf_url = document.get("s3Link") or ""
        emisiones.append(
            EmisionSolicitudReceta.objects.create(
                solicitud=solicitud,
                orden=index,
                total=total,
                medicamentos=medicamentos if isinstance(medicamentos, list) else [],
                estado=(
                    EmisionSolicitudReceta.Estado.EMITIDA
                    if pdf_url
                    else EmisionSolicitudReceta.Estado.ERROR
                ),
                payload_qbi2=payload or {},
                respuesta_qbi2={"receta": document, "response": response_item},
                error_qbi2="" if pdf_url else "QBI2 no devolvió PDF para este documento.",
                qbi2_id_receta=document.get("idReceta") or "",
                qbi2_pdf_url=pdf_url,
            )
        )
    return emisiones
