# ecocardiograma/views.py
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from main.utils import static_file_url
from django.forms.models import model_to_dict
from django.template.loader import render_to_string
from weasyprint import HTML

# Importar modelos (ajusta según tu models.py)
from .models import (
    EstudioEcocardiograma,
    SegmentoEcocardiograma,
    ConclusiónEcocardiograma
)

# Asumiendo que tienes estos modelos en otra app
from main.models import HistoriaClinica, Paciente


def sandbox_or_login(view_func):
    if getattr(settings, 'USE_SANDBOX_DB', False):
        return view_func
    return login_required(view_func)


def _to_float(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip().replace(',', '.')
    if value == '':
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip().replace(',', '.')
    if value == '':
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _get_historia_from_post(request):
    id_hc = request.POST.get('idHC') or request.POST.get('historia_id')
    if not id_hc:
        return None
    try:
        return HistoriaClinica.objects.get(id=int(id_hc))
    except (HistoriaClinica.DoesNotExist, ValueError, TypeError):
        return None


def _get_estudio_from_post(request):
    id_estudio = request.POST.get('idEstudio') or request.POST.get('idEco') or request.POST.get('estudio_id')
    if id_estudio:
        try:
            return EstudioEcocardiograma.objects.get(id=int(id_estudio))
        except (EstudioEcocardiograma.DoesNotExist, ValueError, TypeError):
            pass
    historia = _get_historia_from_post(request)
    if historia:
        estudio = EstudioEcocardiograma.objects.filter(historia=historia).first()
        if estudio:
            return estudio
        return EstudioEcocardiograma.objects.create(historia=historia)
    return None


def _present(value):
    if value is None:
        return False
    try:
        return float(value) != 0
    except (TypeError, ValueError):
        return str(value).strip() != ''


def _gradiente(velocidad):
    try:
        v = float(velocidad)
        if v == 0:
            return None
        return round(4 * (v ** 2))
    except (TypeError, ValueError):
        return None


def _map_choices(value, mapping):
    if value is None or value == '':
        return None
    try:
        return mapping.get(int(value))
    except (TypeError, ValueError):
        return None


def _map_csv_choices(value, mapping):
    if not value:
        return []
    if isinstance(value, list):
        values = value
    else:
        values = [v.strip() for v in str(value).split(',') if v.strip()]
    labels = []
    for v in values:
        try:
            label = mapping.get(int(v))
            if label:
                labels.append(label)
        except (TypeError, ValueError):
            continue
    return labels


@sandbox_or_login
def nuevo_estudio(request, historia_id):
    """Vista principal para mostrar el formulario de ecocardiograma"""
    historia = get_object_or_404(HistoriaClinica, id=historia_id)
    
    # Buscar estudio existente o crear contexto para uno nuevo
    action = (request.GET.get("action") or "").lower()
    force_new = action in ("crear", "nuevo")
    estudio = None
    if action == "recuperar":
        estudio_id = request.GET.get("estudio")
        if estudio_id:
            estudio = EstudioEcocardiograma.objects.filter(pk=estudio_id, historia=historia).first()
    if not estudio and not force_new:
        estudio = EstudioEcocardiograma.objects.filter(historia=historia).first()
    
    # Buscar conclusión existente
    conclusion = None
    if estudio:
        try:
            conclusion = estudio.conclusion
        except ConclusiónEcocardiograma.DoesNotExist:
            conclusion = None
    
    # Buscar segmentos existentes
    segmentos = []
    if estudio:
        segmentos = list(estudio.segmentos.all().values('numero_segmento', 'estado'))
    
    estudio_json = None
    if estudio:
        estudio_json = model_to_dict(estudio)

    conclusion_json = None
    if conclusion:
        conclusion_json = model_to_dict(conclusion)

    context = {
        'historia': historia,
        'paciente': historia.paciente,
        'estudio_id': estudio.id if estudio else 0,
        'estudio': estudio_json,
        'conclusion': conclusion_json,
        'segmentos': segmentos,
    }
    
    return render(request, 'ecocardiograma/eco_form.html', context)


@sandbox_or_login
@csrf_exempt
def guardar_todo_ajax(request, historia_id):
    """Vista AJAX para guardar todo el estudio de una vez"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        historia = get_object_or_404(HistoriaClinica, id=historia_id)
        data = json.loads(request.body)
        
        with transaction.atomic():
            # 1. Crear o actualizar estudio
            estudio_data = data.get('estudio', {})
            estudio_id = estudio_data.get('id')
            
            if estudio_id and estudio_id != 'null':
                estudio = get_object_or_404(EstudioEcocardiograma, id=estudio_id)
            else:
                estudio = EstudioEcocardiograma(historia=historia)
            
            # Actualizar campos del estudio
            campos_estudio = [
                'peso', 'talla', 'presion_sistolica', 'presion_diastolica',
                'auricula_izq_diametro', 'area_auricula_izq', 'plano_valvular_aortico',
                'septum_diastole', 'pared_diastole', 'vent_izq_diastolico',
                'vent_izq_sistolico', 'diametro_tsvi', 'fraccion_simpson',
                'fraccion_acortamiento', 'tapse', 'vent_derecho',
                'valvula_pulmonar', 'valvula_aortica', 'tracto_vent_izq',
                'onda_e_mitral', 'onda_a_mitral', 'onda_e_tricuspidea',
                'onda_a_tricuspidea', 'strain_longitudinal'
            ]
            
            for campo in campos_estudio:
                valor = estudio_data.get(campo)
                if valor is not None and valor != '':
                    try:
                        if campo in ['presion_sistolica', 'presion_diastolica']:
                            valor = int(float(str(valor).replace(',', '.')))
                        else:
                            valor = float(str(valor).replace(',', '.'))
                    except (ValueError, TypeError):
                        valor = None
                    setattr(estudio, campo, valor)
            
            estudio.save()
            
            # 2. Guardar segmentos (guardar los 16, incluyendo 0)
            segmentos_data = data.get('segmentos', {}) or {}
            if segmentos_data is not None:
                for i in range(1, 17):
                    estado = segmentos_data.get(str(i), segmentos_data.get(i))
                    if estado is None or estado == '':
                        continue
                    try:
                        estado_int = int(estado)
                    except (ValueError, TypeError):
                        continue
                    SegmentoEcocardiograma.objects.update_or_create(
                        estudio=estudio,
                        numero_segmento=i,
                        defaults={'estado': estado_int}
                    )
            
            # 3. Guardar conclusiones
            conclusiones_data = data.get('conclusiones', {})
            if conclusiones_data:
                conclusion, created = ConclusiónEcocardiograma.objects.get_or_create(
                    estudio=estudio
                )
                
                # Actualizar campos de conclusión
                campos_conclusion = [
                    'situs', 'comentario_situs',
                    'vasos_normoimplantados', 'comentario_vasos',
                    'concordancia_atrioventricular', 'comentario_concordancia',
                    'auricula_izq', 'ventriculo_izq', 'funcion_sistolica',
                    'funcion_diastolica', 'motilidad_segmentaria', 'comentario_motilidad',
                    'valvula_aortica', 'comentario_valvula_aortica',
                    'valvula_mitral', 'comentario_valvula_mitral',
                    'valvula_tricuspide', 'comentario_valvula_tricuspide',
                    'valvula_pulmonar', 'comentario_valvula_pulmonar',
                    'pericardio', 'comentario_pericardio', 'defectos_congenitos',
                    'comentario_defectos', 'conclusion_texto', 'comentario_final'
                ]
                
                for campo in campos_conclusion:
                    valor = conclusiones_data.get(campo)
                    if valor is not None:
                        if campo in [
                            'situs', 'vasos_normoimplantados', 'concordancia_atrioventricular',
                            'funcion_sistolica', 'funcion_diastolica', 'motilidad_segmentaria',
                            'pericardio', 'defectos_congenitos'
                        ]:
                            setattr(conclusion, campo, _to_int(valor))
                        else:
                            setattr(conclusion, campo, valor)
                
                conclusion.save()
        
        return JsonResponse({
            'success': True,
            'estudio_id': estudio.id,
            'message': 'Estudio guardado correctamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@sandbox_or_login
@require_POST
@csrf_exempt
def guardar_paciente(request):
    """Legacy: guarda datos del paciente y retorna id de estudio"""
    estudio = _get_estudio_from_post(request)
    if not estudio:
        return JsonResponse(False, safe=False)

    estudio.peso = _to_float(request.POST.get('inputPeso')) or 0
    estudio.talla = _to_float(request.POST.get('inputTalla')) or 0
    estudio.presion_sistolica = _to_int(request.POST.get('inputPas')) or 0
    estudio.presion_diastolica = _to_int(request.POST.get('inputPad')) or 0
    estudio.save()

    return JsonResponse(estudio.id, safe=False)


@sandbox_or_login
@require_POST
@csrf_exempt
def guardar_bidimensional(request):
    """Legacy: guarda análisis bidimensional"""
    estudio = _get_estudio_from_post(request)
    if not estudio:
        return JsonResponse(False, safe=False)

    estudio.auricula_izq_diametro = _to_float(request.POST.get('auIzqDiametro')) or 0
    estudio.area_auricula_izq = _to_float(request.POST.get('areaAuriculaIzq')) or 0
    estudio.plano_valvular_aortico = _to_float(request.POST.get('planoValvularAortico')) or 0
    estudio.septum_diastole = _to_float(request.POST.get('septumDiastole')) or 0
    estudio.pared_diastole = _to_float(request.POST.get('paredDiastole')) or 0
    estudio.vent_izq_diastolico = _to_float(request.POST.get('ventIzqDiastolico')) or 0
    estudio.vent_izq_sistolico = _to_float(request.POST.get('ventIzqSistolico')) or 0
    estudio.diametro_tsvi = _to_float(request.POST.get('diametroTsvi')) or 0
    estudio.fraccion_simpson = _to_float(request.POST.get('fraccionSimpson')) or 0
    estudio.fraccion_acortamiento = _to_float(request.POST.get('fraccionAcortamiento')) or 0
    estudio.tapse = _to_float(request.POST.get('tapse')) or 0
    estudio.vent_derecho = _to_float(request.POST.get('ventDerecho')) or 0
    estudio.save()

    return JsonResponse(True, safe=False)


@sandbox_or_login
@require_POST
@csrf_exempt
def guardar_coppler(request):
    """Legacy: guarda análisis doppler"""
    estudio = _get_estudio_from_post(request)
    if not estudio:
        return JsonResponse(False, safe=False)

    estudio.valvula_pulmonar = _to_float(request.POST.get('valvulaPulmonar')) or 0
    estudio.valvula_aortica = _to_float(request.POST.get('valvulaAortica')) or 0
    estudio.tracto_vent_izq = _to_float(request.POST.get('tractoVentIzq')) or 0
    estudio.onda_e_mitral = _to_float(request.POST.get('ondaEMitral')) or 0
    estudio.onda_a_mitral = _to_float(request.POST.get('ondaAMitral')) or 0
    estudio.onda_e_tricuspidea = _to_float(request.POST.get('ondaETricuspidea')) or 0
    estudio.onda_a_tricuspidea = _to_float(request.POST.get('ondaATricuspidea')) or 0
    # Legacy usa auIzqDiametro para strain longitudinal
    strain = request.POST.get('strainLongitudinal') or request.POST.get('auIzqDiametro')
    estudio.strain_longitudinal = _to_float(strain) or 0
    estudio.save()

    return JsonResponse(True, safe=False)


@sandbox_or_login
@require_POST
@csrf_exempt
def guardar_segmentos(request):
    """Legacy: guarda motilidad segmentaria"""
    estudio = _get_estudio_from_post(request)
    if not estudio:
        return JsonResponse(False, safe=False)

    # Guardar los 16 segmentos (incluye 0)
    for i in range(1, 17):
        valor = request.POST.get(f'segmento{i}')
        estado = _to_int(valor)
        if estado is None:
            continue
        SegmentoEcocardiograma.objects.update_or_create(
            estudio=estudio,
            numero_segmento=i,
            defaults={'estado': estado}
        )

    return JsonResponse(True, safe=False)


@sandbox_or_login
@require_POST
@csrf_exempt
def guardar_conclusiones(request):
    """Legacy: guarda conclusiones (items 1..14 y comentarios)"""
    estudio = _get_estudio_from_post(request)
    if not estudio:
        return JsonResponse(False, safe=False)

    conclusion, _ = ConclusiónEcocardiograma.objects.get_or_create(estudio=estudio)

    # Mapear items
    conclusion.auricula_izq = request.POST.get('item_1', '') or ''
    conclusion.ventriculo_izq = request.POST.get('item_2', '') or ''
    conclusion.funcion_sistolica = _to_int(request.POST.get('item_3'))
    conclusion.funcion_diastolica = _to_int(request.POST.get('item_4'))
    conclusion.motilidad_segmentaria = _to_int(request.POST.get('item_5'))
    conclusion.comentario_motilidad = request.POST.get('comentario_5', '') or ''

    conclusion.valvula_aortica = request.POST.get('item_6', '') or ''
    conclusion.comentario_valvula_aortica = request.POST.get('comentario_6', '') or ''
    conclusion.valvula_mitral = request.POST.get('item_7', '') or ''
    conclusion.comentario_valvula_mitral = request.POST.get('comentario_7', '') or ''
    conclusion.valvula_tricuspide = request.POST.get('item_8', '') or ''
    conclusion.comentario_valvula_tricuspide = request.POST.get('comentario_8', '') or ''
    conclusion.valvula_pulmonar = request.POST.get('item_9', '') or ''
    conclusion.comentario_valvula_pulmonar = request.POST.get('comentario_9', '') or ''

    conclusion.pericardio = _to_int(request.POST.get('item_10'))
    conclusion.comentario_pericardio = request.POST.get('comentario_10', '') or ''
    conclusion.defectos_congenitos = _to_int(request.POST.get('item_11'))
    conclusion.comentario_defectos = request.POST.get('comentario_11', '') or ''

    conclusion.situs = _to_int(request.POST.get('item_12'))
    conclusion.comentario_situs = request.POST.get('comentario_12', '') or ''
    conclusion.vasos_normoimplantados = _to_int(request.POST.get('item_13'))
    conclusion.comentario_vasos = request.POST.get('comentario_13', '') or ''
    conclusion.concordancia_atrioventricular = _to_int(request.POST.get('item_14'))
    conclusion.comentario_concordancia = request.POST.get('comentario_14', '') or ''

    conclusion.save()
    return JsonResponse(True, safe=False)


@sandbox_or_login
@require_POST
@csrf_exempt
def guardar_conclusion_b(request):
    """Legacy: guarda conclusión B"""
    estudio = _get_estudio_from_post(request)
    if not estudio:
        return JsonResponse(False, safe=False)
    conclusion, _ = ConclusiónEcocardiograma.objects.get_or_create(estudio=estudio)
    conclusion.conclusion_texto = request.POST.get('conclusionesB', '') or ''
    conclusion.save()
    return JsonResponse(True, safe=False)


@sandbox_or_login
@require_POST
@csrf_exempt
def guardar_comentario_final(request):
    """Legacy: guarda comentario final"""
    estudio = _get_estudio_from_post(request)
    if not estudio:
        return JsonResponse(False, safe=False)
    conclusion, _ = ConclusiónEcocardiograma.objects.get_or_create(estudio=estudio)
    conclusion.comentario_final = request.POST.get('comentarioFinal', '') or ''
    conclusion.save()
    return JsonResponse(True, safe=False)


@sandbox_or_login
def listar_estudios(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, id=historia_id)
    estudios = (
        EstudioEcocardiograma.objects.filter(historia=historia)
        .order_by("-id")
        .values_list("id", "fecha")
    )
    lines = [f"<div>{eid} - {fecha.strftime('%Y-%m-%d')}</div>" for eid, fecha in estudios]
    if not lines:
        lines = ["<div>Sin estudios</div>"]
    return HttpResponse("\n".join(lines))


@sandbox_or_login
def imprimir_estudio(request, estudio_id):
    """Vista para imprimir el estudio"""
    estudio = get_object_or_404(EstudioEcocardiograma, id=estudio_id)
    
    # Obtener conclusión si existe
    try:
        conclusion = estudio.conclusion
    except ConclusiónEcocardiograma.DoesNotExist:
        conclusion = None
    
    # Segmentos (si faltan, default Normal)
    segmentos_map = {s.numero_segmento: s.estado for s in estudio.segmentos.all()}
    segmentos_base = []
    for i in range(1, 17):
        estado = segmentos_map.get(i, 1)
        segmentos_base.append({'numero': i, 'estado': estado})
    segmentos_all_normal = all(s['estado'] == 1 for s in segmentos_base)

    estado_labels = {
        0: 'No evaluado',
        1: 'Normoquinetico',
        2: 'Hipoquinético',
        3: 'Aquinético',
        4: 'Disquinético',
    }
    estado_colores = {
        0: '#FFFFFF',
        1: '#FFFF00',
        2: '#FF7700',
        3: '#FF0000',
        4: '#0000FF',
    }

    segmento_nombres = {
        1: "Septum Anterior Basal - LAD",
        2: "Septum Anterior Medio - LAD",
        3: "Septum Basal - RCA",
        4: "Septum Medio - RCA",
        5: "Septum Apical - LAD",
        6: "Inferior Basal - RCA",
        7: "Inferior Medio - RCA",
        8: "Inferior Apical - LAD",
        9: "Posterior Basal - CX",
        10: "Posterior Medio - CX",
        11: "Lateral Basal - CX",
        12: "Lateral Medio - CX",
        13: "Lateral Apical - LAD",
        14: "Anterior Basal - LAD",
        15: "Anterior Medio - LAD",
        16: "Anterior Apical - LAD",
    }

    segmentos_detalle = []
    segmentos_colores = {}
    segmentos_estado = {}
    for s in segmentos_base:
        numero = s['numero']
        estado = s['estado']
        segmentos_detalle.append(
            {
                'numero': numero,
                'nombre': segmento_nombres.get(numero, f"Segmento {numero}"),
                'estado': estado_labels.get(estado, 'No evaluado')
            }
        )
        segmentos_colores[numero] = estado_colores.get(estado, '#FFFFFF')
        segmentos_estado[numero] = estado_labels.get(estado, 'No evaluado')

    # Secciones de impresión
    bidimensional_rows = []
    if _present(estudio.auricula_izq_diametro):
        bidimensional_rows.append(('Aurícula izquierda diámetro A-P', estudio.auricula_izq_diametro, 'mm'))
    if _present(estudio.area_auricula_izq):
        bidimensional_rows.append(('Área aurícula izquierda', estudio.area_auricula_izq, 'cm²'))
    if _present(estudio.plano_valvular_aortico):
        bidimensional_rows.append(('Plano valvular aórtico', estudio.plano_valvular_aortico, 'mm'))
    if _present(estudio.septum_diastole):
        bidimensional_rows.append(('Septum interventricular en diástole', estudio.septum_diastole, 'mm'))
    if _present(estudio.pared_diastole):
        bidimensional_rows.append(('Pared posterior en diástole', estudio.pared_diastole, 'mm'))
    if _present(estudio.vent_izq_diastolico):
        bidimensional_rows.append(('Diámetro ventrículo izquierdo diastólico', estudio.vent_izq_diastolico, 'mm'))
    if _present(estudio.vent_izq_sistolico):
        bidimensional_rows.append(('Diámetro ventrículo izquierdo sistólico', estudio.vent_izq_sistolico, 'mm'))
    if _present(estudio.fraccion_simpson):
        bidimensional_rows.append(("Fracción de eyección por Simpson's", estudio.fraccion_simpson, '%'))
    if _present(estudio.fraccion_acortamiento):
        bidimensional_rows.append(('Fracción de acortamiento', estudio.fraccion_acortamiento, '%'))
    if _present(estudio.tapse):
        bidimensional_rows.append(('TAPSE', estudio.tapse, 'mm'))
    if _present(estudio.vent_derecho):
        bidimensional_rows.append(('Diámetro de ventrículo derecho', estudio.vent_derecho, 'mm'))

    doppler_rows = []
    if _present(estudio.valvula_pulmonar):
        doppler_rows.append(('Válvula pulmonar', estudio.valvula_pulmonar, _gradiente(estudio.valvula_pulmonar)))
    if _present(estudio.valvula_aortica):
        doppler_rows.append(('Válvula aórtica', estudio.valvula_aortica, _gradiente(estudio.valvula_aortica)))
    if _present(estudio.tracto_vent_izq):
        doppler_rows.append(('Tracto de salida ventrículo izquierdo', estudio.tracto_vent_izq, _gradiente(estudio.tracto_vent_izq)))
    if _present(estudio.onda_e_mitral) or _present(estudio.onda_a_mitral):
        doppler_rows.append(('Válvula mitral (Onda E/A)', f"{estudio.onda_e_mitral or '-'} / {estudio.onda_a_mitral or '-'}", _gradiente(estudio.onda_e_mitral)))
    if _present(estudio.onda_e_tricuspidea) or _present(estudio.onda_a_tricuspidea):
        doppler_rows.append((
            'Válvula tricuspídea (Onda E/A)',
            f"{estudio.onda_e_tricuspidea or '-'} / {estudio.onda_a_tricuspidea or '-'}",
            _gradiente(estudio.onda_e_tricuspidea)
        ))
    if _present(estudio.strain_longitudinal):
        doppler_rows.append(('Strain longitudinal global', f"{estudio.strain_longitudinal}", None))

    conclusion_lines = []
    if conclusion:
        mapa_situs = {1: 'Solitus', 2: 'Inversus', 3: 'Indeterminado'}
        mapa_si_no = {1: 'No', 2: 'Sí'}
        mapa_func_sis = {1: 'Conservada', 2: 'Deterioro de grado leve', 3: 'Deterioro de grado moderado', 4: 'Deterioro de grado severo'}
        mapa_func_dia = {1: 'Normal', 2: 'Patrón de relajación prolongada', 3: 'Patrón pseudonormalizado'}
        mapa_mot = {1: 'Normal', 2: 'Anormal'}
        mapa_valvula = {
            1: 'Dentro de límites normales',
            2: 'Insuficiencia de grado leve',
            3: 'Insuficiencia de grado moderado',
            4: 'Insuficiencia de grado severo',
            5: 'Estenosis de grado leve',
            6: 'Estenosis de grado moderado',
            7: 'Estenosis de grado severo',
        }
        mapa_pericardio = {1: 'Libre', 2: 'Derrame de grado leve', 3: 'Derrame de grado moderado', 4: 'Derrame de grado severo'}

        auricula_map = {
            1: 'Normal',
            2: 'Ligeramente dilatada',
            3: 'Con dilatación de grado moderado',
            4: 'Con severa dilatación',
            5: 'Con presencia de imagen compatible con trombo en su interior',
        }
        ventriculo_map = {
            1: 'Con diámetros y espesores parietales conservados',
            2: 'Levemente dilatado',
            3: 'Moderadamente dilatado',
            4: 'Severamente dilatado',
            5: 'Hipertrofia concéntrica',
            6: 'Hipertrofia excéntrica',
            7: 'Con hipertrofia del septum interventricular',
        }

        def add_line(label, value, comment=None):
            if value:
                line = f"{label}: {value}"
                if comment:
                    line = f"{line}. {comment}"
                conclusion_lines.append(line)

        add_line('Situs', _map_choices(conclusion.situs, mapa_situs), conclusion.comentario_situs)
        add_line('Vasos normo implantados', _map_choices(conclusion.vasos_normoimplantados, mapa_si_no), conclusion.comentario_vasos)
        add_line('Concordancia atrioventricular', _map_choices(conclusion.concordancia_atrioventricular, mapa_si_no), conclusion.comentario_concordancia)

        auricula_vals = _map_csv_choices(conclusion.auricula_izq, auricula_map)
        if auricula_vals:
            add_line('Aurícula izquierda', ', '.join(auricula_vals))

        ventriculo_vals = _map_csv_choices(conclusion.ventriculo_izq, ventriculo_map)
        if ventriculo_vals:
            add_line('Ventrículo izquierdo', ', '.join(ventriculo_vals))

        add_line('Función sistólica del ventrículo izquierdo', _map_choices(conclusion.funcion_sistolica, mapa_func_sis))
        add_line('Función diastólica del ventrículo izquierdo', _map_choices(conclusion.funcion_diastolica, mapa_func_dia))
        add_line('Motilidad segmentaria', _map_choices(conclusion.motilidad_segmentaria, mapa_mot), conclusion.comentario_motilidad)

        valv_a = _map_csv_choices(conclusion.valvula_aortica, mapa_valvula)
        if valv_a:
            add_line('Válvula aórtica', ', '.join(valv_a), conclusion.comentario_valvula_aortica)
        valv_m = _map_csv_choices(conclusion.valvula_mitral, mapa_valvula)
        if valv_m:
            add_line('Válvula mitral', ', '.join(valv_m), conclusion.comentario_valvula_mitral)
        valv_t = _map_csv_choices(conclusion.valvula_tricuspide, mapa_valvula)
        if valv_t:
            add_line('Válvula tricúspide', ', '.join(valv_t), conclusion.comentario_valvula_tricuspide)
        valv_p = _map_csv_choices(conclusion.valvula_pulmonar, mapa_valvula)
        if valv_p:
            add_line('Válvula pulmonar', ', '.join(valv_p), conclusion.comentario_valvula_pulmonar)

        add_line('Pericardio', _map_choices(conclusion.pericardio, mapa_pericardio), conclusion.comentario_pericardio)
        add_line('Imágenes agregadas y/o defectos congénitos', _map_choices(conclusion.defectos_congenitos, mapa_si_no), conclusion.comentario_defectos)
    
    context = {
        'estudio': estudio,
        'paciente': estudio.historia.paciente,
        'historia': estudio.historia,
        'conclusion': conclusion,
        'segmentos': segmentos_detalle,
        'segmentos_colores': segmentos_colores,
        'segmentos_estado': segmentos_estado,
        'segmentos_all_normal': segmentos_all_normal,
        'bidimensional_rows': bidimensional_rows,
        'doppler_rows': doppler_rows,
        'conclusion_lines': conclusion_lines,
        'print_logo_path': static_file_url("main/images/logo_omar_prieto.svg"),
        'print_site_text': "www.cardioprieto.com",
        'print_header_text': "Consultorio Cardiológico Doctor Omar Prieto",
        'print_css_path': static_file_url("main/css/print.css"),
        'print_segmentos_path': static_file_url("ecocardiograma/images/segmentos.png"),
        'print_show_signature': request.GET.get('firma') == '1',
        'show_peso': _present(estudio.peso),
        'show_talla': _present(estudio.talla),
        'show_pas': _present(estudio.presion_sistolica),
        'show_pad': _present(estudio.presion_diastolica),
    }
    
    html = render_to_string("ecocardiograma/imprimir_estudio.html", context)
    pdf = HTML(string=html).write_pdf()
    filename = f"ecocardiograma_{estudio_id}_{estudio.historia_id}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename={filename}"
    return response
