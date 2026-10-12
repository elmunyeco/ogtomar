from django.conf import settings
from django.db import models
from django.utils import timezone


class SolicitudReceta(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        APROBADA = "aprobada", "Aprobada"
        RECHAZADA = "rechazada", "Rechazada"
        EMITIDA = "emitida", "Emitida"
        ERROR_EMISION = "error_emision", "Error de emision"
        ANULADA = "anulada", "Anulada"

    paciente = models.ForeignKey(
        "main.Paciente",
        on_delete=models.RESTRICT,
        related_name="qbi2_solicitudes_receta",
    )
    historia_clinica = models.ForeignKey(
        "main.HistoriaClinica",
        on_delete=models.RESTRICT,
        related_name="qbi2_solicitudes_receta",
    )
    client_request_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        unique=True,
        help_text="Clave de idempotencia enviada por el cliente médico.",
    )
    medicamento_reg_no = models.CharField(max_length=50)
    medicamento_nombre_producto = models.CharField(max_length=255, blank=True)
    medicamento_nombre_droga = models.CharField(max_length=255, blank=True)
    medicamento_presentacion = models.CharField(max_length=255, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    diagnostico = models.CharField(max_length=255, blank=True)
    posologia = models.TextField(blank=True)
    observacion_paciente = models.TextField(blank=True)
    observacion_medico = models.TextField(blank=True)
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="qbi2_solicitudes_receta_aprobadas",
    )
    fecha_decision = models.DateTimeField(null=True, blank=True)
    payload_qbi2 = models.JSONField(default=dict, blank=True)
    respuesta_qbi2 = models.JSONField(default=dict, blank=True)
    error_qbi2 = models.TextField(blank=True)
    qbi2_id_receta = models.CharField(max_length=100, blank=True)
    qbi2_pdf_url = models.URLField(blank=True)
    request_ip = models.GenericIPAddressField(null=True, blank=True)
    request_user_agent = models.TextField(blank=True)
    auditoria = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    hidden_from_history_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "qbi2_solicitudes_receta"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["estado", "-created_at"], name="qbi2_sol_estado_fecha_idx"),
            models.Index(fields=["paciente", "-created_at"], name="qbi2_sol_paciente_fecha_idx"),
            models.Index(fields=["medicamento_reg_no"], name="qbi2_sol_regno_idx"),
        ]

    def __str__(self):
        medicamento = self.medicamento_nombre_producto or self.medicamento_reg_no
        return f"Solicitud receta {self.id} - {self.paciente} - {medicamento}"

    def aprobar(self, user, observacion=""):
        self.estado = self.Estado.APROBADA
        self.aprobado_por = user if getattr(user, "is_authenticated", False) else None
        self.fecha_decision = timezone.now()
        self.observacion_medico = observacion or self.observacion_medico
        self.save(update_fields=["estado", "aprobado_por", "fecha_decision", "observacion_medico", "updated_at"])

    def rechazar(self, user, observacion=""):
        self.estado = self.Estado.RECHAZADA
        self.aprobado_por = user if getattr(user, "is_authenticated", False) else None
        self.fecha_decision = timezone.now()
        self.observacion_medico = observacion or self.observacion_medico
        self.save(update_fields=["estado", "aprobado_por", "fecha_decision", "observacion_medico", "updated_at"])

    def marcar_emitida(self, user, *, diagnostico, posologia, observacion="", payload=None, response=None, summary=None):
        self.estado = self.Estado.EMITIDA
        self.aprobado_por = user if getattr(user, "is_authenticated", False) else None
        self.fecha_decision = timezone.now()
        self.diagnostico = diagnostico
        self.posologia = posologia
        self.observacion_medico = observacion or self.observacion_medico
        self.payload_qbi2 = payload or {}
        self.respuesta_qbi2 = response or {}
        self.error_qbi2 = ""
        self.qbi2_id_receta = (summary or {}).get("idReceta") or ""
        self.qbi2_pdf_url = (summary or {}).get("s3Link") or ""
        self.save(
            update_fields=[
                "estado",
                "aprobado_por",
                "fecha_decision",
                "diagnostico",
                "posologia",
                "observacion_medico",
                "payload_qbi2",
                "respuesta_qbi2",
                "error_qbi2",
                "qbi2_id_receta",
                "qbi2_pdf_url",
                "updated_at",
            ]
        )

    def marcar_error_emision(self, user, *, diagnostico, posologia, observacion="", payload=None, response=None, error=""):
        self.estado = self.Estado.ERROR_EMISION
        self.aprobado_por = user if getattr(user, "is_authenticated", False) else None
        self.fecha_decision = timezone.now()
        self.diagnostico = diagnostico
        self.posologia = posologia
        self.observacion_medico = observacion or self.observacion_medico
        self.payload_qbi2 = payload or {}
        self.respuesta_qbi2 = response or {}
        self.error_qbi2 = error
        self.save(
            update_fields=[
                "estado",
                "aprobado_por",
                "fecha_decision",
                "diagnostico",
                "posologia",
                "observacion_medico",
                "payload_qbi2",
                "respuesta_qbi2",
                "error_qbi2",
                "updated_at",
            ]
        )

    def reabrir_para_reintento(self, user):
        """Return a failed request to review while preserving the failed attempt."""
        if self.estado != self.Estado.ERROR_EMISION:
            return False
        if self.emisiones.filter(estado=EmisionSolicitudReceta.Estado.EMITIDA).exists():
            # A partial provider response may already represent legal prescriptions.
            # Retrying it blindly could duplicate those documents.
            return False

        auditoria = dict(self.auditoria or {})
        intentos = auditoria.get("intentos_emision")
        if not isinstance(intentos, list):
            intentos = []
        intentos.append(
            {
                "estado": self.estado,
                "fecha": self.fecha_decision.isoformat() if self.fecha_decision else "",
                "error": self.error_qbi2,
                "respuesta": self.respuesta_qbi2,
                "reabierta_en": timezone.now().isoformat(),
                "reabierta_por": getattr(user, "username", "") or "",
            }
        )
        auditoria["intentos_emision"] = intentos

        self.estado = self.Estado.PENDIENTE
        self.aprobado_por = None
        self.fecha_decision = None
        self.auditoria = auditoria
        self.save(
            update_fields=[
                "estado",
                "aprobado_por",
                "fecha_decision",
                "auditoria",
                "updated_at",
            ]
        )
        self.emisiones.filter(estado=EmisionSolicitudReceta.Estado.ERROR).delete()
        return True


class PatientLoginThrottle(models.Model):
    """Failed portal logins keyed by a non-reversible document fingerprint."""

    document_hash = models.CharField(max_length=64, unique=True)
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    blocked_until = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "qbi2_patient_login_throttle"


class MedicamentoHabitualOculto(models.Model):
    paciente = models.ForeignKey("main.Paciente", on_delete=models.CASCADE)
    reg_no = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["paciente", "reg_no"], name="qbi2_habitual_oculto_unique")]


class EmisionSolicitudReceta(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EMITIDA = "emitida", "Emitida"
        ERROR = "error", "Error"

    solicitud = models.ForeignKey(
        SolicitudReceta,
        on_delete=models.CASCADE,
        related_name="emisiones",
    )
    orden = models.PositiveSmallIntegerField()
    total = models.PositiveSmallIntegerField()
    medicamentos = models.JSONField(default=list)
    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    payload_qbi2 = models.JSONField(default=dict, blank=True)
    respuesta_qbi2 = models.JSONField(default=dict, blank=True)
    error_qbi2 = models.TextField(blank=True)
    qbi2_id_receta = models.CharField(max_length=100, blank=True)
    qbi2_pdf_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "qbi2_emisiones_solicitud_receta"
        ordering = ["orden", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["solicitud", "orden"],
                name="qbi2_emision_solicitud_orden_uniq",
            )
        ]

    def __str__(self):
        return f"Emisión {self.orden}/{self.total} de solicitud {self.solicitud_id}"
