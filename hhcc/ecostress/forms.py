from django import forms

from .models import EcostressEstudio


class EcostressForm(forms.ModelForm):
    class Meta:
        model = EcostressEstudio
        fields = [
            "historia",
            "indicacion_estudio",
            "tipo_apremio",
            "medicacion_momento_estudio",
            "medico_solicitante",
            "frecuencia_cardiaca_basal",
            "frecuencia_cardiaca_maxima",
            "presion_arterial_basal_inicial",
            "presion_arterial_basal_final",
            "presion_arterial_maxima_inicial",
            "presion_arterial_maxima_final",
            "informe_ergometria",
            "datos_ecocardiograficos_basales",
            "datos_ecocardiograficos_post_esfuerzo_inmediato",
            "conclusion",
        ]
        widgets = {
            "historia": forms.HiddenInput(),
        }
