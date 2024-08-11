from django import forms
from .models import Paciente, Identificacion, TipoDocumento

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = '__all__'