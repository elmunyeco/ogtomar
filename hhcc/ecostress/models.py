from django.db import models
from django.core.validators import MaxLengthValidator

from main.models import HistoriaClinica


class EcostressEstudio(models.Model):
    """
    Estudio de ecostress cardiaco.
    Basado en la tabla legacy `stress`.
    """

    id_stress = models.AutoField(primary_key=True, db_column="idStress")
    historia = models.ForeignKey(
        HistoriaClinica,
        on_delete=models.CASCADE,
        related_name="ecostress_estudios",
        db_column="idHC",
    )
    indicacion_estudio = models.TextField(
        null=True,
        blank=True,
        db_column="indicacionEstudio",
        validators=[MaxLengthValidator(512)],
    )
    tipo_apremio = models.TextField(
        null=True,
        blank=True,
        db_column="tipoApremio",
        validators=[MaxLengthValidator(512)],
    )
    medicacion_momento_estudio = models.TextField(
        null=True,
        blank=True,
        db_column="medicacionMomentoEstudio",
        validators=[MaxLengthValidator(512)],
    )
    medico_solicitante = models.TextField(
        null=True,
        blank=True,
        db_column="medicoSolicitante",
        validators=[MaxLengthValidator(512)],
    )
    frecuencia_cardiaca_basal = models.TextField(
        null=True,
        blank=True,
        db_column="frecuenciaCardiacaBasal",
        validators=[MaxLengthValidator(512)],
    )
    frecuencia_cardiaca_maxima = models.TextField(
        null=True,
        blank=True,
        db_column="frecuenciaCardiacaMaxima",
        validators=[MaxLengthValidator(512)],
    )
    presion_arterial_basal_inicial = models.TextField(
        null=True,
        blank=True,
        db_column="presionArterialBasalInicial",
        validators=[MaxLengthValidator(512)],
    )
    presion_arterial_basal_final = models.TextField(
        null=True,
        blank=True,
        db_column="presionArterialBasalFinal",
        validators=[MaxLengthValidator(512)],
    )
    presion_arterial_maxima_inicial = models.TextField(
        null=True,
        blank=True,
        db_column="presionArterialMaximaInicial",
        validators=[MaxLengthValidator(512)],
    )
    presion_arterial_maxima_final = models.TextField(
        null=True,
        blank=True,
        db_column="presionArterialMaximaFinal",
        validators=[MaxLengthValidator(512)],
    )
    informe_ergometria = models.TextField(
        null=True,
        blank=True,
        db_column="informeErgometria",
        validators=[MaxLengthValidator(512)],
    )
    datos_ecocardiograficos_basales = models.TextField(
        null=True,
        blank=True,
        db_column="datosEcocardiograficosBasales",
        validators=[MaxLengthValidator(512)],
    )
    datos_ecocardiograficos_post_esfuerzo_inmediato = models.TextField(
        null=True,
        blank=True,
        db_column="datosEcocardiograficosPostEsfuerzoInmediato",
        validators=[MaxLengthValidator(512)],
    )
    conclusion = models.TextField(
        null=True,
        blank=True,
        db_column="conclusion",
        validators=[MaxLengthValidator(8000)],
    )
    fecha_estudio = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "stress"
        verbose_name = "Estudio de ecostress"
        verbose_name_plural = "Estudios de ecostress"
        indexes = [
            models.Index(fields=["historia"], name="stress_historia_idx"),
        ]

    def __str__(self):
        return f"Ecostress HC {self.historia_id} - Estudio {self.pk or 'nuevo'}"
