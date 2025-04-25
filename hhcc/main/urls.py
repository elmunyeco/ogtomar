from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("landing/", views.landing_page, name="landing"),
    path("landing_dropdown/", views.landing_page_dropdown, name="landing_dropdown"),
    path("buscador/", views.buscador, name="buscador"),
    path("pacientes/", views.listar_buscar_pacientes, name="listar_buscar_pacientes"),
    path('pacientes/crear/', views.crear_paciente, name='crear_paciente'),
    path('pacientes/<int:pk>/', views.detalle_paciente, name='detalle_paciente'),
    path('pacientes/<int:pk>/editar/', views.editar_paciente, name='editar_paciente'),
    path('pacientes/<int:pk>/eliminar/', views.eliminar_paciente, name='eliminar_paciente'),
    path("historias/", views.listar_buscar_historias, name="listar_buscar_historias"),
    path("guardar_paciente/<int:pk>/", views.guardar_paciente, name="guardar_paciente"),
    path("borrar_paciente/<int:pk>/", views.borrar_paciente, name="borrar_paciente"),
    path(
        "ordenes_medicas/<int:paciente_id>/",
        views.ordenes_medicas,
        name="ordenes_medicas",
    ),
    path(
        "detalle_historia/<int:historia_id>/",
        views.detalle_historia,
        name="detalle_historia",
    ),
    path(
        "actualizar_condiciones/<int:historia_id>/",
        views.actualizar_condiciones,
        name="actualizar_condiciones",
    ),
    path(
        "guardar_signos_vitales/<int:historia_id>/",
        views.guardar_signos_vitales,
        name="guardar_signos_vitales",
    ),
    path(
        "historia/<int:historia_id>/actualizar/",
        views.actualizar_historia,
        name="actualizar_historia",
    ),
    path(
        "descargarPDFSolicitudes/<int:paciente_id>/<str:diagnostico>/<str:estudios>/<str:tipo>/",
        views.descargarPDFSolicitudes,
        name="descargar_pdf_solicitudes",
    ),
    path(
        "ordenes_pedicas/<int:paciente_id>/",
        views.ordenes_pedicas,
        name="ordenes_pedicas",
    ),
    path(
        "generar_pdf_orden/<int:paciente_id>/<str:diagnostico>/<str:estudios>/<str:tipo>/",
        views.generar_pdf_orden,
        name="generar_pdf_orden",
    ),
    path(
        "api/historia/<int:historia_id>",
        views.get_historia_data,
        name="get_historia_data",
    ),
    path(
        "api/historia/<int:historia_id>/ultimos-comentarios/",
        views.get_ultimo_comentario_indicaciones,
        name="get_ultimo_comentario_indicaciones",
    ),
    path(
        "api/historia/<int:historia_id>/guardar/",
        views.guardar_historia,
        name="guardar_historia",
    ),
    path(
        "historia/<int:historia_id>/indicaciones/",
        views.indicaciones_list,
        name="indicaciones",
    ),
    path(
        "historia/<int:historia_id>/indicaciones/agregar/",
        views.indicacion_agregar,
        name="indicacion_agregar",
    ),
    path(
        "indicaciones/<int:id>/eliminar/",
        views.indicacion_eliminar,
        name="indicacion_eliminar",
    ),
    path(
        "historia/<int:historia_id>/indicaciones/comentario/",
        views.guardar_comentarios_indicaciones,
        name="guardar_comentarios_indicaciones",
    ),
    path(
        "historial_medico/<int:historia_id>/",
        views.detalle_historia_con_historial,
        name="detalle_historia_con_historial",
    ),
    path("eliminar-comentario/", views.eliminar_comentario, name="eliminar_comentario"),
    
    
    # Nuevas URLs para las páginas de ejemplo
    path('h1/', views.h1_html, name='h1_html'),
    path('h2/', views.h2_html, name='h2_html'),
    path('h3/', views.h3_html, name='h3_html')
]
