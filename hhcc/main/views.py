from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Paciente, HistoriaClinica, TipoDocumento, IndicacionesVisitas
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


def detalle_historia(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, id=historia_id)
    paciente = historia.paciente

    # Añade logs para debug
    print(f"Historia ID: {historia_id}")
    print(f"Historia encontrada: {historia}")
    print(f"Paciente: {paciente}")

    context = {
        "historia": historia,
        "paciente": paciente,
    }

    # Imprime el contexto completo
    print(f"Contexto: {context}")

    return render(request, "detalle_historia.html", context)


def ordenes_medicas(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    context = {
        "paciente": paciente,
    }
    return render(request, "ordenes_medicas.html", context)


from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Image,
    Table,
    TableStyle,
)
from reportlab.lib.colors import HexColor
from datetime import datetime
from io import BytesIO
from django.http import FileResponse
from .models import Paciente


def dibujar_encabezado(canvas, doc, paciente, diagnostico):
    color_principal = HexColor("#9a4035")
    styles = getSampleStyleSheet()

    # Estilo para el nombre del doctor (reduciendo el leading)
    nombre_doctor_style = ParagraphStyle(
        "NombreDoctor",
        parent=styles["Normal"],
        fontSize=16,
        textColor=color_principal,
        fontName="Helvetica-Bold",
        leading=16,  # Reducido para acercar más los elementos
        alignment=1,
    )

    # Estilo para la especialidad (reduciendo el espacio antes del párrafo)
    especialidad_style = ParagraphStyle(
        "Especialidad",
        parent=styles["Normal"],
        fontSize=12,
        textColor=color_principal,
        fontName="Helvetica",
        leading=14,
        alignment=1,
        spaceBefore=0,  # Eliminamos el espacio antes del párrafo
    )

    # Estilo para la información de contacto (centrado)
    contacto_style = ParagraphStyle(
        "Contacto",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        alignment=1,  # 1 = centered
    )

    # Crear logo
    logo = "/home/eze/omar/hhcc/main/static/main/images/logosolo.png"
    logo_image = Image(logo, width=20 * mm, height=20 * mm)

    # Información del doctor
    nombre_doctor = Paragraph("Dr. Omar Prieto", nombre_doctor_style)
    especialidad = Paragraph("Cardiología Integral", especialidad_style)

    # Información de contacto (centrada)
    contacto_text = """
    Las Heras 459<br/>
    Monte Grande<br/>
    Tel: 11 3309-7865<br/>
    www.cardioprieto.com
    """
    contacto = Paragraph(contacto_text, contacto_style)

    # Tabla del encabezado
    encabezado_table = Table(
        [
            [
                logo_image,
                Table(
                    [[nombre_doctor], [especialidad]],
                    colWidths=[120 * mm],
                    rowHeights=[8 * mm, 6 * mm],
                ),
                contacto,
            ]
        ],
        colWidths=[25 * mm, 110 * mm, 45 * mm],
    )

    encabezado_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("ALIGN", (2, 0), (2, 0), "CENTER"),  # Cambiado a CENTER
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 1 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1 * mm),
            ]
        )
    )

    # Posicionar encabezado
    encabezado_table.wrapOn(canvas, doc.width, doc.topMargin)
    encabezado_table.drawOn(canvas, doc.leftMargin, 750)

    # Línea divisoria
    canvas.setStrokeColor(color_principal)
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 745, doc.width + doc.leftMargin, 745)

    # Datos del paciente centrados
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor("black")

    y_position = 725
    fecha_solicitud = datetime.now().strftime("%d/%m/%Y")

    datos_paciente = [
        f"Nombre y apellido: {paciente.nombre} {paciente.apellido}",
        f"{paciente.idTipoDoc.nombre}: {paciente.numDoc}",
        f"Obra social: {paciente.obraSocial or '-'}",
        f"Afiliado: {paciente.afiliado or '-'}",
        f"Fecha de solicitud: {fecha_solicitud}",
        f"Diagnóstico: {diagnostico or '-'}",
    ]

    # Calcular el centro de la página
    page_center = doc.leftMargin + (doc.width / 2)

    for dato in datos_paciente:
        # Calcular el ancho del texto para centrarlo
        text_width = canvas.stringWidth(dato, "Helvetica", 9)
        x_position = page_center - (text_width / 2)
        canvas.drawString(x_position, y_position, dato)
        y_position -= 12


def descargarPDFSolicitudes(request, paciente_id, diagnostico, estudios, tipo=None):
    buffer = BytesIO()
    paciente = Paciente.objects.get(id=paciente_id)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=70 * mm,
        bottomMargin=20 * mm,
    )

    elements = []
    styles = getSampleStyleSheet()

    estudio_style = ParagraphStyle(
        "EstudioStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        leftIndent=20,
        spaceBefore=4,
        spaceAfter=4,
        bulletIndent=10,
        firstLineIndent=0,
    )

    for codigo in estudios.split("|"):
        nombre_estudio = get_nombre_estudio(codigo, tipo)
        elements.append(Paragraph(f"• {nombre_estudio}", estudio_style))

    """ if tipo == "otros":
        elements.append(Paragraph(f"• {estudios}", estudio_style))
        elements.append(Spacer(1, 6))
    else:
        for codigo in estudios.split("|"):
            nombre_estudio = get_nombre_estudio(codigo, tipo)
            elements.append(Paragraph(f"• {nombre_estudio}", estudio_style))
            elements.append(Spacer(1, 6)) """

    # Construir el PDF
    doc.build(
        elements,
        onFirstPage=lambda canvas, doc: dibujar_encabezado(
            canvas, doc, paciente, diagnostico
        ),
        onLaterPages=lambda canvas, doc: dibujar_encabezado(
            canvas, doc, paciente, diagnostico
        ),
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


def ordenes_pedicas(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    context = {
        "paciente": paciente,
    }
    return render(request, "ordenes_pedicas.html", context)


from django.template.loader import render_to_string
from django.http import FileResponse
from weasyprint import HTML
from io import BytesIO
from datetime import datetime
from .models import Paciente
from django.conf import settings


def generar_pdf_orden(request, paciente_id, diagnostico, estudios, tipo=None):
    paciente = Paciente.objects.get(id=paciente_id)
    fecha_solicitud = datetime.now().strftime("%d/%m/%Y")

    # Obtener la ruta absoluta del directorio static
    static_root = (
        settings.STATICFILES_DIRS[0]
        if hasattr(settings, "STATICFILES_DIRS")
        else settings.STATIC_ROOT
    )

    context = {
        "paciente": paciente,
        "diagnostico": diagnostico,
        "fecha_solicitud": datetime.now().strftime("%d/%m/%Y"),
        "estudios": estudios.split("|"),
        "STATIC_ROOT": static_root,  # Pasar la ruta estática al template
    }

    html_string = render_to_string("O_M.html", context)

    # Configurar WeasyPrint para que encuentre los archivos estáticos
    buffer = BytesIO()
    HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf(buffer)
    buffer.seek(0)

    return FileResponse(
        buffer, as_attachment=False, filename=f"orden_{tipo}_{paciente.apellido}.pdf"
    )


from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import (
    HistoriaClinica,
    SignosVitales,
    CondicionMedicaHistoria,
    CondicionMedica,
)


def get_historia_data(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, pk=historia_id)
    try:
        signos_vitales = SignosVitales.objects.filter(historia=historia).latest("fecha")
        condiciones = CondicionMedicaHistoria.objects.filter(historia=historia)

        data = {
            "signos_vitales": {
                "presion_sistolica": signos_vitales.presion_sistolica,
                "presion_diastolica": signos_vitales.presion_diastolica,
                "peso": signos_vitales.peso,
                "glucemia": signos_vitales.glucemia,
                "colesterol": signos_vitales.colesterol,
            },
            "condiciones": list(condiciones.values("id")),
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def detalle_historia_viejo(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, id=historia_id)
    paciente = historia.paciente

    # Obtener últimos signos vitales
    signos_vitales = (
        SignosVitales.objects.filter(historia=historia).order_by("-fecha").first()
    )

    # Obtener condiciones del paciente
    condiciones_paciente = CondicionMedicaHistoria.objects.filter(
        historia=historia
    ).select_related("condicion")

    # Obtener todas las condiciones posibles
    todas_condiciones = CondicionMedica.objects.all()

    # Obtener IDs de las condiciones actuales para marcar los checkboxes
    condiciones_activas = condiciones_paciente.values_list("condicion_id", flat=True)

    context = {
        "historia": historia,
        "paciente": paciente,
        "signos_vitales": signos_vitales,
        "todas_condiciones": todas_condiciones,
        "condiciones_activas": condiciones_activas,
    }

    return render(request, "detalle_historia_t2.html", context)


def detalle_historia(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, id=historia_id)
    today = timezone.now().date()

    # Obtener última visita (para cargar signos vitales y condiciones)
    signos_vitales = SignosVitales.objects.filter(
        historia=historia, fecha=today
    ).first()

    # Obtener comentarios del día si existen
    comentarios_hoy = ComentariosVisitas.objects.filter(
        historia_clinica=historia, fecha=today, tipo="EVOL"
    ).first()

    condiciones_paciente = CondicionMedicaHistoria.objects.filter(historia=historia)
    todas_condiciones = CondicionMedica.objects.all()
    condiciones_activas = condiciones_paciente.values_list("condicion_id", flat=True)

    context = {
        "historia": historia,
        "paciente": historia.paciente,
        "signos_vitales": signos_vitales,
        "todas_condiciones": todas_condiciones,
        "condiciones_activas": condiciones_activas,
        "comentarios_hoy": comentarios_hoy.comentarios if comentarios_hoy else "",
    }

    return render(request, "detalle_historia_t3.html", context)


from .models import ComentariosVisitas
from django.db.models import Subquery


def get_ultimo_comentario_indicaciones(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, pk=historia_id)
    try:
        comentarios = ComentariosVisitas.objects.filter(
            historia_clinica=historia,
            fecha=Subquery(
                ComentariosVisitas.objects.filter(historia_clinica=historia)
                .order_by("-fecha")
                .values("fecha")[:1]
            ),
        )

        data = {
            "comentarios": [
                {
                    "tipo": c.tipo,
                    "texto": c.comentarios,
                    "fecha": c.fecha.strftime("%Y-%m-%d"),
                }
                for c in comentarios
            ]
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


from django.views.decorators.http import require_POST


@require_POST
def actualizar_condiciones(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, id=historia_id)

    # Obtener las condiciones seleccionadas del form
    condiciones_seleccionadas = request.POST.getlist("condiciones")

    # Borrar condiciones existentes
    CondicionMedicaHistoria.objects.filter(historia=historia).delete()

    # Crear nuevas condiciones
    for condicion_id in condiciones_seleccionadas:
        CondicionMedicaHistoria.objects.create(
            historia=historia, condicion_id=condicion_id
        )

    return redirect("detalle_historia", historia_id=historia_id)


@require_POST
def guardar_signos_vitales(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, id=historia_id)

    SignosVitales.objects.create(
        historia=historia,
        presion_sistolica=request.POST.get("presion_sistolica"),
        presion_diastolica=request.POST.get("presion_diastolica"),
        peso=request.POST.get("peso"),
        glucemia=request.POST.get("glucemia"),
        colesterol=request.POST.get("colesterol"),
    )

    return redirect("detalle_historia", historia_id=historia_id)


from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt  # Solo para testing


@csrf_exempt  # Remover en producción
@require_POST
def actualizar_historia(request, historia_id):
    import json

    data = json.loads(request.body)

    # Log data para debug
    print("Historia ID:", historia_id)
    print("Signos Vitales:", json.dumps(data["signosVitales"], indent=2))
    print("Nota Evolución:", data["notaEvolucion"])
    print("Condiciones activas:", [c["id"] for c in data["condiciones"] if c["active"]])

    return JsonResponse({"status": "ok"})


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.utils import timezone
import json
from .utils import process_signos_vitales

def guardar_historia(request, historia_id):
    try:
        historia = get_object_or_404(HistoriaClinica, pk=historia_id)
        data = json.loads(request.body)
        today = timezone.now().date()

        # Guardar signos vitales
        signos_vitales = process_signos_vitales(data)
        if any(v is not None for v in signos_vitales.values()):
            fecha_visita = data.get('fecha_visita', today)  # Permitir fecha específica
            signos_existentes = SignosVitales.objects.filter(
                historia=historia, 
                fecha=fecha_visita
            ).first()
            
            if signos_existentes:
                for key, value in signos_vitales.items():
                    setattr(signos_existentes, key, value)
                signos_existentes.save()
            else:
                SignosVitales.objects.create(
                    historia=historia, 
                    fecha=fecha_visita, 
                    **signos_vitales
                )

        # Actualizar condiciones
        if "condiciones" in data:
            CondicionMedicaHistoria.objects.filter(historia=historia).delete()
            CondicionMedicaHistoria.objects.bulk_create([
                CondicionMedicaHistoria(historia=historia, condicion_id=cond_id)
                for cond_id in data["condiciones"]
            ])

        # Guardar/actualizar comentario

        if comentarios := data.get("comentarios"):
            ComentariosVisitas.objects.update_or_create(
                historia_clinica=historia,
                fecha=today,
                tipo="EVOL",
                defaults={"comentarios": comentarios}
            )
        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


from django.views.decorators.csrf import csrf_protect

@csrf_protect
def indicaciones_list(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, id=historia_id)
    
    indicaciones = [ind.to_dict() for ind in IndicacionesVisitas.objects.filter(
        historia_clinica=historia,
        eliminado=False
    ).order_by('-fecha')]

    ultimo_comentario = ComentariosVisitas.objects.filter(
        historia_clinica=historia,
        tipo='INDIC'
    ).order_by('-fecha').first()

    return render(request, 'indicaciones/lista.html', {
        'indicaciones_json': json.dumps(indicaciones),
        'comentario_json': json.dumps(
            ultimo_comentario.to_dict() if ultimo_comentario 
            else {'comentarios': '', 'fecha': datetime.now().strftime('%Y-%m-%d')}
        ),
        'historia': historia
    })
    
from datetime import datetime

@csrf_protect
def indicacion_agregar(request, historia_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validación básica
            required_fields = ['medicamento', 'fecha']
            if not all(field in data for field in required_fields):
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Faltan campos requeridos'
                }, status=400)
            
            indicacion = IndicacionesVisitas.objects.create(
                historia_clinica_id=historia_id,
                medicamento=data['medicamento'],
                ochoHoras=data.get('ochoHoras', ''),
                doceHoras=data.get('doceHoras', ''),
                dieciochoHoras=data.get('dieciochoHoras', ''),
                veintiunaHoras=data.get('veintiunaHoras', ''),
                fecha=datetime.strptime(data['fecha'], '%Y-%m-%d').date(),
                eliminado=False
            )
            return JsonResponse({
                'status': 'success', 
                'data': indicacion.to_dict()
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error', 
                'message': 'JSON inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=500)
    
    return render(request, 'indicaciones/agregar.html', {
        'historia': get_object_or_404(HistoriaClinica, id=historia_id)
    })
    
@csrf_protect
def indicacion_eliminar(request, id):
    if request.method == 'POST':
        try:
            indicacion = get_object_or_404(IndicacionesVisitas, id=id)
            indicacion.eliminado = True
            indicacion.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Indicación eliminada correctamente'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)
    
    
from django.utils import timezone
    
@csrf_protect
def guardar_comentarios_indicaciones(request, historia_id):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Método no permitido'
        }, status=405)
        
    try:
        data = json.loads(request.body)
        if 'comentarios' not in data:
            return JsonResponse({
                'status': 'error',
                'message': 'Falta el campo comentarios'
            }, status=400)

        comentario = ComentariosVisitas.objects.create(
            historia_clinica_id=historia_id,
            comentarios=data['comentarios'],
            tipo='INDIC',
            fecha=timezone.now()
        )
        
        return JsonResponse({
            'status': 'success',
            'data': comentario.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        }, status=500)    