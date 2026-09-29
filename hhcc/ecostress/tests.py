from django.test import RequestFactory, TestCase

from main.models import HistoriaClinica, Paciente, TipoDocumento

from .models import EcostressEstudio
from .views import listar_estudios


class ListarEstudiosTests(TestCase):
    def test_admite_estudios_legados_sin_fecha(self):
        tipo_documento = TipoDocumento.objects.create(
            nombre="DNI",
            descripcion="Documento Nacional de Identidad",
        )
        paciente = Paciente.objects.create(
            idTipoDoc=tipo_documento,
            numDoc="1",
            nombre="Paciente",
            apellido="De prueba",
            sexo="H",
        )
        historia = HistoriaClinica.objects.create(paciente=paciente)
        estudio = EcostressEstudio.objects.create(
            historia=historia,
            fecha_estudio=None,
        )

        response = listar_estudios(RequestFactory().get("/"), historia.pk)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"{estudio.pk} - Sin fecha")
