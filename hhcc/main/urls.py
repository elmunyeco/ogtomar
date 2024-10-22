from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('landing/', views.landing_page, name='landing'),
    path('landing_dropdown/', views.landing_page_dropdown, name='landing_dropdown'),
    path('buscador/', views.buscador, name='buscador'),
    path('pacientes/', views.PacienteListView.as_view(), name='pacientes_list'),
    path('pacientes_listar_buscar/', views.listar_buscar_pacientes(), name='listar_buscar_pacientes'),
    path('pacientes_tw/', views.PacienteListViewTw.as_view(), name='pacientes_list_tw'),
    path('guardar_paciente/<int:pk>/', views.guardar_paciente, name='guardar_paciente'),
    path('borrar_paciente/<int:pk>/', views.borrar_paciente, name='borrar_paciente'),
]