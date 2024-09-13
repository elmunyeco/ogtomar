from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('show_image/', views.show_image, name='show_image'),
    path('landing/', views.landing_page, name='landing'),
    path('landing2/', views.landing_page_2, name='landing2'),
    path('cargar_paciente/', views.cargar_paciente, name='cargar_paciente'),
    path('pacientes/', views.PacienteListView.as_view(), name='pacientes_list'),
    path('pacientes_tw/', views.PacienteListViewTw.as_view(), name='pacientes_list_tailwind'),
]