from django.db import models
from django.core.validators import MaxLengthValidator
from django.utils import timezone

from main.models import HistoriaClinica


class MmiiEstudio(models.Model):
    """
    Doppler Color Arterial de Miembros Inferiores.
    Basado en la tabla legacy `doppler` (renombrada a `mmii`).
    """

    id_mmii = models.AutoField(db_column="idMMII", primary_key=True)
    historia = models.ForeignKey(
        HistoriaClinica,
        on_delete=models.CASCADE,
        related_name="mmii_estudios",
        db_column="idHC",
    )
    art_fem_comun_derecha = models.TextField(
        db_column="artFemComunDerecha",
        null=True,
        blank=True,
        validators=[MaxLengthValidator(512)],
    )
    art_fem_superficial_derecha = models.TextField(
        db_column="artFemSuperficialDerecha",
        null=True,
        blank=True,
        validators=[MaxLengthValidator(512)],
    )
    art_fem_profunda_derecha = models.TextField(
        db_column="artFemProfundaDerecha",
        null=True,
        blank=True,
        validators=[MaxLengthValidator(512)],
    )
    art_poplitea_derecha = models.TextField(
        db_column="artPopliteaDerecha",
        null=True,
        blank=True,
        validators=[MaxLengthValidator(512)],
    )
    art_infrapatelares_derecha = models.TextField(
        db_column="artInfrapatelaresDerecha",
        null=True,
        blank=True,
        validators=[MaxLengthValidator(512)],
    )
    art_fem_comun_izquierda = models.TextField(
        db_column="artFemComunIzquierda",
        null=True,
        blank=True,
        validators=[MaxLengthValidator(512)],
    )
    art_fem_superficial_izquierda = models.TextField(
        db_column="artFemSuperficialIzquierda",
        null=True,
        blank=True,
        validators=[MaxLengthValidator(512)],
    )
    art_fem_profunda_izquierda = models.TextField(
        db_column="artFemProfundaIzquierda",
        null=True,
        blank=True,
        validators=[MaxLengthValidator(512)],
    )
    art_poplitea_izquierda = models.TextField(
        db_column="artPopliteaIzquierda",
        null=True,
        blank=True,
        validators=[MaxLengthValidator(512)],
    )
    art_infrapatelares_izquierda = models.TextField(
        db_column="artInfrapatelaresIzquierda",
        null=True,
        blank=True,
        validators=[MaxLengthValidator(512)],
    )
    conclusion = models.TextField(
        db_column="conclusion",
        null=True,
        blank=True,
        validators=[MaxLengthValidator(8000)],
    )
    fecha_estudio = models.DateField(default=timezone.localdate)

    class Meta:
        db_table = "mmii"
        verbose_name = "MMII arterial de miembros inferiores"
        verbose_name_plural = "MMII arterial de miembros inferiores"
        indexes = [
            models.Index(fields=["historia"], name="mmii_historia_idx")
        ]

    def __str__(self):
        return f"MMII HC {self.historia_id} - Estudio {self.pk or 'nuevo'}"
