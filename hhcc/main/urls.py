from django.urls import path
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("nombre/", login_required(views.cambiar_nombre), name="cambiar_nombre"),
    path("password/", auth_views.PasswordChangeView.as_view(template_name="password_change_form.html"), name="password_change"),
    path("password/done/", auth_views.PasswordChangeDoneView.as_view(template_name="password_change_done.html"), name="password_change_done"),
    path("", login_required(views.index), name="index"),
    path("buscador/", login_required(views.buscador), name="buscador"),
    path("docs/busqueda-trigramas/", login_required(views.documento_trigramas), name="documento_trigramas"),
    path("pacientes/", login_required(views.listar_buscar_pacientes), name="listar_buscar_pacientes"),
    path('pacientes/crear/', login_required(views.crear_paciente), name='crear_paciente'),
    path('pacientes/<int:pk>/editar/', login_required(views.editar_paciente), name='editar_paciente'),
    path('pacientes/<int:pk>/eliminar/', login_required(views.eliminar_paciente), name='eliminar_paciente'),
    path("historias/", login_required(views.listar_buscar_historias), name="listar_buscar_historias"),
    path(
        "historias/<int:historia_id>/estudios/",
        login_required(views.listar_estudios_historia),
        name="listar_estudios_historia",
    ),
    path(
        "historias/<int:historia_id>/estudios/nuevo/",
        login_required(views.historia_estudios_nuevo),
        name="historia_estudios_nuevo",
    ),
    path(
        "ordenes_medicas/<int:paciente_id>/",
        login_required(views.ordenes_medicas),
        name="ordenes_medicas",
    ),
    path(
        "descargarPDFSolicitudes/<int:paciente_id>/<str:diagnostico>/<str:estudios>/<str:tipo>/",
        login_required(views.descargarPDFSolicitudes),
        name="descargar_pdf_solicitudes",
    ),
    path(
        "generar_pdf_orden/<int:paciente_id>/<str:diagnostico>/<str:estudios>/<str:tipo>/",
        login_required(views.generar_pdf_orden),
        name="generar_pdf_orden",
    ),
    path(
        "api/historia/<int:historia_id>/ultimos-comentarios/",
        login_required(views.get_ultimo_comentario_indicaciones),
        name="get_ultimo_comentario_indicaciones",
    ),
    path(
        "api/historia/<int:historia_id>/guardar/",
        login_required(views.guardar_historia),
        name="guardar_historia",
    ),
    path(
        "historia/<int:historia_id>/indicaciones/",
        login_required(views.indicaciones_list),
        name="indicaciones",
    ),
    path(
        "historia/<int:historia_id>/indicaciones/imprimir/",
        login_required(views.imprimir_indicaciones),
        name="imprimir_indicaciones",
    ),
    path(
        "historia/<int:historia_id>/indicaciones/agregar/",
        login_required(views.indicacion_agregar),
        name="indicacion_agregar",
    ),
    path(
        "historia/<int:historia_id>/indicaciones/<int:id>/editar/",
        login_required(views.indicacion_editar),
        name="indicacion_editar",
    ),
    path(
        "indicaciones/<int:id>/eliminar/",
        login_required(views.indicacion_eliminar),
        name="indicacion_eliminar",
    ),
    path(
        "historia/<int:historia_id>/indicaciones/comentario/",
        login_required(views.guardar_comentarios_indicaciones),
        name="guardar_comentarios_indicaciones",
    ),
    path(
        "historial_medico/<int:historia_id>/",
        login_required(views.detalle_historia_con_historial),
        name="detalle_historia_con_historial",
    ),
    path(
        "historial_medico/<int:historia_id>/imprimir/",
        login_required(views.imprimir_historia_clinica),
        name="imprimir_historia_clinica",
    ),
    path("eliminar-comentario/", login_required(views.eliminar_comentario), name="eliminar_comentario"),
]
