from django.shortcuts import render

# Archivo: ecocardiograma/views.py - Agregar esta función a las vistas existentes

import json
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods

@login_required
@csrf_protect
@require_http_methods(["POST"])
def guardar_todo_ajax(request, historia_id):
    """
    Vista AJAX para guardar todos los datos del ecocardiograma en una sola petición
    """
    try:
        # Parsear los datos JSON del request
        data = json.loads(request.body)
        
        # Obtener la historia clínica
        historia = get_object_or_404(HistoriaClinica, id=historia_id)
        
        # Datos del estudio
        datos_estudio = data.get('estudio', {})
        estudio_id = datos_estudio.get('id')
        
        # Obtener o crear el estudio
        if estudio_id and int(estudio_id) > 0:
            estudio = get_object_or_404(EstudioEcocardiograma, id=estudio_id)
        else:
            estudio = EstudioEcocardiograma(historia=historia)
        
        # Actualizar campos del estudio
        campos_estudio = [
            'peso', 'talla', 'presion_sistolica', 'presion_diastolica',
            'auricula_izq_diametro', 'area_auricula_izq', 'plano_valvular_aortico',
            'septum_diastole', 'pared_diastole', 'vent_izq_diastolico',
            'vent_izq_sistolico', 'diametro_tsvi', 'fraccion_simpson',
            'tapse', 'vent_derecho', 'valvula_pulmonar', 'valvula_aortica',
            'tracto_vent_izq', 'onda_e_mitral', 'onda_a_mitral',
            'onda_e_tricuspidea', 'onda_a_tricuspidea', 'strain_longitudinal'
        ]
        
        for campo in campos_estudio:
            valor = datos_estudio.get(campo)
            if valor is not None and valor != '':
                # Convertir strings vacíos a None para campos numéricos
                if valor == '':
                    valor = None
                else:
                    try:
                        # Intentar convertir a decimal para campos numéricos
                        valor = float(valor) if '.' in str(valor) else int(valor)
                    except (ValueError, TypeError):
                        valor = None
                setattr(estudio, campo, valor)
        
        # Calcular fracción de acortamiento si tenemos los datos
        if estudio.vent_izq_diastolico and estudio.vent_izq_sistolico:
            diastolico = float(estudio.vent_izq_diastolico)
            sistolico = float(estudio.vent_izq_sistolico)
            if diastolico > 0:
                estudio.fraccion_acortamiento = round(((diastolico - sistolico) / diastolico) * 100, 2)
        
        # Guardar el estudio
        estudio.save()
        
        # Guardar segmentos
        datos_segmentos = data.get('segmentos', {})
        if datos_segmentos:
            with transaction.atomic():
                # Eliminar segmentos existentes
                estudio.segmentos.all().delete()
                
                # Crear nuevos segmentos
                for numero_str, estado_str in datos_segmentos.items():
                    try:
                        numero = int(numero_str)
                        estado = int(estado_str)
                        
                        if 1 <= numero <= 16 and estado in [0, 1, 2, 3, 4]:
                            SegmentoEcocardiograma.objects.create(
                                estudio=estudio,
                                numero_segmento=numero,
                                estado=estado
                            )
                    except (ValueError, TypeError):
                        continue
        
        # Guardar conclusiones
        datos_conclusiones = data.get('conclusiones', {})
        if datos_conclusiones:
            # Obtener o crear la conclusión
            conclusion, created = ConclusiónEcocardiograma.objects.get_or_create(
                estudio=estudio
            )
            
            # Campos de texto simples
            campos_texto = [
                'funcion_sistolica', 'funcion_diastolica', 'motilidad_segmentaria',
                'pericardio', 'defectos_congenitos', 'comentario_motilidad',
                'comentario_pericardio', 'comentario_defectos', 'conclusion_texto',
                'comentario_final'
            ]
            
            for campo in campos_texto:
                valor = datos_conclusiones.get(campo)
                if valor is not None:
                    # Convertir a entero para campos de selección
                    if campo in ['funcion_sistolica', 'funcion_diastolica', 'motilidad_segmentaria', 
                                'pericardio', 'defectos_congenitos']:
                        try:
                            valor = int(valor) if valor != '' else None
                        except (ValueError, TypeError):
                            valor = None
                    setattr(conclusion, campo, valor)
            
            # Campos de selección múltiple (ya vienen como strings separados por comas)
            campos_multiples = ['auricula_izq', 'ventriculo_izq']
            for campo in campos_multiples:
                valor = datos_conclusiones.get(campo, '')
                setattr(conclusion, campo, valor)
            
            conclusion.save()
        
        # Respuesta exitosa
        return JsonResponse({
            'success': True,
            'estudio_id': estudio.id,
            'message': 'Datos guardados correctamente'
        })
        
    except HistoriaClinica.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Historia clínica no encontrada'
        }, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


# También actualizar la función nuevo_estudio para pasar mejor los datos al template
@login_required
def nuevo_estudio(request, historia_id=None):
    """
    Vista principal para crear un nuevo estudio de ecocardiograma o editar uno existente.
    """
    # Obtener la historia clínica
    historia = get_object_or_404(HistoriaClinica, id=historia_id)
    
    # Verificar si ya existe un estudio
    estudio = EstudioEcocardiograma.objects.filter(
        historia=historia
    ).order_by('-fecha').first()
    
    # Obtener segmentos si existen
    segmentos_data = []
    if estudio:
        segmentos_data = [
            {
                'numero_segmento': segmento.numero_segmento,
                'estado': segmento.estado
            }
            for segmento in estudio.segmentos.all()
        ]
    
    # Obtener conclusión si existe
    conclusion = None
    if estudio:
        try:
            conclusion = estudio.conclusion
        except ConclusiónEcocardiograma.DoesNotExist:
            pass
    
    # Serializar datos para JavaScript (usando json.dumps para asegurar formato correcto)
    estudio_json = json.dumps({
        'id': estudio.id if estudio else None,
        'peso': float(estudio.peso) if estudio and estudio.peso else None,
        'talla': float(estudio.talla) if estudio and estudio.talla else None,
        'presion_sistolica': estudio.presion_sistolica if estudio else None,
        'presion_diastolica': estudio.presion_diastolica if estudio else None,
        'auricula_izq_diametro': float(estudio.auricula_izq_diametro) if estudio and estudio.auricula_izq_diametro else None,
        'area_auricula_izq': float(estudio.area_auricula_izq) if estudio and estudio.area_auricula_izq else None,
        'plano_valvular_aortico': float(estudio.plano_valvular_aortico) if estudio and estudio.plano_valvular_aortico else None,
        'septum_diastole': float(estudio.septum_diastole) if estudio and estudio.septum_diastole else None,
        'pared_diastole': float(estudio.pared_diastole) if estudio and estudio.pared_diastole else None,
        'vent_izq_diastolico': float(estudio.vent_izq_diastolico) if estudio and estudio.vent_izq_diastolico else None,
        'vent_izq_sistolico': float(estudio.vent_izq_sistolico) if estudio and estudio.vent_izq_sistolico else None,
        'diametro_tsvi': float(estudio.diametro_tsvi) if estudio and estudio.diametro_tsvi else None,
        'fraccion_simpson': float(estudio.fraccion_simpson) if estudio and estudio.fraccion_simpson else None,
        'tapse': float(estudio.tapse) if estudio and estudio.tapse else None,
        'vent_derecho': float(estudio.vent_derecho) if estudio and estudio.vent_derecho else None,
        'valvula_pulmonar': float(estudio.valvula_pulmonar) if estudio and estudio.valvula_pulmonar else None,
        'valvula_aortica': float(estudio.valvula_aortica) if estudio and estudio.valvula_aortica else None,
        'tracto_vent_izq': float(estudio.tracto_vent_izq) if estudio and estudio.tracto_vent_izq else None,
        'onda_e_mitral': float(estudio.onda_e_mitral) if estudio and estudio.onda_e_mitral else None,
        'onda_a_mitral': float(estudio.onda_a_mitral) if estudio and estudio.onda_a_mitral else None,
        'onda_e_tricuspidea': float(estudio.onda_e_tricuspidea) if estudio and estudio.onda_e_tricuspidea else None,
        'onda_a_tricuspidea': float(estudio.onda_a_tricuspidea) if estudio and estudio.onda_a_tricuspidea else None,
        'strain_longitudinal': float(estudio.strain_longitudinal) if estudio and estudio.strain_longitudinal else None,
    }) if estudio else 'null'
    
    conclusion_json = json.dumps({
        'auricula_izq': conclusion.auricula_izq if conclusion else '',
        'ventriculo_izq': conclusion.ventriculo_izq if conclusion else '',
        'funcion_sistolica': conclusion.funcion_sistolica if conclusion else '',
        'funcion_diastolica': conclusion.funcion_diastolica if conclusion else '',
        'motilidad_segmentaria': conclusion.motilidad_segmentaria if conclusion else '',
        'comentario_motilidad': conclusion.comentario_motilidad if conclusion else '',
        'pericardio': conclusion.pericardio if conclusion else '',
        'comentario_pericardio': conclusion.comentario_pericardio if conclusion else '',
        'defectos_congenitos': conclusion.defectos_congenitos if conclusion else '',
        'comentario_defectos': conclusion.comentario_defectos if conclusion else '',
        'conclusion_texto': conclusion.conclusion_texto if conclusion else '',
        'comentario_final': conclusion.comentario_final if conclusion else '',
    }) if conclusion else 'null'
    
    segmentos_json = json.dumps(segmentos_data)
    
    context = {
        'paciente': historia.paciente,
        'historia': historia,
        'estudio': estudio,
        'conclusion': conclusion,
        'segmentos': segmentos_data,
        # Datos serializados para JavaScript
        'estudio_json': estudio_json,
        'conclusion_json': conclusion_json,
        'segmentos_json': segmentos_json,
    }
    
    return render(request, 'ecocardiograma/eco_form_optimizado.html', context)
# Create your views here.
