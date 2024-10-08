from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('show_image/', views.show_image, name='show_image'),
    path('landing/', views.landing_page, name='landing'),
    path('landing_dropdown/', views.landing_page_dropdown, name='landing_dropdown'),    path('buscador/', views.buscador, name='buscador'),
    path('cargar_paciente/', views.cargar_paciente, name='cargar_paciente'),
    path('pacientes/', views.PacienteListView.as_view(), name='pacientes_list'),
    path('pacientes_tw/', views.PacienteListViewTw.as_view(), name='pacientes_list_tailwind'),
]