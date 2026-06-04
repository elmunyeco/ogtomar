from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


app_name = "qbi2_poc"

urlpatterns = [
    path("", login_required(views.qbi2_poc_home), name="home"),
    path("medicamentos/directo/", login_required(views.vademecum_legacy), name="medicamentos_directo"),
    path("medicamentos/cache/", views.vademecum_demo, name="medicamentos_cache"),
    path("paciente/recetas/nueva/", views.pacientes_portal_page, name="paciente_receta_nueva"),
    path("medico/solicitudes/", login_required(views.solicitudes_receta_page), name="medico_solicitudes"),
    path("lab/receta/", login_required(views.receta_poc_page), name="lab_receta"),
    path("api/health/", login_required(views.health), name="api_health"),
    path("api/medicamentos/cache/", views.vademecum_search_api, name="api_medicamentos_cache"),
    path(
        "api/medicamentos/directo/",
        login_required(views.buscar_vademecum_legacy),
        name="api_medicamentos_directo",
    ),
    path(
        "api/paciente/medicamentos/directo/",
        views.buscar_vademecum_portal,
        name="api_paciente_medicamentos_directo",
    ),
    path("api/lab/receta/emitir/", login_required(views.emitir_receta_poc), name="api_lab_receta_emitir"),
    path("api/paciente/validar-y-solicitar/", views.validar_paciente_portal, name="api_paciente_validar_solicitar"),
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
    path("api/cache/recientes/", views.cache_recent_api, name="api_cache_recientes"),
]
