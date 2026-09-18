from __future__ import annotations

from django.conf import settings

from main.models import HistoriaClinica, Paciente

from .models import SolicitudReceta


PATIENT_SESSION_KEY = "qbi2_patient_portal_patient_id"


def normalize_document(value: str) -> str:
    return "".join(char for char in (value or "") if char.isdigit())


def normalize_surname(value: str) -> str:
    return " ".join((value or "").split()).casefold()


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
        "medicamentos": medicamentos[:2],
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
