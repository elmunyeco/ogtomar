from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Paciente, HistoriaClinica, TipoDocumento
from .forms import PacienteForm
from django.shortcuts import get_object_or_404


def index(request):
    return render(request, "index.html")

def landing_page(request):
    return render(request, "landing_page.html")

def landing_page_dropdown(request):
    return render(request, "landing_page_dropdown.html")

def buscador(request):
    return render(request, "buscador.html")


from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Paciente

from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Paciente

from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Paciente

from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Paciente


def listar_buscar_pacientes(request):
    # Obtener el término de búsqueda y el tipo de búsqueda (DNI, Nombre o Apellido)
    query = request.GET.get("query", "")  # Si no hay búsqueda, el query será vacío
    tipo = request.GET.get(
        "tipo", "Documento"
    )  # Por defecto, la búsqueda será por numDoc
    # Imprimo tipo de busqueda
    print(tipo)

    # Filtrar los pacientes en función de la búsqueda
    if query:
        if tipo == "Documento":
            pacientes = Paciente.objects.filter(numDoc__icontains=query)
        elif tipo == "Nombre":
            pacientes = Paciente.objects.filter(nombre__icontains=query)
        elif tipo == "Apellido":
            pacientes = Paciente.objects.filter(apellido__icontains=query)
        else:
            # Si no hay criterio, mostrar todos los pacientes
            pacientes = Paciente.objects.all()

    else:
        # Si no hay búsqueda, mostrar todos los pacientes
        pacientes = Paciente.objects.all()

    # Ordenar los pacientes por un campo específico antes de paginar
    pacientes = pacientes.order_by(
        "id"
    )  # Ordenar por ID para evitar inconsistencias en la paginación

    # Paginador para dividir los pacientes en grupos de 14
    paginator = Paginator(pacientes, 12)  # 14 pacientes por página

    # Obtener el número de página desde la solicitud GET (si no existe, se usa la página 1 por defecto)
    page_number = request.GET.get("page", 1)

    # Obtener la página solicitada
    page_obj = paginator.get_page(page_number)

    #
    print(pacientes.query)
    
    # Renderizar la plantilla correcta: 'listar_buscar_pacientes.html'
    return render(
        request,
        "listar_buscar_pacientes.html",
        {"page_obj": page_obj, "query": query, "tipo": tipo},
    )

def listar_buscar_historias(request):
    # Obtener el término de búsqueda y el tipo de búsqueda
    query = request.GET.get("query", "")
    tipo = request.GET.get("tipo", "ID")  # Por defecto, la búsqueda será por ID de historia

    # Inicializar el queryset
    historias = HistoriaClinica.objects.all()

    if query:
        if tipo == "ID":
            # Búsqueda por ID de historia clínica
            try:
                # Convertir a entero si es posible
                id_busqueda = int(query)
                historias = historias.filter(id=id_busqueda)
            except ValueError:
                # Si no es un número válido, retornar conjunto vacío
                historias = HistoriaClinica.objects.none()

        elif tipo == "Documento":
            # Búsqueda por documento del paciente
            historias = historias.filter(paciente__numDoc__icontains=query)

        elif tipo == "Nombre":
            # Búsqueda por nombre del paciente
            historias = historias.filter(paciente__nombre__icontains=query)

        elif tipo == "Apellido":
            # Búsqueda por apellido del paciente
            historias = historias.filter(paciente__apellido__icontains=query)

    # Ordenar las historias por fecha de alta (más reciente primero) y luego por ID
    historias = historias.order_by('id')

    # Paginación
    paginator = Paginator(historias, 12)  # 12 historias por página
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    # Para debugging
    print(historias.query)

    return render(
        request,
        "listar_buscar_historias.html",
        {
            "page_obj": page_obj,
            "query": query,
            "tipo": tipo
        }
    )

def buscar_criteria(request):
    query = request.GET.get("query", "")  # Obtiene el término de búsqueda
    resultados = []

    if query:
        # Filtrar por nombre, apellido, nombre completo, documento o ID de historia clínica
        resultados = Paciente.objects.filter(
            Q(nombre__icontains=query)  # Buscar por coincidencia parcial en el nombre
            | Q(apellido__icontains=query)  # Coincidencia parcial en el apellido
            | Q(documento__icontains=query)  # Coincidencia parcial en el documento
            | Q(
                historiaclinica__id__icontains=query
            )  # Coincidencia en el ID de la historia clínica
            | Q(
                Q(nombre__icontains=query.split()[0])
                & Q(apellido__icontains=query.split()[-1])
            )  # Nombre completo
        )

        # Mostrar los IDs de las historias clínicas en la consola de comandos
        for paciente in resultados:
            print(f"ID Historia Clínica: {paciente.historiaclinica.id}")

    # No renderizamos resultados aún, solo mostramos en consola
    return render(request, "buscador.html", {"query": query, "resultados": []})


""" def cargar_paciente(request):
    if request.method == "POST":
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("index")
    else:
        form = PacienteForm()
    return render(request, "cargar_paciente.html", {"form": form}) """


def guardar_paciente(request, paciente_id=None):
    if paciente_id:
        # Si hay un ID de paciente, entonces estamos editando
        paciente = get_object_or_404(Paciente, id=paciente_id)
    else:
        # Si no hay ID, estamos creando un nuevo paciente
        paciente = None

    if request.method == "POST":
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            return redirect("index")
    else:
        form = PacienteForm(instance=paciente)

    return render(
        request, "guardar_paciente.html", {"form": form, "paciente": paciente}
    )


def borrar_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    if request.method == "POST":
        paciente.delete()
        return redirect("index")
    return render(request, "borrar_paciente.html", {"paciente": paciente})



```python
from django.http import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO

def descargarPDFSolicitudes(request, paciente_id, diagnostico, estudios, tipo=None):
    """
    tipo puede ser: 'lab', 'cardio', 'clinicos', 'otros'
    estudios: para estudios codificados viene como 's001|s002|etc'
             para otros estudios viene como texto libre
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )
    
    elements = []
    styles = getSampleStyleSheet()
    paciente = Paciente.objects.get(id=paciente_id)

    # Definir estilo para estudios
    estudio_style = ParagraphStyle(
        'EstudioStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,  # Espaciado entre líneas
        leftIndent=20
    )

    # Primera página siempre lleva encabezado
    agregar_encabezado(elements, paciente, diagnostico, tipo, styles)
    
    if tipo == 'otros':
        # Procesar otros estudios (texto libre)
        estudios_list = estudios.split('\n')
        elementos_por_pagina = 30  # Ajustar según necesidad
        
        for i, estudio in enumerate(estudios_list):
            if i > 0 and i % elementos_por_pagina == 0:
                elements.append(PageBreak())
                agregar_encabezado(elements, paciente, diagnostico, tipo, styles)
            
            elements.append(Paragraph(f"• {estudio.strip()}", estudio_style))
            elements.append(Spacer(1, 6))
    else:
        # Procesar estudios codificados
        estudios_list = estudios.split('|')
        elementos_por_pagina = 30  # Ajustar según necesidad
        
        for i, codigo in enumerate(estudios_list):
            if i > 0 and i % elementos_por_pagina == 0:
                elements.append(PageBreak())
                agregar_encabezado(elements, paciente, diagnostico, tipo, styles)
            
            nombre_estudio = get_nombre_estudio(codigo, tipo)
            elements.append(Paragraph(f"• {nombre_estudio}", estudio_style))
            elements.append(Spacer(1, 6))

    # Generar PDF
    doc.build(elements)
    buffer.seek(0)
    
    filename = f'orden_{tipo}_{paciente.apellido}.pdf'
    return FileResponse(buffer, as_attachment=True, filename=filename)

def agregar_encabezado(elements, paciente, diagnostico, tipo, styles):
    """Agrega el encabezado estándar a la página"""
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=12,
        spaceAfter=20,
        alignment=1  # Centrado
    )
    
    # Logo
    logo = Image('path/to/logo.png', width=200, height=100)
    elements.append(logo)
    elements.append(Spacer(1, 12))
    
    # Título según tipo de estudio
    titulos = {
        'lab': 'ESTUDIOS DE LABORATORIO',
        'cardio': 'ESTUDIOS CARDIOVASCULARES',
        'clinicos': 'ESTUDIOS CLÍNICOS',
        'otros': 'OTROS ESTUDIOS'
    }
    
    elements.append(Paragraph(titulos.get(tipo, ''), header_style))
    elements.append(Spacer(1, 12))
    
    # Datos del paciente
    header_text = f"""
    <para alignment="center">
        Paciente: {paciente.nombre} {paciente.apellido}<br/>
        DNI: {paciente.dni}<br/>
        Obra Social: {paciente.obra_social}<br/>
        N° Afiliado: {paciente.nro_afiliado}<br/>
        Diagnóstico: {diagnostico}
    </para>
    """
    elements.append(Paragraph(header_text, header_style))
    elements.append(Spacer(1, 20))

def get_nombre_estudio(codigo, tipo):
    """Obtiene el nombre del estudio según su código y tipo"""
    estudios = {
        'lab': {
            's001': 'Hemograma',
            's002': 'Coagulograma',
            # ... etc
        },
        'cardio': {
            's101': 'Holter de 48 hs 3 Canales',
            # ... etc
        },
        'clinicos': {
            's201': 'Espirometría',
            # ... etc
        }
    }
    return estudios.get(tipo, {}).get(codigo, 'Estudio no encontrado')
```