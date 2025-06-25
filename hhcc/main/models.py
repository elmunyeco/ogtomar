from django.db import models
from django.utils import timezone


class TipoDocumento(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=255)

    class Meta:
        db_table = "tipos_documentos"
        indexes = [
            models.Index(fields=["nombre"], name="nombre_tipodocumento_idx"),
        ]

    def __str__(self):
        return self.nombre


class Paciente(models.Model):
    SEXO_CHOICES = [
        ("H", "Hombre"),
        ("M", "Mujer"),
    ]

    idTipoDoc = models.ForeignKey(
        TipoDocumento, 
        on_delete=models.CASCADE, 
        default=1,
        db_column="idTipoDoc_id"
    )    
    numDoc = models.CharField(max_length=50)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    fechaNac = models.DateField(null=True, blank=True)
    sexo = models.CharField(
        max_length=1, 
        choices=SEXO_CHOICES,
        verbose_name="Sexo"
    )
    mail = models.EmailField(max_length=50, null=True, blank=True)
    direccion = models.CharField(max_length=100, null=True, blank=True)
    localidad = models.CharField(max_length=60, null=True, blank=True)
    obraSocial = models.CharField(max_length=50, null=True, blank=True)
    plan = models.CharField(max_length=50, null=True, blank=True)
    afiliado = models.CharField(max_length=50, null=True, blank=True)
    telefono = models.CharField(max_length=50, null=True, blank=True)
    celular = models.CharField(max_length=50, null=True, blank=True)
    profesion = models.CharField(max_length=50, null=True, blank=True)
    referente = models.CharField(max_length=50, null=True, blank=True)
    fechaAlta = models.DateField(default=timezone.now)
    deBaja = models.BooleanField(default=False)
    """ 
    idTipoDoc_temp = models.IntegerField(
        null=True, blank=True
    )  # Campo temporal para migrar 
    """
    class Meta:
        db_table = "pacientes"
        unique_together = (
            "idTipoDoc",
            "numDoc",
        )
        ordering = ['-fechaAlta']
        indexes = [
            models.Index(fields=["nombre"], name="nombre_paciente_idx"),
            models.Index(fields=["apellido"], name="apellido_paciente_idx"),
            models.Index(fields=["fechaAlta"], name="paciente_fechaAlta_idx"),
            models.Index(fields=["idTipoDoc"], name="pacientes_tipo_doc_idx"),
        ]
       # Método personalizado para obtener la identificación
    @property
    def identificacion(self):
        return f"{self.idTipoDoc.nombre} {self.numDoc}"

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.identificacion})"


class CondicionMedica(models.Model):
    nombre = models.CharField(max_length=100)
    orden = models.IntegerField(default=0)

    class Meta:
        db_table = "condiciones_medicas"
        ordering = ["orden"]

    def __str__(self):
        return self.nombre


class HistoriaClinica(models.Model):

    fechaAlta = models.DateField(default=timezone.now)

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.RESTRICT, 
        related_name="historias_clinicas"
    )

    condiciones = models.ManyToManyField(
        CondicionMedica, 
        through="CondicionMedicaHistoria"
    )

    class Meta:
        db_table = "historias_clinicas"
        indexes = [
            # ✅ Este índice ya está bien
            models.Index(fields=["fechaAlta"], name="historia_fechaAlta_idx"),
            models.Index(fields=["paciente"], name="historia_paciente_idx"),
        ]

    def __str__(self):
        if self.paciente:
            return f"Historia Clínica de {self.paciente.nombre} {self.paciente.apellido} - {self.fechaAlta.strftime('%Y-%m-%d')}"


class CondicionMedicaHistoria(models.Model):
    historia = models.ForeignKey("HistoriaClinica", on_delete=models.CASCADE)
    condicion = models.ForeignKey("CondicionMedica", on_delete=models.CASCADE)

    class Meta:
        db_table = "condiciones_medicas_historias"
        unique_together = ["historia", "condicion"]

    def __str__(self):
        return f"Condición {self.condicion.nombre} en Historia {self.historia.id}"


""" class Visita(models.Model):
    historia_clinica = models.ForeignKey(HistoriaClinica, on_delete=models.CASCADE)
    fecha = models.DateField()
    # otros campos relacionados a la visita
"""


class SignosVitales(models.Model):
    historia = models.ForeignKey(HistoriaClinica, on_delete=models.CASCADE)
    fecha = models.DateField(default=timezone.now)
    presion_sistolica = models.IntegerField(null=True, blank=True)
    presion_diastolica = models.IntegerField(null=True, blank=True)
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    glucemia = models.IntegerField(null=True, blank=True)
    colesterol = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "signos_vitales"
        ordering = ["-fecha"]        
        indexes = [
        
            models.Index(fields=["historia"], name="signos_vitales_historia_idx"),
            models.Index(fields=["fecha"], name="signos_vitales_fecha_idx"),
        ]
    def __str__(self):
        return f"Signos Vitales - Historia {self.historia_id} - {self.fecha.strftime('%Y-%m-%d')}"


class ComentariosVisitas(models.Model):
    TIPO_COMENTARIO = [
        ("EVOL", "Evolución"),
        ("INDIC", "Indicaciones"),
    ]
    fecha = models.DateTimeField(auto_now_add=True)
    comentarios = models.TextField()
    tipo = models.CharField(max_length=5, choices=TIPO_COMENTARIO, default="EVOL")
    historia_clinica = models.ForeignKey(
        "HistoriaClinica", on_delete=models.CASCADE, db_column="idHistoriaClinica"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "fecha": self.fecha.strftime("%Y-%m-%d %H:%M:%S"),
            "comentarios": self.comentarios,
            "tipo": self.tipo,
        }

    class Meta:
        db_table = "comentarios_visitas"
        indexes = [
            models.Index(fields=["fecha"]),
            models.Index(fields=["historia_clinica"]),
            models.Index(fields=["fecha", "historia_clinica"]),
        ]
    
    def __str__(self):
        return f"Comentario - Historia {self.historia_clinica_id} - {self.fecha.strftime('%Y-%m-%d %H:%M:%S')}"


class IndicacionesVisitas(models.Model):
    historia_clinica = models.ForeignKey(
        "HistoriaClinica", 
        on_delete=models.CASCADE, 
        db_column="historia_clinica_id"
    )

    medicamento = models.TextField()
    ochoHoras = models.TextField(null=True)
    doceHoras = models.TextField(null=True)
    dieciochoHoras = models.TextField(null=True)
    veintiunaHoras = models.TextField(null=True)
    fecha = models.DateField()
    eliminado = models.BooleanField(null=True)

    def to_dict(self):
        return {
            "id": self.id,
            "historia_clinica_id": self.historia_clinica_id,
            "medicamento": self.medicamento,
            "ochoHoras": self.ochoHoras,
            "doceHoras": self.doceHoras,
            "dieciochoHoras": self.dieciochoHoras,
            "veintiunaHoras": self.veintiunaHoras,
            "fecha": self.fecha.strftime('%Y-%m-%d'),
            "eliminado": self.eliminado,
        }

    class Meta:
        db_table = "indicaciones_visitas"

        indexes = [
            models.Index(fields=["fecha"], name="indicaciones_fecha_idx"),
            models.Index(fields=["historia_clinica"], name="indicaciones_historia_idx"),
            models.Index(fields=["historia_clinica", "fecha"], name="ind_hist_fecha_idx"),
        ]
    
    def __str__(self):
        return f"Indicaciones - Historia {self.historia_clinica_id} - {self.fecha.strftime('%Y-%m-%d')}"
