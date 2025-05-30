# Archivo: ecocardiograma/templatetags/ecocardiograma_tags.py

from django import template
import json
import math

register = template.Library()

@register.filter
def to_json(value):
    """
    Convierte un valor Python a JSON de forma segura para usar en templates
    """
    if value is None:
        return 'null'
    return json.dumps(value)

@register.filter
def get_item(dictionary, key):
    """
    Obtiene un item de un diccionario usando una clave
    """
    return dictionary.get(key)

@register.filter
def mul(value, arg):
    """
    Multiplica un valor por un argumento
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """
    Divide un valor por un argumento
    """
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def pow(value, arg):
    """
    Eleva un valor a una potencia
    """
    try:
        return math.pow(float(value), float(arg))
    except (ValueError, TypeError):
        return 0

@register.filter
def ceil(value):
    """
    Redondea hacia arriba
    """
    try:
        return math.ceil(float(value))
    except (ValueError, TypeError):
        return 0

@register.filter
def split(value, delimiter=','):
    """
    Divide una cadena usando un delimitador
    """
    if not value:
        return []
    return value.split(delimiter)

@register.filter
def contains(value, arg):
    """
    Verifica si un valor contiene otro valor
    """
    try:
        return arg in value
    except (TypeError, AttributeError):
        return False

@register.filter
def default_if_none_or_empty(value, default):
    """
    Retorna un valor por defecto si el valor es None o está vacío
    """
    if value is None or value == '':
        return default
    return value

@register.simple_tag
def calcular_bmi(peso, talla):
    """
    Calcula el BMI dados el peso y la talla
    """
    try:
        peso = float(peso)
        talla = float(talla)
        if peso > 0 and talla > 0:
            return round(peso / (talla * talla), 1)
    except (ValueError, TypeError, ZeroDivisionError):
        pass
    return None

@register.simple_tag
def calcular_fraccion_acortamiento(diastolico, sistolico):
    """
    Calcula la fracción de acortamiento
    """
    try:
        diastolico = float(diastolico)
        sistolico = float(sistolico)
        if diastolico > 0 and sistolico > 0:
            return round(((diastolico - sistolico) / diastolico) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        pass
    return None

@register.simple_tag
def calcular_gradiente(velocidad):
    """
    Calcula el gradiente de presión a partir de la velocidad
    """
    try:
        velocidad = float(velocidad)
        if velocidad > 0:
            return round(velocidad * velocidad * 4, 1)
    except (ValueError, TypeError):
        pass
    return None

@register.inclusion_tag('ecocardiograma/partials/valor_con_unidad.html')
def valor_con_unidad(valor, unidad, placeholder="0.0"):
    """
    Renderiza un campo de valor con su unidad
    """
    return {
        'valor': valor,
        'unidad': unidad,
        'placeholder': placeholder
    }

@register.inclusion_tag('ecocardiograma/partials/campo_calculado.html')
def campo_calculado(valor, unidad):
    """
    Renderiza un campo calculado de solo lectura
    """
    return {
        'valor': valor,
        'unidad': unidad
    }

@register.filter
def get_estado_segmento_display(value):
    """
    Obtiene la descripción del estado de un segmento
    """
    estados = {
        0: 'No evaluado',
        1: 'Normal',
        2: 'Hipoquinético',
        3: 'Aquinético',
        4: 'Disquinético'
    }
    try:
        return estados.get(int(value), 'No evaluado')
    except (ValueError, TypeError):
        return 'No evaluado'

@register.filter
def get_numero_segmento_display(value):
    """
    Obtiene la descripción del número de segmento
    """
    segmentos = {
        1: 'Septum Anterior Basal',
        2: 'Septum Anterior Medio',
        3: 'Septum Basal',
        4: 'Septum Medio',
        5: 'Septum Aplical',
        6: 'Inferior Basal',
        7: 'Inferior Medio',
        8: 'Inferior Aplical',
        9: 'Posterior Basal',
        10: 'Posterior Medio',
        11: 'Lateral Basal',
        12: 'Lateral Medio',
        13: 'Lateral Aplical',
        14: 'Anterior Basal',
        15: 'Anterior Medio',
        16: 'Anterior Aplical'
    }
    try:
        return f"{value}. {segmentos.get(int(value), 'Segmento desconocido')}"
    except (ValueError, TypeError):
        return 'Segmento desconocido'

@register.simple_tag
def get_conclusion_display(conclusion, campo):
    """
    Obtiene la representación legible de un campo de conclusión
    """
    if not conclusion:
        return ''
    
    valor = getattr(conclusion, campo, None)
    if not valor:
        return ''
    
    # Mapeos para diferentes campos
    mapeos = {
        'situs': {
            1: 'Solitus',
            2: 'Inversus',
            3: 'Indeterminado'
        },
        'funcion_sistolica': {
            1: 'Conservada',
            2: 'Deterioro de grado leve',
            3: 'Deterioro de grado moderado',
            4: 'Deterioro de grado severo'
        },
        'funcion_diastolica': {
            1: 'Normal',
            2: 'Patrón de relajación prolongada',
            3: 'Patrón pseudonormalizado'
        },
        'motilidad_segmentaria': {
            1: 'Normal',
            2: 'Anormal'
        },
        'pericardio': {
            1: 'Libre',
            2: 'Derrame de grado leve',
            3: 'Derrame de grado moderado',
            4: 'Derrame de grado severo'
        }
    }
    
    mapeo = mapeos.get(campo, {})
    try:
        return mapeo.get(int(valor), str(valor))
    except (ValueError, TypeError):
        return str(valor)

@register.simple_tag
def url_imprimir_estudio(estudio_id):
    """
    Genera la URL para imprimir un estudio
    """
    from django.urls import reverse
    if estudio_id:
        return reverse('ecocardiograma:imprimir_estudio', args=[estudio_id])
    return '#'