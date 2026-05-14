from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

app_name = "qbi2"

urlpatterns = [
    path("health/", login_required(views.health), name="health"),
    path("api/vademecum/buscar/", login_required(views.buscar_vademecum), name="buscar_vademecum"),
]
