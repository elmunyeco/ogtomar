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
    obraSocial = models.CharField(max_length=50, null=True, blank=True)  # Obra social
    plan = models.CharField(max_length=50, null=True, blank=True)  # Plan opcional
    afiliado = models.CharField(max_length=50, null=True, blank=True )  # Número de afiliado
    telefono = models.CharField(max_length=50, null=True, blank=True )  # Teléfono
    celular = models.CharField(max_length=50, null=True, blank=True )  # Celular
    profesion = models.CharField(max_length=50, null=True, blank=True )  # Profesión
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
        ordering = ['-fechaAlta']
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


class IndicacionesVisitas(models.Model):
    historia_clinica = models.ForeignKey(
        "HistoriaClinica", on_delete=models.CASCADE, db_column="historia_clinica_id"
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
            models.Index(fields=["fecha"]),
            models.Index(fields=["historia_clinica"]),
            models.Index(fields=["historia_clinica", "fecha"]),
        ]

# Estudios

class EstudioEcocardiograma(models.Model):
    historia = models.ForeignKey(HistoriaClinica, on_delete=models.CASCADE)
    fecha = models.DateField(default=timezone.now)
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    talla = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    presion_sistolica = models.IntegerField(null=True, blank=True)
    presion_diastolica = models.IntegerField(null=True, blank=True)
    
    # Campos para análisis bidimensional
    auricula_izq_diametro = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    area_auricula_izq = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    plano_valvular_aortico = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    septum_diastole = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pared_diastole = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    vent_izq_diastolico = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    vent_izq_sistolico = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    diametro_tsvi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fraccion_simpson = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fraccion_acortamiento = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tapse = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    vent_derecho = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Campos para análisis Doppler
    valvula_pulmonar = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    valvula_aortica = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tracto_vent_izq = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    onda_e_mitral = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    onda_a_mitral = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    onda_e_tricuspidea = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    onda_a_tricuspidea = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Campos adicionales
    strain_longitudinal = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"Ecocardiograma {self.id} - {self.historia.paciente}"
    
    class Meta:
        verbose_name = 'Estudio de Ecocardiograma'
        verbose_name_plural = 'Estudios de Ecocardiograma'

class SegmentoEcocardiograma(models.Model):
    ESTADO_CHOICES = [
        (0, 'No evaluado'),
        (1, 'Normal'),
        (2, 'Hipoquinético'),
        (3, 'Aquinético'),
        (4, 'Disquinético'),
    ]
    
    estudio = models.ForeignKey(EstudioEcocardiograma, on_delete=models.CASCADE, related_name='segmentos')
    numero_segmento = models.IntegerField()
    estado = models.IntegerField(choices=ESTADO_CHOICES, default=0)
    
    def __str__(self):
        return f"Segmento {self.numero_segmento} - Estudio {self.estudio.id}"
    
    class Meta:
        verbose_name = 'Segmento de Ecocardiograma'
        verbose_name_plural = 'Segmentos de Ecocardiograma'
        unique_together = ['estudio', 'numero_segmento']

class ConclusiónEcocardiograma(models.Model):
    SITUS_CHOICES = [
        (1, 'Solitus'),
        (2, 'Inversus'),
        (3, 'Indeterminado'),
    ]
    
    SI_NO_CHOICES = [
        (1, 'No'),
        (2, 'Sí'),
    ]
    
    FUNCION_SISTOLICA_CHOICES = [
        (1, 'Conservada'),
        (2, 'Deterioro de grado leve'),
        (3, 'Deterioro de grado moderado'),
        (4, 'Deterioro de grado severo'),
    ]
    
    FUNCION_DIASTOLICA_CHOICES = [
        (1, 'Normal'),
        (2, 'Patrón de relajación prolongada'),
        (3, 'Patrón pseudonormalizado'),
    ]
    
    MOTILIDAD_CHOICES = [
        (1, 'Normal'),
        (2, 'Anormal'),
    ]
    
    VALVULA_CHOICES = [
        (1, 'Dentro de límites normales'),
        (2, 'Insuficiencia de grado leve'),
        (3, 'Insuficiencia de grado moderado'),
        (4, 'Insuficiencia de grado severo'),
        (5, 'Estenosis de grado leve'),
        (6, 'Estenosis de grado moderado'),
        (7, 'Estenosis de grado severo'),
    ]
    
    PERICARDIO_CHOICES = [
        (1, 'Libre'),
        (2, 'Derrame de grado leve'),
        (3, 'Derrame de grado moderado'),
        (4, 'Derrame de grado Severo'),
    ]

    estudio = models.OneToOneField(EstudioEcocardiograma, on_delete=models.CASCADE, related_name='conclusion')
    
    # Conclusiones específicas
    situs = models.IntegerField(choices=SITUS_CHOICES, null=True, blank=True)
    comentario_situs = models.TextField(blank=True, null=True)
    
    vasos_normoimplantados = models.IntegerField(choices=SI_NO_CHOICES, null=True, blank=True)
    comentario_vasos = models.TextField(blank=True, null=True)
    
    concordancia_atrioventricular = models.IntegerField(choices=SI_NO_CHOICES, null=True, blank=True)
    comentario_concordancia = models.TextField(blank=True, null=True)
    
    auricula_izq = models.CharField(max_length=100, blank=True)  # Almacena valores seleccionados como string separado por comas
    
    ventriculo_izq = models.CharField(max_length=100, blank=True)  # Almacena valores seleccionados como string
    
    funcion_sistolica = models.IntegerField(choices=FUNCION_SISTOLICA_CHOICES, null=True, blank=True)
    
    funcion_diastolica = models.IntegerField(choices=FUNCION_DIASTOLICA_CHOICES, null=True, blank=True)
    
    motilidad_segmentaria = models.IntegerField(choices=MOTILIDAD_CHOICES, null=True, blank=True)
    comentario_motilidad = models.TextField(blank=True, null=True)
    
    valvula_aortica = models.CharField(max_length=50, blank=True)  # Para almacenar múltiples selecciones
    comentario_valvula_aortica = models.TextField(blank=True, null=True)
    
    valvula_mitral = models.CharField(max_length=50, blank=True)
    comentario_valvula_mitral = models.TextField(blank=True, null=True)
    
    valvula_tricuspide = models.CharField(max_length=50, blank=True)
    comentario_valvula_tricuspide = models.TextField(blank=True, null=True)
    
    valvula_pulmonar = models.CharField(max_length=50, blank=True)
    comentario_valvula_pulmonar = models.TextField(blank=True, null=True)
    
    pericardio = models.IntegerField(choices=PERICARDIO_CHOICES, null=True, blank=True)
    comentario_pericardio = models.TextField(blank=True, null=True)
    
    defectos_congenitos = models.IntegerField(choices=SI_NO_CHOICES, null=True, blank=True)
    comentario_defectos = models.TextField(blank=True, null=True)
    
    # Conclusión textual
    conclusion_texto = models.TextField(blank=True)
    comentario_final = models.TextField(blank=True)
    
    def __str__(self):
        return f"Conclusión para estudio {self.estudio.id}"
    
    class Meta:
        verbose_name = 'Conclusión de Ecocardiograma'
        verbose_name_plural = 'Conclusiones de Ecocardiograma'
