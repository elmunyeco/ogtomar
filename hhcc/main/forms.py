from django import forms
from django.core.exceptions import ValidationError
from .models import Paciente, TipoDocumento

class Qbi2CoverageFormMixin:
    coverage_fields = ("obraSocial", "plan", "qbi2_financiador_id", "qbi2_plan_id")
    allow_unchanged_legacy_coverage = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_coverage = tuple(
            getattr(self.instance, name, None) for name in self.coverage_fields
        )
        for name in self.coverage_fields:
            if name in self.fields:
                self.fields[name].required = False
                self.fields[name].widget = forms.HiddenInput()

    def clean(self):
        cleaned = super().clean()
        coverage_name = (cleaned.get("obraSocial") or "").strip()
        financier_id = cleaned.get("qbi2_financiador_id")
        plan_id = cleaned.get("qbi2_plan_id")
        if not coverage_name and not financier_id:
            for name in self.coverage_fields:
                cleaned[name] = None if name.endswith("_id") else ""
            cleaned["afiliado"] = ""
            return cleaned

        original_name, original_plan, original_financier, original_plan_id = self._original_coverage
        normalized_original_name = " ".join((original_name or "").casefold().split())
        original_is_private = normalized_original_name in {
            "", "particular", "sin cobertura", "ninguna", "sin obra social",
        }
        unchanged_legacy = (
            not financier_id
            and not original_financier
            and coverage_name == (original_name or "").strip()
            and (cleaned.get("plan") or "").strip() == (original_plan or "").strip()
        )
        if unchanged_legacy and (self.allow_unchanged_legacy_coverage or original_is_private):
            return cleaned
        if not financier_id:
            self.add_error("obraSocial", "Seleccionar una cobertura del catálogo QBI2 o Sin cobertura.")
            return cleaned

        from Qbi2.client import Qbi2ConfigurationError, Qbi2HTTPError
        from Qbi2.services import FinanciadorService

        try:
            canonical = FinanciadorService().resolve_selection(financier_id, plan_id)
        except (Qbi2ConfigurationError, Qbi2HTTPError):
            self.add_error("obraSocial", "No se pudo validar la cobertura con QBI2. Intentar nuevamente.")
            return cleaned
        except ValidationError as exc:
            self.add_error("obraSocial", exc)
            return cleaned

        selected_plan = canonical["plan"]
        cleaned["obraSocial"] = canonical["nombreComercial"]
        cleaned["qbi2_financiador_id"] = canonical["idFinanciador"]
        cleaned["plan"] = selected_plan["nombre"] if selected_plan else ""
        cleaned["qbi2_plan_id"] = selected_plan["id"] if selected_plan else None
        return cleaned


class PacienteForm(Qbi2CoverageFormMixin, forms.ModelForm):
    """
    Formulario para la creación y edición de pacientes
    """
    class Meta:
        model = Paciente
        fields = [
            'idTipoDoc', 'numDoc', 'nombre', 'apellido', 'fechaNac', 'sexo',
            'mail', 'direccion', 'localidad', 'obraSocial', 'plan',
            'qbi2_financiador_id', 'qbi2_plan_id', 'afiliado',
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


class PacientePortalForm(Qbi2CoverageFormMixin, forms.ModelForm):
    """Datos no clinicos que el propio paciente puede mantener."""

    allow_unchanged_legacy_coverage = False

    class Meta:
        model = Paciente
        fields = [
            "sexo", "direccion", "telefono", "celular", "mail", "obraSocial",
            "plan", "qbi2_financiador_id", "qbi2_plan_id", "afiliado",
        ]
        labels = {
            "sexo": "Sexo",
            "direccion": "Dirección",
            "telefono": "Teléfono",
            "celular": "Celular",
            "mail": "Correo electrónico",
            "obraSocial": "Cobertura",
            "afiliado": "Número de afiliado",
        }
        widgets = {
            "mail": forms.EmailInput(attrs={"autocomplete": "email"}),
            "direccion": forms.TextInput(attrs={"autocomplete": "street-address"}),
            "telefono": forms.TextInput(attrs={"autocomplete": "tel"}),
            "celular": forms.TextInput(attrs={"autocomplete": "tel"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.required = name == "sexo"
