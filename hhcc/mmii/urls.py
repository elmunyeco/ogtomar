from django.urls import path

from . import views


app_name = "mmii"

urlpatterns = [
    path("<int:historia_id>/", views.nuevo_estudio, name="mmii_form"),
    path("<int:historia_id>/estudios/", views.listar_estudios, name="mmii_listar_estudios"),
    path("<int:historia_id>/nuevo/", views.nuevo_estudio, name="mmii_nuevo"),
    path(
        "imprimir_estudio/<int:estudio_id>/<int:historia_id>/",
        views.imprimir_estudio,
        name="mmii_imprimir",
    ),
]
