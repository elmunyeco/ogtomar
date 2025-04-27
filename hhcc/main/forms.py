from django import forms
from .models import Paciente, TipoDocumento

class PacienteForm(forms.ModelForm):
    """
    Formulario para la creación y edición de pacientes
    """
    class Meta:
        model = Paciente
        fields = [
            'idTipoDoc', 'numDoc', 'nombre', 'apellido', 'fechaNac', 'sexo',
            'mail', 'direccion', 'localidad', 'obraSocial', 'plan', 'afiliado',
            'telefono', 'celular', 'profesion', 'referente'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar widgets y etiquetas
        self.fields['idTipoDoc'].label = "Tipo de Documento"
        self.fields['numDoc'].label = "Número de Documento"
        self.fields['fechaNac'].label = "Fecha de Nacimiento"
        self.fields['fechaNac'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['mail'].label = "Correo Electrónico"
        self.fields['obraSocial'].label = "Obra Social"
        self.fields['afiliado'].label = "Número de Afiliado"
        self.fields['referente'].label = "Médico Referente"
        
        # Hacer que algunos campos no sean obligatorios
        optional_fields = ['mail', 'direccion', 'localidad', 'plan', 'celular', 'referente']
        for field in optional_fields:
            self.fields[field].required = False