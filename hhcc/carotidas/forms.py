from decimal import Decimal, InvalidOperation

from django import forms

from .models import CarotidasEstudio


class CarotidasForm(forms.ModelForm):
    esp_int_med_der = forms.CharField(required=False)
    esp_int_med_izq = forms.CharField(required=False)

    class Meta:
        model = CarotidasEstudio
        fields = [
            "historia",
            "com_derecha",
            "int_derecha",
            "ext_derecha",
            "com_izquierda",
            "int_izquierda",
            "ext_izquierda",
            "art_vertebrales",
            "sugerencias",
            "id_com_der",
            "id_com_izq",
            "esp_int_med_der",
            "esp_int_med_izq",
        ]
        widgets = {
            "historia": forms.HiddenInput(),
        }

    def clean(self):
        cleaned = super().clean()
        # Normalizar decimales si vienen con coma
        for field in ["esp_int_med_der", "esp_int_med_izq"]:
            val = self.data.get(field)
            if val and "," in val:
                val = val.replace(",", ".")
            if val:
                try:
                    cleaned[field] = Decimal(val)
                except InvalidOperation:
                    self.add_error(field, "Por favor, escriba un número válido.")
        return cleaned
