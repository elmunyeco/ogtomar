from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("landing/", views.landing_page, name="landing"),
    path("landing_dropdown/", views.landing_page_dropdown, name="landing_dropdown"),
    path("buscador/", views.buscador, name="buscador"),
    path("pacientes/", views.listar_buscar_pacientes, name="listar_buscar_pacientes"),
    path("historias/", views.listar_buscar_historias, name="listar_buscar_historias"),
    path("guardar_paciente/<int:pk>/", views.guardar_paciente, name="guardar_paciente"),
    path("borrar_paciente/<int:pk>/", views.borrar_paciente, name="borrar_paciente"),
    path('ordenes_medicas/<int:paciente_id>/', views.ordenes_medicas, name='ordenes_medicas'),
    path(
        "descargarPDFSolicitudes/<int:paciente_id>/<str:diagnostico>/<str:estudios>/<str:tipo>/",
        views.descargarPDFSolicitudes,
        name="descargar_pdf_solicitudes",
    ),

    path('ordenes_pedicas/<int:paciente_id>/', views.ordenes_pedicas, name='ordenes_pedicas'),
    path('generar_pdf_orden/<int:paciente_id>/<str:diagnostico>/<str:estudios>/<str:tipo>/', 
         views.generar_pdf_orden, 
         name='generar_pdf_orden'),
]
