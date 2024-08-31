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

class Paciente(models.Model):
    SEXO_CHOICES = [
        ("h", "Hombre"),
        ("m", "Mujer"),
        ("f", "Femenino"),
    ]

    id = models.AutoField(primary_key=True)
    idtipodoc = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE)  # type: ignore
    mail = models.EmailField(max_length=254, blank=True, null=True)
    plan = models.CharField(max_length=100, blank=True, null=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    debaja = models.BooleanField(default=False)
    nombre = models.CharField(max_length=100)
    numdoc = models.CharField(max_length=20)
    celular = models.CharField(max_length=20, blank=True, null=True)
    afiliado = models.CharField(max_length=20, blank=True, null=True)
    apellido = models.CharField(max_length=100)
    fechanac = models.DateField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    fechaalta = models.DateField()
    localidad = models.CharField(max_length=100)
    profesion = models.CharField(max_length=100, blank=True, null=True)
    referente = models.CharField(max_length=100, blank=True, null=True)
    obrasocial = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


from django.utils import timezone

class HistoriaClinica(models.Model):
    paciente = models.OneToOneField(Paciente, on_delete=models.CASCADE)
    fechaalta = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Historia Clínica de {self.paciente.nombre} {self.paciente.apellido}"

class Visita(models.Model):
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
        ('enfermedad', 'Enfermedad'),
        ('intervencion', 'Intervención'),
        ('otro', 'Otro'),
    ]
    
    orden = models.IntegerField(default=0)  # Campo para definir el orden de aparición

    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='otro')

    
    def __str__(self):
        return f"{self.nombre} ({self.tipo})"

class Antecedente(models.Model):
    condicion_medica = models.ForeignKey(CondicionMedica, on_delete=models.CASCADE)
    historia_clinica = models.ForeignKey(HistoriaClinica, on_delete=models.CASCADE)
    fecha = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.condicion.nombre} del tipo {self.condicion.tipo} en {self.historia_clinica.paciente.nombre} {self.historia_clinica.paciente.apellido}"