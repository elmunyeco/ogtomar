from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('cargar_paciente/', views.cargar_paciente, name='cargar_paciente'),
    path('pacientes/', views.PacienteListView.as_view(), name='pacientes_list'),
]