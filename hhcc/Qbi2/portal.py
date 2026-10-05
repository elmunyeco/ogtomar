from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac

from main.models import (
    ComentariosVisitas,
    HistoriaClinica,
    IndicacionesVisitas,
    Paciente,
    SignosVitales,
)

from .models import PatientLoginThrottle, SolicitudReceta


PATIENT_SESSION_KEY = "qbi2_patient_portal_patient_id"


def normalize_document(value: str) -> str:
    return "".join(char for char in (value or "") if char.isdigit())


def normalize_surname(value: str) -> str:
    return " ".join((value or "").split()).casefold()


def _document_fingerprint(documento: str) -> str:
    return salted_hmac(
        "qbi2.patient-login",
        normalize_document(documento),
        algorithm="sha256",
    ).hexdigest()


def patient_login_is_blocked(documento: str) -> bool:
    normalized = normalize_document(documento)
    if not normalized:
        return False
    throttle = PatientLoginThrottle.objects.filter(
        document_hash=_document_fingerprint(normalized)
    ).first()
    if not throttle or not throttle.blocked_until:
        return False
    if throttle.blocked_until > timezone.now():
        return True
    throttle.delete()
    return False


@transaction.atomic
def register_patient_login_failure(documento: str) -> bool:
    normalized = normalize_document(documento)
    if not normalized:
        return False
    document_hash = _document_fingerprint(normalized)
    throttle, _ = PatientLoginThrottle.objects.select_for_update().get_or_create(
        document_hash=document_hash
    )
    if throttle.blocked_until and throttle.blocked_until <= timezone.now():
        throttle.failed_attempts = 0
        throttle.blocked_until = None
    throttle.failed_attempts += 1
    max_failures = int(getattr(settings, "QBI2_PATIENT_LOGIN_MAX_FAILURES", 5))
    blocked = throttle.failed_attempts >= max_failures
    if blocked:
        minutes = int(getattr(settings, "QBI2_PATIENT_LOGIN_BLOCK_MINUTES", 10))
        throttle.blocked_until = timezone.now() + timedelta(minutes=minutes)
    throttle.save()
    return blocked


def clear_patient_login_failures(documento: str) -> None:
    normalized = normalize_document(documento)
    if normalized:
        PatientLoginThrottle.objects.filter(
            document_hash=_document_fingerprint(normalized)
        ).delete()


def find_patient_history(apellido: str, documento: str) -> tuple[Paciente | None, HistoriaClinica | None]:
    apellido = normalize_surname(apellido)
    documento = normalize_document(documento)
    if not apellido or not documento:
        return None, None

    candidatos = Paciente.objects.filter(numDoc=documento, deBaja=False).order_by("-fechaAlta", "-id")
    paciente = next(
        (candidato for candidato in candidatos if normalize_surname(candidato.apellido) == apellido),
        None,
    )
    if not paciente:
        return None, None

    historia = (
        HistoriaClinica.objects.filter(paciente=paciente)
        .order_by("-fechaAlta", "-id")
        .first()
    )
    return paciente, historia


def start_patient_session(request, paciente: Paciente) -> None:
    request.session.cycle_key()
    request.session[PATIENT_SESSION_KEY] = paciente.pk
    request.session.set_expiry(getattr(settings, "QBI2_PATIENT_SESSION_AGE", 30 * 60))


def get_patient_from_session(request) -> Paciente | None:
    paciente_id = request.session.get(PATIENT_SESSION_KEY)
    if not paciente_id:
        return None
    paciente = Paciente.objects.filter(pk=paciente_id, deBaja=False).first()
    if not paciente:
        request.session.pop(PATIENT_SESSION_KEY, None)
    return paciente


def end_patient_session(request) -> None:
    request.session.pop(PATIENT_SESSION_KEY, None)


def patient_has_private_coverage(paciente: Paciente) -> bool:
    value = " ".join((paciente.obraSocial or "").casefold().split())
    return not value or value in {"particular", "sin cobertura", "ninguna", "sin obra social"}


def latest_patient_attention(paciente: Paciente):
    history_ids = list(paciente.historias_clinicas.values_list("id", flat=True))
    if not history_ids:
        return None
    dates = [
        ComentariosVisitas.objects.filter(
            historia_clinica_id__in=history_ids,
            tipo="EVOL",
        ).order_by("-fecha").values_list("fecha", flat=True).first(),
        SignosVitales.objects.filter(
            historia_id__in=history_ids
        ).order_by("-fecha").values_list("fecha", flat=True).first(),
        IndicacionesVisitas.objects.filter(
            historia_clinica_id__in=history_ids,
            eliminado=False,
        ).order_by("-fecha").values_list("fecha", flat=True).first(),
        paciente.historias_clinicas.order_by("-fechaAlta").values_list(
            "fechaAlta", flat=True
        ).first(),
    ]
    normalized = [value.date() if hasattr(value, "date") else value for value in dates if value]
    return max(normalized) if normalized else None


def patient_portal_eligibility(paciente: Paciente, *, max_attention_age_years: int) -> dict:
    coverage_required = bool(
        not patient_has_private_coverage(paciente) and not paciente.qbi2_financiador_id
    )
    last_attention = latest_patient_attention(paciente)
    today = timezone.localdate()
    try:
        threshold = today.replace(year=today.year - max_attention_age_years)
    except ValueError:  # 29 de febrero
        threshold = today.replace(month=2, day=28, year=today.year - max_attention_age_years)
    attention_expired = last_attention is None or last_attention < threshold
    return {
        "coverage_required": coverage_required,
        "attention_expired": attention_expired,
        "last_attention": last_attention,
        "can_request": not coverage_required and not attention_expired,
        "max_attention_age_years": max_attention_age_years,
    }


def create_prescription_request(
    paciente: Paciente,
    historia: HistoriaClinica,
    medicamento: dict,
    *,
    medicamentos: list[dict] | None = None,
    receta_orden: int | None = None,
    total_recetas: int | None = None,
    total_medicamentos_paciente: int | None = None,
    diagnostico: str = "",
    observacion_paciente: str = "",
    request_ip: str | None = None,
    request_user_agent: str = "",
) -> SolicitudReceta:
    medicamentos = medicamentos or [medicamento]
    auditoria = {
        "source": "portal-pacientes",
        "medicamento": medicamento,
        "medicamentos": medicamentos,
    }
    if receta_orden is not None and total_recetas is not None:
        auditoria["receta_orden"] = receta_orden
        auditoria["total_recetas"] = total_recetas
    if total_medicamentos_paciente is not None:
        auditoria["total_medicamentos_paciente"] = total_medicamentos_paciente

    return SolicitudReceta.objects.create(
        paciente=paciente,
        historia_clinica=historia,
        medicamento_reg_no=(medicamento.get("regNo") or "").strip(),
        medicamento_nombre_producto=(medicamento.get("nombreProducto") or "").strip(),
        medicamento_nombre_droga=(medicamento.get("nombreDroga") or "").strip(),
        medicamento_presentacion=(medicamento.get("presentacion") or "").strip(),
        diagnostico=(diagnostico or "").strip(),
        observacion_paciente=(observacion_paciente or "").strip(),
        request_ip=request_ip,
        request_user_agent=request_user_agent[:1000],
        auditoria=auditoria,
    )


def get_client_ip(request) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None
