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
    idTipoDoc_temp = models.IntegerField(
        null=True, blank=True
    )  # Campo temporal para migrar

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


class HistoriaClinica(models.Model):

    # Fecha de alta de la historia clínica
    fechaAlta = models.DateField(default=timezone.now)

    # Clave foránea a Paciente
    paciente = models.ForeignKey(
        "Paciente", on_delete=models.RESTRICT, related_name="historias_clinicas"
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


class CondicionMedica(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, blank=False, null=False)
    orden = models.PositiveIntegerField(db_index=True, blank=False, null=False)

    class Meta:
        db_table = "econdiciones_medicas"
        verbose_name = "Condicion"
        verbose_name_plural = "CondicionesMedicas"
        ordering = ["orden"]

    def __str__(self):
        return self.nombre
    
class CondicionMedicaPaciente(models.Model):
    historia = models.ForeignKey(HistoriaClinica, on_delete=models.CASCADE)
    condicion = models.ForeignKey(CondicionMedica, on_delete=models.CASCADE)
    fecha = models.DateTimeField(default=timezone.now)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'condiciones_medicas_pacientes'
        verbose_name = "Antecedente"
        verbose_name_plural = "Antecedentes"


""" class Visita(models.Model):
    historia_clinica = models.ForeignKey(HistoriaClinica, on_delete=models.CASCADE)
    fecha = models.DateField()
    # otros campos relacionados a la visita
"""

class SignosVitales(models.Model):
    historia = models.ForeignKey(HistoriaClinica, on_delete=models.CASCADE)
    fecha = models.DateTimeField(default=timezone.now)
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