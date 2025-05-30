from django.db import models
from django.utils import timezone
from main.models import HistoriaClinica

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
        db_table = "estudios_ecocardiograma"
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
        db_table = "segmentos_ecocardiograma"
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
        db_table = "conclusiones_ecocardiograma"
        verbose_name = 'Conclusión de Ecocardiograma'
        verbose_name_plural = 'Conclusiones de Ecocardiograma'
