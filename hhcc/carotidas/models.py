from django.db import models
from django.utils import timezone

from main.models import HistoriaClinica


class CarotidasEstudio(models.Model):
    """
    Estudio de carótidas (doppler vasos del cuello / QIMT).
    Basado en la tabla legacy `carotidas`.
    """

    historia = models.ForeignKey(
        HistoriaClinica,
        on_delete=models.CASCADE,
        related_name="carotidas_estudios",
    )
    com_derecha = models.CharField(max_length=512, null=True, blank=True)
    int_derecha = models.CharField(max_length=512, null=True, blank=True)
    ext_derecha = models.CharField(max_length=512, null=True, blank=True)
    com_izquierda = models.CharField(max_length=512, null=True, blank=True)
    int_izquierda = models.CharField(max_length=512, null=True, blank=True)
    ext_izquierda = models.CharField(max_length=512, null=True, blank=True)
    art_vertebrales = models.CharField(max_length=255, null=True, blank=True)
    sugerencias = models.CharField(max_length=255, null=True, blank=True)
    id_com_der = models.PositiveIntegerField(default=0)
    id_com_izq = models.PositiveIntegerField(default=0)
    esp_int_med_der = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    esp_int_med_izq = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    fecha_estudio = models.DateField(default=timezone.localdate)

    COMUN_CHOICES = {
        1: "Dentro de límites normales. Sin lesiones que impresionen patológicas.",
        2: "Presenta múltiples lesiones sin compromiso hemodinámico anterógrado.",
        3: "Presenta incremento del espesor íntima media.",
        4: "Presenta recorrido tortuoso que genera flujo turbulento.",
        99: "Otras.",
    }

    INTERNA_CHOICES = {
        0: "Se presenta libre de lesiones visibles y hemodinámicamente mesurables.",
        1: "Se observa lesión",
        2: "Estable",
        3: "Inestable",
        4: "Localizada próxima a la bifurcación carotidea",
        5: "Localizada en segmento medio",
        6: "Localizada en segmento distal",
        7: "Estenosis < 25%",
        8: "Estenosis 25-50 %",
        9: "Estenosis > 60%",
    }

    EXTERNA_CHOICES = {
        0: "Se presenta libre de lesiones visibles y hemodinámicamente mesurables.",
        1: "Se observa lesión",
        2: "Estenosis < 25%",
        3: "Estenosis 25-50 %",
        4: "Estenosis > 60%",
    }

    VERTEBRALES_CHOICES = {
        0: "Flujos conservados.",
        1: "Disminución del flujo en arteria vertebral",
        2: "Izquierda",
        3: "Derecha",
    }

    class Meta:
        db_table = "carotidas"
        verbose_name = "Estudio de carótidas"
        verbose_name_plural = "Estudios de carótidas"
        indexes = [
            models.Index(fields=["historia"], name="carotidas_historia_idx"),
            models.Index(fields=["id_com_der", "id_com_izq"], name="carotidas_com_idx"),
        ]

    def __str__(self):
        return f"Carótidas HC {self.historia_id} - Estudio {self.pk or 'nuevo'}"

    @staticmethod
    def _parse_codes(value):
        if value is None:
            return []
        raw = str(value).strip()
        if not raw:
            return []
        if "," in raw:
            parts = raw.split(",")
        else:
            parts = [raw]
        codes = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if part.isdigit():
                codes.append(int(part))
        return codes

    def _decode_comun_from_field(self, value):
        codes = self._parse_codes(value)
        if not codes:
            return ""
        return self.COMUN_CHOICES.get(codes[0], "")

    def com_der_texto(self):
        if self.id_com_der:
            return self.COMUN_CHOICES.get(self.id_com_der, "")
        return self._decode_comun_from_field(self.com_derecha)

    def com_izq_texto(self):
        if self.id_com_izq:
            return self.COMUN_CHOICES.get(self.id_com_izq, "")
        return self._decode_comun_from_field(self.com_izquierda)

    def _decode_interna(self, value):
        codes = self._parse_codes(value)
        if not codes:
            return value or ""
        if 0 in codes:
            return self.INTERNA_CHOICES[0]
        if 1 in codes:
            estabilidad = ""
            localizacion = ""
            estenosis = ""
            for code in codes:
                if code in (2, 3):
                    estabilidad = self.INTERNA_CHOICES.get(code, estabilidad)
                if code in (4, 5, 6):
                    localizacion = self.INTERNA_CHOICES.get(code, localizacion)
                if code in (7, 8, 9):
                    estenosis = self.INTERNA_CHOICES.get(code, estenosis)
            detalles = []
            if estabilidad:
                detalles.append(f"{estabilidad}.")
            if localizacion:
                detalles.append(f"{localizacion}.")
            if estenosis:
                detalles.append(f"{estenosis}.")
            detalle_txt = " ".join(detalles).strip()
            return "Se observa lesión." + (f" {detalle_txt}" if detalle_txt else "")
        return value or ""

    def _decode_externa(self, value):
        codes = self._parse_codes(value)
        if not codes:
            return value or ""
        if 0 in codes:
            return self.EXTERNA_CHOICES[0]
        if 1 in codes:
            estenosis = ""
            for code in codes:
                if code in (2, 3, 4):
                    estenosis = self.EXTERNA_CHOICES.get(code, estenosis)
            return "Se observa lesión." + (f" {estenosis}." if estenosis else "")
        return value or ""

    def _decode_vertebrales(self, value):
        codes = self._parse_codes(value)
        if not codes:
            return value or ""
        if 0 in codes:
            return self.VERTEBRALES_CHOICES[0]
        if 1 in codes:
            lado = ""
            for code in codes:
                if code in (2, 3):
                    lado = self.VERTEBRALES_CHOICES.get(code, lado)
            if lado:
                return f"Disminución del flujo en arteria vertebral {lado.lower()}."
            return "Disminución del flujo en arteria vertebral."
        return value or ""

    def int_derecha_texto(self):
        return self._decode_interna(self.int_derecha)

    def int_izquierda_texto(self):
        return self._decode_interna(self.int_izquierda)

    def ext_derecha_texto(self):
        return self._decode_externa(self.ext_derecha)

    def ext_izquierda_texto(self):
        return self._decode_externa(self.ext_izquierda)

    def art_vertebrales_texto(self):
        return self._decode_vertebrales(self.art_vertebrales)
