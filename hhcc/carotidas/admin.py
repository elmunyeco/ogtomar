from django.contrib import admin

from .models import CarotidasEstudio


@admin.register(CarotidasEstudio)
class CarotidasEstudioAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "historia",
        "com_derecha",
        "com_izquierda",
        "esp_int_med_der",
        "esp_int_med_izq",
    )
    search_fields = ("historia__id", "historia__paciente__apellido", "historia__paciente__nombre")
