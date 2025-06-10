# ecocardiograma/views.py
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

# Importar modelos (ajusta según tu models.py)
from .models import (
    EstudioEcocardiograma, 
    SegmentoEcocardiograma, 
    ConclusiónEcocardiograma
)

# Asumiendo que tienes estos modelos en otra app
from main.models import HistoriaClinica, Paciente


@login_required
def nuevo_estudio(request, historia_id):
    """Vista principal para mostrar el formulario de ecocardiograma"""
    historia = get_object_or_404(HistoriaClinica, id=historia_id)
    
    # Buscar estudio existente o crear contexto para uno nuevo
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
    
    context = {
        'historia': historia,
        'paciente': historia.paciente,
        'estudio': estudio,
        'conclusion': conclusion,
        'segmentos': segmentos,
    }
    
    return render(request, 'ecocardiograma/eco_form.html', context)


@login_required
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
                if valor and valor != '':
                    # Convertir a número si es necesario
                    try:
                        if campo in ['presion_sistolica', 'presion_diastolica']:
                            valor = int(float(valor)) if valor else None
                        else:
                            valor = float(valor) if valor else None
                    except (ValueError, TypeError):
                        valor = None
                    setattr(estudio, campo, valor)
            
            estudio.save()
            
            # 2. Guardar segmentos
            segmentos_data = data.get('segmentos', {})
            if segmentos_data:
                # Eliminar segmentos existentes
                estudio.segmentos.all().delete()
                
                # Crear nuevos segmentos
                for numero, estado in segmentos_data.items():
                    if estado and estado != '0':
                        SegmentoEcocardiograma.objects.create(
                            estudio=estudio,
                            numero_segmento=int(numero),
                            estado=int(estado)
                        )
            
            # 3. Guardar conclusiones
            conclusiones_data = data.get('conclusiones', {})
            if conclusiones_data:
                conclusion, created = ConclusiónEcocardiograma.objects.get_or_create(
                    estudio=estudio
                )
                
                # Actualizar campos de conclusión
                campos_conclusion = [
                    'auricula_izq', 'ventriculo_izq', 'funcion_sistolica',
                    'funcion_diastolica', 'motilidad_segmentaria', 'comentario_motilidad',
                    'pericardio', 'comentario_pericardio', 'defectos_congenitos',
                    'comentario_defectos', 'conclusion_texto', 'comentario_final'
                ]
                
                for campo in campos_conclusion:
                    valor = conclusiones_data.get(campo)
                    if valor is not None:
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


@login_required
def imprimir_estudio(request, estudio_id):
    """Vista para imprimir el estudio"""
    estudio = get_object_or_404(EstudioEcocardiograma, id=estudio_id)
    
    # Obtener conclusión si existe
    try:
        conclusion = estudio.conclusion
    except ConclusiónEcocardiograma.DoesNotExist:
        conclusion = None
    
    # Obtener segmentos
    segmentos = estudio.segmentos.all().order_by('numero_segmento')
    
    context = {
        'estudio': estudio,
        'paciente': estudio.historia.paciente,
        'historia': estudio.historia,
        'conclusion': conclusion,
        'segmentos': segmentos,
    }
    
    return render(request, 'ecocardiograma/imprimir_estudio.html', context)