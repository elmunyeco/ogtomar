from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Paciente, TipoDocumento, Identificacion
from .forms import PacienteForm

def show_image(request):
    return render(request, 'show_image.html')

def index(request):
    return render(request, 'index.html')

def landing_page(request):
    return render(request, 'landing_page.html')

def landing_page_2(request):
    return render(request, 'landing_page_2.html')

def cargar_paciente(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = PacienteForm()
    return render(request, 'cargar_paciente.html', {'form': form})

from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic import ListView

class PacienteListView(ListView):
    model = Paciente
    template_name = 'pacientes_list.html'
    context_object_name = 'pacientes'
    paginate_by = 20  # Número de pacientes por páginas
    
class PacienteListViewTw(ListView):
    model = Paciente
    template_name = 'pacientes_list_tw.html'
    context_object_name = 'pacientes'
    paginate_by = 20  # Número de pacientes por páginas    