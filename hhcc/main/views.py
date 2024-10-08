from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Paciente, TipoDocumento, Identificacion
from .forms import PacienteForm


def show_image(request):
    return render(request, "show_image.html")


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


def cargar_paciente(request):
    if request.method == "POST":
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("index")
    else:
        form = PacienteForm()
    return render(request, "cargar_paciente.html", {"form": form})


from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic import ListView


class PacienteListView(ListView):
    model = Paciente
    template_name = "pacientes_list.html"
    context_object_name = "pacientes"
    paginate_by = 20  # Número de pacientes por páginas


class PacienteListViewTw(ListView):
    model = Paciente
    template_name = "pacientes_list_tw.html"
    context_object_name = "pacientes"
    paginate_by = 20  # Número de pacientes por páginas
