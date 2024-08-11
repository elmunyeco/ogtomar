from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Paciente, TipoDocumento, Identificacion
from .forms import PacienteForm

def index(request):
    return render(request, 'index.html')

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