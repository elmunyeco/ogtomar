from django.db import models


class TipoDocumento(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre


class Identificacion(models.Model):
    numero = models.CharField(max_length=20)
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.tipo_documento.nombre}: {self.numero}"


from django.utils import timezone


class Paciente(models.Model):
    SEXO_CHOICES = [
        ("h", "Hombre"),
        ("m", "Mujer"),
    ]

    idTipoDoc = models.PositiveIntegerField()  # Equivalente a int(10) unsigned en MySQL
    numDoc = models.CharField(
        max_length=50
    )  # Cambiado a VARCHAR para búsquedas parciales
    nombre = models.CharField(max_length=50)  # Nombre con búsqueda en índice full-text
    apellido = models.CharField(
        max_length=50
    )  # Apellido con búsqueda en índice full-text
    fechaNac = models.DateField()  # Fecha de nacimiento
    sexo = models.CharField(
        max_length=1, choices=[("M", "Masculino"), ("F", "Femenino"), ("O", "Otro")]
    )  # Char(1)
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

    class Meta:
        db_table = "pacientes"  # Nombre de la tabla en MySQL
        unique_together = ("idTipoDoc", "numDoc")  # Índice único para validar documento
        indexes = [
            models.Index(fields=["nombre"], name="nombre_idx"),  # Índice en nombre
            models.Index(
                fields=["apellido"], name="apellido_idx"
            ),  # Índice en apellido
            models.Index(
                fields=["fechaAlta"], name="paciente_fechaAlta_idx"
            ),  # Índice en fecha de alta
        ]

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class HistoriaClinica(models.Model):
    # Clave foránea a Paciente
    paciente = models.ForeignKey(
        "Paciente", on_delete=models.RESTRICT, related_name="historias_clinicas"
    )

    # Fecha de alta de la historia clínica
    fechaAlta = models.DateField(default=timezone.now)

    # Campo de baja lógica
    deBaja = models.BooleanField(default=False)  # 0 = Activo, 1 = Dado de baja

    class Meta:
        db_table = "historiaclinica"  # Nombre de la tabla en MySQL
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


""" class Visita(models.Model):
    historia_clinica = models.ForeignKey(HistoriaClinica, on_delete=models.CASCADE)
    fecha = models.DateField()
    # otros campos relacionados a la visita


class SignosVitales(models.Model):
    visita = models.ForeignKey(Visita, on_delete=models.CASCADE)
    peso = models.FloatField(null=True, blank=True)  # en kilogramos
    glucemia = models.FloatField(null=True, blank=True)  # en mg/dL
    colesterol = models.FloatField(null=True, blank=True)  # en mg/dL
    presion_sistolica = models.IntegerField(null=True, blank=True)  # en mmHg
    presion_diastolica = models.IntegerField(null=True, blank=True)  # en mmHg

    def __str__(self):
        return f"Signos Vitales de la visita {self.visita.id} para HC {self.visita.historia_clinica.id}"


class CondicionMedica(models.Model):
    TIPO_CHOICES = [
        ("enfermedad", "Enfermedad"),
        ("intervencion", "Intervención"),
        ("otro", "Otro"),
    ]

    orden = models.IntegerField(default=0)  # Campo para definir el orden de aparición

    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default="otro")

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"


class Antecedente(models.Model):
    condicion_medica = models.ForeignKey(CondicionMedica, on_delete=models.CASCADE)
    historia_clinica = models.ForeignKey(HistoriaClinica, on_delete=models.CASCADE)
    fecha = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.condicion.nombre} del tipo {self.condicion.tipo} en {self.historia_clinica.paciente.nombre} {self.historia_clinica.paciente.apellido}"
 """