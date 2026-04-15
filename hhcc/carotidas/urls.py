from django.urls import path

from . import views


app_name = "carotidas"

urlpatterns = [
    path("<int:historia_id>/", views.nuevo_estudio, name="carotidas_form"),
    path("<int:historia_id>/estudios/", views.listar_estudios, name="carotidas_listar_estudios"),
    path("<int:historia_id>/nuevo/", views.nuevo_estudio, name="carotidas_nuevo"),
    path("estudio/<int:pk>/", views.detalle_estudio, name="carotidas_detalle"),
    path(
        "imprimir_estudio/<int:estudio_id>/<int:historia_id>/",
        views.imprimir_estudio,
        name="carotidas_imprimir",
    ),
]
