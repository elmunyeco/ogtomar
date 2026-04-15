from django import forms

from .models import MmiiEstudio


class MmiiForm(forms.ModelForm):
    class Meta:
        model = MmiiEstudio
        fields = [
            "historia",
            "art_fem_comun_derecha",
            "art_fem_superficial_derecha",
            "art_fem_profunda_derecha",
            "art_poplitea_derecha",
            "art_infrapatelares_derecha",
            "art_fem_comun_izquierda",
            "art_fem_superficial_izquierda",
            "art_fem_profunda_izquierda",
            "art_poplitea_izquierda",
            "art_infrapatelares_izquierda",
            "conclusion",
        ]
        widgets = {"historia": forms.HiddenInput()}
