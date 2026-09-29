from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import resolve
from django.utils import timezone

from .models import HistoriaClinica, Paciente, TipoDocumento


class HistoriaClinicaCoreTests(TestCase):
    def setUp(self):
        self.tipo_documento = TipoDocumento.objects.create(nombre="DNI", descripcion="Documento")

    def test_creating_patient_creates_one_history(self):
        paciente = Paciente.objects.create(
            idTipoDoc=self.tipo_documento,
            numDoc="12345678",
            nombre="Ana",
            apellido="Perez",
            sexo="M",
        )

        historias = HistoriaClinica.objects.filter(paciente=paciente)

        self.assertEqual(historias.count(), 1)
        self.assertEqual(historias.get().fechaAlta, timezone.localdate(paciente.fechaAlta))

    def test_main_workflow_routes_require_login(self):
        protected_paths = [
            "/",
            "/pacientes/",
            "/historias/",
            "/historial_medico/1/",
            "/historia/1/indicaciones/",
        ]

        for path in protected_paths:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 302, path)
            self.assertIn("/login/", response["Location"], path)

    def test_main_routes_keep_expected_destinations(self):
        expected = {
            "/": "index",
            "/pacientes/": "listar_buscar_pacientes",
            "/historias/": "listar_buscar_historias",
            "/historial_medico/1/": "detalle_historia_con_historial",
            "/historia/1/indicaciones/": "indicaciones",
        }

        for path, view_name in expected.items():
            self.assertEqual(resolve(path).view_name, view_name)

    def test_authenticated_user_can_invoke_main_index(self):
        user = get_user_model().objects.create_user(username="clinico", password="test")
        request = RequestFactory().get("/")
        request.user = user

        with patch("main.views.render", return_value=HttpResponse("ok")):
            from main.views import index

            response = index(request)

        self.assertEqual(response.status_code, 200)
