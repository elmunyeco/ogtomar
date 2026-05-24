from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

app_name = "qbi2"

urlpatterns = [
    path("health/", login_required(views.health), name="health"),
    path("api/vademecum/buscar/", login_required(views.buscar_vademecum), name="buscar_vademecum"),
    path("api/pacientes-portal/vademecum/buscar/", views.buscar_vademecum_portal, name="buscar_vademecum_portal"),
    path("api/receta/poc/emitir/", login_required(views.emitir_receta_poc), name="emitir_receta_poc"),
    path("api/pacientes-portal/validar/", views.validar_paciente_portal, name="validar_paciente_portal"),
    path(
        "api/solicitudes-receta/<int:solicitud_id>/aprobar/",
        login_required(views.aprobar_solicitud_receta),
        name="aprobar_solicitud_receta",
    ),
    path(
        "api/solicitudes-receta/<int:solicitud_id>/rechazar/",
        login_required(views.rechazar_solicitud_receta),
        name="rechazar_solicitud_receta",
    ),
]
