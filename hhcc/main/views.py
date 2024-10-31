from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Paciente, TipoDocumento
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