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


from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic import ListView


class PacienteListView(ListView):
    model = Paciente
    template_name = "pacientes_list.html"
    context_object_name = "pacientes"
    paginate_by = 15  # Número de pacientes por páginas


class PacienteListViewTw(ListView):
    model = Paciente
    template_name = "pacientes_list_tw2.html"
    context_object_name = "pacientes"
    paginate_by = 16  # Número de pacientes por páginas
