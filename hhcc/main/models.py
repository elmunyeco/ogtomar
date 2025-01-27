from django.db import models
from django.utils import timezone


# Modelo TipoDocumento
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


# Modelo Paciente
class Paciente(models.Model):
    SEXO_CHOICES = [
        ("h", "Hombre"),
        ("m", "Mujer"),
    ]

    idTipoDoc = models.ForeignKey(
        TipoDocumento, on_delete=models.CASCADE, default=1
    )  # Clave foránea hacia TipoDocumento
    numDoc = models.CharField(max_length=50)  # Número de documento
    nombre = models.CharField(max_length=50)  # Nombre del paciente
    apellido = models.CharField(max_length=50)  # Apellido del paciente
    fechaNac = models.DateField(null=True, blank=True)  # Fecha de nacimiento
    sexo = models.CharField(
        max_length=1, choices=[("M", "Masculino"), ("F", "Femenino"), ("O", "Otro")]
    )  # Sexo
    mail = models.EmailField(max_length=50, null=True, blank=True)  # Email opcional
    direccion = models.CharField(
        max_length=100, null=True, blank=True
    )  # Dirección opcional
    localidad = models.CharField(
        max_length=60, null=True, blank=True
    )  # Localidad opcional
    obraSocial = models.CharField(max_length=50)  # Obra social
    plan = models.CharField(max_length=50, null=True, blank=True)  # Plan opcional
    afiliado = models.CharField(max_length=50)  # Número de afiliado
    telefono = models.CharField(max_length=50)  # Teléfono
    celular = models.CharField(max_length=50)  # Celular
    profesion = models.CharField(max_length=50)  # Profesión
    referente = models.CharField(
        max_length=50, null=True, blank=True
    )  # Referente opcional
    fechaAlta = models.DateField(default=timezone.now)  # Fecha de alta
    deBaja = models.BooleanField(default=False)  # Dado de baja (lógica)
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
        )  # Combinación única de tipo de documento y número
        indexes = [
            models.Index(fields=["nombre"], name="nombre_paciente_idx"),
            models.Index(fields=["apellido"], name="apellido_paciente_idx"),
            models.Index(fields=["fechaAlta"], name="paciente_fechaAlta_idx"),
        ]

    # Método personalizado para obtener la identificación
    @property
    def identificacion(self):
        return f"{self.idTipoDoc.nombre} {self.numDoc}"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class CondicionMedica(models.Model):
    nombre = models.CharField(max_length=100)
    orden = models.IntegerField(default=0)

    class Meta:
        db_table = "condiciones_medicas"
        ordering = ["orden"]

    def __str__(self):
        return self.nombre


class HistoriaClinica(models.Model):

    # Fecha de alta de la historia clínica
    fechaAlta = models.DateField(default=timezone.now)

    # Clave foránea a Paciente
    paciente = models.ForeignKey(
        "Paciente", on_delete=models.RESTRICT, related_name="historias_clinicas"
    )

    condiciones = models.ManyToManyField(
        CondicionMedica, through="CondicionMedicaHistoria"
    )

    class Meta:
        db_table = "historias_clinicas"  # Nombre de la tabla en MySQL
        indexes = [
            models.Index(
                fields=["fechaAlta"], name="historia_fechaAlta_idx"
            ),  # Índice en fechaAlta
            models.Index(
                fields=["paciente"], name="idPaciente_idx"
            ),  # Índice en idPaciente (ForeignKey)
        ]

    def __str__(self):
        if self.paciente:
            return f"Historia Clínica #{self.id} del paciente {self.paciente.nombre} {self.paciente.apellido}"


class CondicionMedicaHistoria(models.Model):
    historia = models.ForeignKey("HistoriaClinica", on_delete=models.CASCADE)
    condicion = models.ForeignKey("CondicionMedica", on_delete=models.CASCADE)

    class Meta:
        db_table = "condiciones_medicas_historias"
        unique_together = ["historia", "condicion"]

    def __str__(self):
        return f"{self.condicion.nombre} - {self.historia.paciente}"


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

    def __str__(self):
        return f"Signos Vitales de la visita {self.visita.id} para HC {self.visita.historia_clinica.id}"


class ComentariosVisitas(models.Model):
    TIPO_COMENTARIO = [
        ("EVOL", "Evolución"),
        ("INDIC", "Indicaciones"),
    ]
    fecha = models.DateField()
    comentarios = models.TextField()
    tipo = models.CharField(max_length=5, choices=TIPO_COMENTARIO, default="EVOL")
    historia_clinica = models.ForeignKey(
        "HistoriaClinica", on_delete=models.CASCADE, db_column="idHistoriaClinica"
    )

    class Meta:
        db_table = "comentarios_visitas"
        indexes = [
            models.Index(fields=["fecha"]),
            models.Index(fields=["historia_clinica"]),
            models.Index(fields=["fecha", "historia_clinica"]),
        ]


class IndicacionesVisitas(models.Model):
    historia_clinica = models.ForeignKey(
        "HistoriaClinica", 
        on_delete=models.CASCADE,
        db_column="idHistoriaClinica"
    )
    medicamento = models.TextField()
    ochoHoras = models.TextField(null=True)
    doceHoras = models.TextField(null=True)
    dieciochoHoras = models.TextField(null=True)
    veintiunaHoras = models.TextField(null=True)
    fecha = models.DateField()
    eliminado = models.BooleanField(null=True)

    class Meta:
        db_table = "indicaciones_visitas"
        indexes = [
            models.Index(fields=["fecha"]),
            models.Index(fields=["historia_clinica"]),
            models.Index(fields=["historia_clinica", "fecha"]),
        ]