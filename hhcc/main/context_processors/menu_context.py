def menu_context(request):
    """
    Context processor que proporciona información sobre el menú y breadcrumbs
    """
    # URL actual para determinar la sección activa
    current_path = request.path.strip('/')
    
    # Determinar la sección activa
    active_section = ''
    if current_path == '' or current_path == 'index.html':
        active_section = 'inicio'
    elif 'pacientes' in current_path:
        active_section = 'pacientes'
    elif 'historias' in current_path or current_path.startswith('h') and current_path.endswith('_html'):
        active_section = 'historias'
    elif 'ordenes' in current_path:
        active_section = 'ordenes'
    
    # Generar breadcrumbs según la URL actual
    breadcrumbs = [{'label': 'Inicio', 'url': '/'}]
    
    # Añadir breadcrumbs según la sección
    if active_section == 'pacientes':
        breadcrumbs.append({'label': 'Pacientes', 'url': '/pacientes/'})
        
        # Subpáginas de pacientes
        if 'guardar_paciente' in current_path:
            breadcrumbs.append({'label': 'Nuevo Paciente', 'url': None})
        elif 'listar_buscar_pacientes' in current_path:
            breadcrumbs.append({'label': 'Buscar Pacientes', 'url': None})
    
    elif active_section == 'historias':
        breadcrumbs.append({'label': 'Historias', 'url': '/historias/'})
        
        # Subpáginas de historias
        if 'listar_buscar_historias' in current_path:
            breadcrumbs.append({'label': 'Buscar Historias', 'url': None})
        elif 'h1_html' in current_path:
            breadcrumbs.append({'label': 'Uno', 'url': None})
        elif 'h2_html' in current_path:
            breadcrumbs.append({'label': 'Dos', 'url': None})
        elif 'h3_html' in current_path:
            breadcrumbs.append({'label': 'Tres', 'url': None})
    
    elif active_section == 'ordenes':
        breadcrumbs.append({'label': 'Órdenes', 'url': '/ordenes/'})
        
        # Subpáginas de ordenes
        if 'ordenes_medicas' in current_path:
            breadcrumbs.append({'label': 'Órdenes Médicas', 'url': None})
        elif 'ordenes_pedicas' in current_path:
            breadcrumbs.append({'label': 'Solicitudes', 'url': None})
    
    return {
        'active_section': active_section,
        'breadcrumbs': breadcrumbs,
    }