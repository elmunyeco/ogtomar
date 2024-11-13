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
    tipo = request.GET.get(
        "tipo", "ID"
    )  # Por defecto, la búsqueda será por ID de historia

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
    historias = historias.order_by("id")

    # Paginación
    paginator = Paginator(historias, 12)  # 12 historias por página
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    # Para debugging
    print(historias.query)

    return render(
        request,
        "listar_buscar_historias.html",
        {"page_obj": page_obj, "query": query, "tipo": tipo},
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


def dope(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    return render(request, "dope.html", {"paciente": paciente})


def ordenes_medicas(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    return render(request, "ordenes_medicas.html", {"paciente": paciente})


from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
)
from io import BytesIO
from django.http import FileResponse
from .models import Paciente


def encabezado(canvas, doc, paciente, diagnostico):
    # Crear una tabla para el logo y los datos del paciente
    logo = "/home/eze/ogtomar/hhcc/main/static/main/images/logosolo.png"
    logo_image = Image(logo, width=100, height=100)

    # Datos del paciente en párrafos
    styles = getSampleStyleSheet()
    datos_paciente = [
        f"Paciente: {paciente.nombre} {paciente.apellido}",
        f"Documento: {paciente.numDoc}",
        f"Obra Social: {paciente.obraSocial}",
        f"N° Afiliado: {paciente.afiliado}",
        f"Diagnóstico: {diagnostico}",
    ]
    datos_paragraphs = [Paragraph(dato, styles["Normal"]) for dato in datos_paciente]

    # Crear la tabla con el logo y los datos del paciente
    encabezado_table = Table([[logo_image, datos_paragraphs]], colWidths=[120, 400])
    encabezado_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),  # Alinear en la parte superior
                ("LEFTPADDING", (1, 0), (1, 0), 10),
                ("TOPPADDING", (0, 0), (1, 0), 20),  # Espaciado superior
            ]
        )
    )

    # Dibujar la tabla en el canvas
    encabezado_table.wrapOn(canvas, doc.width, doc.topMargin)
    encabezado_table.drawOn(canvas, 72, 700)  # Ajustar posición inicial si es necesario


def descargarPDFSolicitudes(request, paciente_id, diagnostico, estudios, tipo=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=56.7,  # 2cm en puntos
        leftMargin=56.7,  # 2cm en puntos
        topMargin=56.7,  # 2cm en puntos
        bottomMargin=56.7,  # 2cm en puntos
    )

    elements = []
    styles = getSampleStyleSheet()

    # Agregar espacio debajo del encabezado para evitar sobreposición
    elements.append(
        Spacer(1, 20)
    )  # Ajusta el valor según la cantidad de espacio que quieras

    # Datos del paciente
    paciente = Paciente.objects.get(id=paciente_id)

    # Estudios
    estudio_style = ParagraphStyle(
        "EstudioStyle", parent=styles["Normal"], fontSize=10, leading=14, leftIndent=20
    )
    for codigo in estudios.split("|"):
        nombre_estudio = get_nombre_estudio(codigo, tipo)
        elements.append(Paragraph(f"• {nombre_estudio}", estudio_style))
        elements.append(Spacer(1, 6))

    """ if tipo == "otros":
        elements.append(Paragraph(f"• {estudios}", estudio_style))
        elements.append(Spacer(1, 6))
    else:
        for codigo in estudios.split("|"):
            nombre_estudio = get_nombre_estudio(codigo, tipo)
            elements.append(Paragraph(f"• {nombre_estudio}", estudio_style))
            elements.append(Spacer(1, 6)) """

    # Construcción del PDF con encabezado en cada página
    doc.build(
        elements,
        onFirstPage=lambda canvas, doc: encabezado(canvas, doc, paciente, diagnostico),
        onLaterPages=lambda canvas, doc: encabezado(canvas, doc, paciente, diagnostico),
    )

    buffer.seek(0)
    filename = f"orden_{tipo}_{paciente.apellido}.pdf"
    return FileResponse(buffer, as_attachment=False, filename=filename)


def get_nombre_estudio(codigo, tipo):
    """Obtiene el nombre del estudio según su código y tipo"""
    estudios = {
        "lab": {
            "s001": "Hemograma",
            "s002": "Coagulograma",
            "s003": "KPTT",
            "s004": "Quick",
            "s005": "Recuento de Plaquetas",
            "s006": "Grupo y Factor",
            "s007": "Urea",
            "s008": "Creatinina",
            "s009": "Ácido Úrico",
            "s010": "Ionograma",
            "s011": "Magnesemia",
            "s012": "Calcemia",
            "s013": "Glucemia",
            "s014": "Insulinemia",
            "s015": "Homa",
            "s016": "Hemoglobina Glicosilada",
            "s017": "Fructosamina",
            "s018": "CTOG",
            "s019": "Hepatograma",
            "s020": "HDL, LDL, TG",
            "s021": "Lipidograma",
            "s022": "LPA",
            "s023": "APO A",
            "s024": "APO B",
            "s025": "Vitamina D",
            "s026": "Serologia Chagas",
            "s027": "VIH Elisa",
            "s028": "CPK",
            "s029": "CPK MB",
            "s030": "LDH",
            "s031": "Troponina",
            "s032": "Mioglobina",
            "s033": "BNP",
            "s034": "Pro BNP",
            "s035": "Dimero D",
            "s036": "PCR US",
            "s037": "Homocisteina",
            "s038": "Latex AR",
            "s039": "AC Anti Jo",
            "s040": "AC Anti Ro",
            "s041": "FAN",
            "s042": "ASTO",
            "s043": "TSH, T3, T4, T4L",
            "s044": "ATPO",
            "s045": "AC ATG",
            "s046": "AC AFM",
            "s047": "TRAB",
            "s048": "Proteinograma Electroforetico",
            "s049": "Proteinograma por Inmunofijacion",
            "s050": "Catecolaminas en plasma",
            "s051": "Aldosterona",
            "s052": "Renina plasmática",
            "s053": "Cortisol en Ayunas",
            "s054": "ACTH",
            "s055": "PRL",
            "s056": "PTH",
            "s057": "Ac. Folico",
            "s058": "Eritropoyetina plasmática",
            "s059": "PSA total y libre",
            "s060": "Testosterona en plasma",
            "s061": "LH-FSH",
            "s062": "AAG",
            "s063": "AAE",
            "s064": "IG A",
            "s065": "IG E",
            "s066": "Factor Lupico",
            "s067": "Microalbuminuria de 24 hs",
            "s068": "Clearance de Creatinina",
            "s069": "Orina completa",
            "s070": "Urocultivo",
            "s071": "Antibiograma",
            "s072": "Recuento de Colonias",
            "s073": "Tipificacion de gérmenes",
        },
        "cardio": {
            "s101": "Estudio de perfusión miocárdica en reposo y ejercicio gatillado (Gated Spect)",
            "s102": "Estudio de perfusión miocárdica en reposo y ejercicio (Spect)",
            "s103": "Estudio de perfusión miocárdica con dipiridamol (Spect)",
            "s104": "Holter de 48 hs 3 Canales",
            "s105": "Monitoreo Ambulatorio de la presión arterial",
            "s106": "Cinecoronariografia y eventual angioplastia",
            "s107": "Angiotomografia de alta resolución de arterias coronarias con contraste (Score de Calcio)",
            "s108": "Resonancia magnética cardiaca con evaluación de realce tardío (con cte)",
            "s109": "Angioresonancia de vasos del cuello y Cerebro (con contraste)",
            "s110": "Angiotomografia de Vasos del cuello y cerebro con reconstrucción 3d (con contraste)",
            "s111": "Tomografia computada de abdomen de alta resolución evaluación de glandula suprarrenal",
            "s112": "Doppler color de ambas arterias renales",
            "s113": "Ecostress con ejercicio físico con treadmill",
            "s114": "Ecocardiograma doppler color con evaluación de Strain",
            "s115": "Doppler color de vasos del cuello con evaluación de QIMT",
            "s116": "Doppler color arterial de miembros inferiores",
            "s117": "Doppler color venoso de miembros inferiores",
            "s118": "Doppler color de aorta torácica y abdominal",
            "s119": "Evaluacion por servicio de electrofisiología",
        },
        "clinicos": {
            "s201": "Espirometría",
            "s202": "Polisomnografia",
            "s203": "Electroencefalograma",
            "s204": "Mapeo Cerebral",
            "s205": "Videoendoscopia digestiva alta con sedación",
            "s206": "Videoendoscopia digestiva baja con sedación",
            "s207": "Tomografia computada de cerebro sin contraste",
            "s208": "Tomografia computada de cerebro con contraste",
            "s209": "Resonancia magnética de cerebro con difusión (con contraste)",
            "s210": "Tomografia computada de Torax (sin contraste)",
            "s211": "Tomografia computada de Torax (con contraste)",
            "s212": "Tomografia computada de Abdomen (sin contraste)",
            "s213": "Tomografia computada de Abdomen (con contraste)",
            "s214": "Rx. Torax (frente)",
            "s220": "Rx. Columna Cervical (F,P,O)",
            "s221": "Espinograma (F,P)",
            "s222": "Densitometria Osea corporal total",
            "s223": "PET TC Corporal total",
            "s224": "Volumenes Pulmonares y DLCO",
            "s225": "Test de marcha de 6 minutos",
            "s226": "Ecografia y doppler color tiroideo",
            "s227": "Centellograma tiroideo",
            "s228": "Ecografia Abdominal",
            "s229": "Ecografia Vesico prostatica",
        },
    }
    return estudios.get(tipo, {}).get(codigo, "Estudio no encontrado")
