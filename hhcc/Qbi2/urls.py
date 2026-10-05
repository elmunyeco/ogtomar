from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


app_name = "recetas"

urlpatterns = [
    path("paciente/ingresar/", views.paciente_login_page, name="paciente_login"),
    path("paciente/salir/", views.paciente_logout, name="paciente_logout"),
    path("paciente/recetas/nueva/", views.pacientes_portal_page, name="paciente_receta_nueva"),
    path("medico/solicitudes/", login_required(views.solicitudes_receta_page), name="medico_solicitudes"),
    path("medico/recetas/nueva/", login_required(views.receta_medico_page), name="medico_receta_nueva"),
    path(
        "api/paciente/medicamentos/directo/",
        views.buscar_vademecum_portal,
        name="api_paciente_medicamentos_directo",
    ),
    path(
        "api/paciente/financiadores/",
        views.buscar_financiadores_portal,
        name="api_paciente_financiadores",
    ),
    path(
        "api/catalogos/<str:catalogo>/",
        login_required(views.catalogo_api),
        name="api_catalogo",
    ),
    path(
        "api/medico/recetas/pacientes/",
        login_required(views.receta_pacientes_api),
        name="api_receta_pacientes",
    ),
    path(
        "api/medico/recetas/preview/",
        login_required(views.receta_preview_api),
        name="api_receta_preview",
    ),
    path(
        "api/medico/recetas/emitir/",
        login_required(views.receta_emit_api),
        name="api_receta_emitir",
    ),
    path("api/paciente/validar-y-solicitar/", views.validar_paciente_portal, name="api_paciente_validar_solicitar"),
    path(
        "api/paciente/perfil/actualizar/",
        views.actualizar_perfil_paciente,
        name="api_paciente_perfil_actualizar",
    ),
    path(
        "api/medico/solicitudes/<int:solicitud_id>/aprobar/",
        login_required(views.aprobar_solicitud_receta),
        name="api_medico_solicitud_aprobar",
    ),
    path(
        "api/medico/solicitudes/<int:solicitud_id>/rechazar/",
        login_required(views.rechazar_solicitud_receta),
        name="api_medico_solicitud_rechazar",
    ),
    path(
        "api/medico/solicitudes/<int:solicitud_id>/reabrir/",
        login_required(views.reabrir_solicitud_receta),
        name="api_medico_solicitud_reabrir",
    ),
    path(
        "api/medico/solicitudes/<int:solicitud_id>/correo/",
        login_required(views.preparar_correo_receta),
        name="api_medico_solicitud_correo",
    ),
]
