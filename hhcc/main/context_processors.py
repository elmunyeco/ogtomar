import json

def menu_context(request):
    """
    Añade variables de contexto relacionadas con la navegación y el menú.
    Esto estará disponible en todos los templates automáticamente.
    """
    # Determinar la sección activa basada en la URL
    active_section = ''
    path = request.path
    
    if '/pacientes' in path:
        active_section = 'pacientes'
    elif '/historias' in path:
        active_section = 'historias'
    elif '/ordenes' in path:
        active_section = 'ordenes'
    elif path == '/' or path == '/index/' or path == '/index.html':
        active_section = 'inicio'
    
    # Configurar breadcrumbs predeterminados
    breadcrumbs = [
        {"label": "Inicio", "url": "/"}
    ]
    
    if active_section == 'pacientes':
        breadcrumbs.append({"label": "Pacientes", "url": "/pacientes/"})
    elif active_section == 'historias':
        breadcrumbs.append({"label": "Historias", "url": "/historias/"})
    elif active_section == 'ordenes':
        breadcrumbs.append({"label": "Órdenes", "url": "/ordenes/"})
    
    # Si estamos en una vista específica, añadir el breadcrumb apropiado
    # (esto se puede ampliar según sea necesario)
    if 'buscar' in path:
        if active_section == 'pacientes':
            breadcrumbs.append({"label": "Buscar Pacientes", "url": None})
        elif active_section == 'historias':
            breadcrumbs.append({"label": "Buscar Historias", "url": None})
    
    return {
        'active_section': active_section,
        'breadcrumbs_json': json.dumps(breadcrumbs),
    }
