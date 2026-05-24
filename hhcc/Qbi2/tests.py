import json

from django.contrib.auth.models import User
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from main.models import HistoriaClinica, Paciente, TipoDocumento

from .models import SolicitudReceta
from .portal import normalize_document
from .recipes import RecetaPocResult, build_hml_receta_poc_payload, build_receta_payload_from_solicitud, summarize_receta_response
from .services import VademecumService, normalize_medicamento, normalize_vademecum_response
from . import views
from .views import buscar_vademecum, emitir_receta_poc, pacientes_portal_page, receta_poc_page, vademecum_page


class FakeClient:
    def __init__(self):
        self.calls = []

    def get(self, path, params=None):
        self.calls.append((path, params))
        return {
            "medicamentos": [
                {
                    "nombreProducto": "AMPLIAR",
                    "nombreDroga": "atorvastatin",
                    "presentacion": "20 mg comp.x 30",
                    "regNo": "24818",
                }
            ],
            "pageInfo": {"numeroPagina": 1, "tieneMasResultados": True},
        }


class VademecumServiceTests(SimpleTestCase):
    def test_normalizes_common_list_response(self):
        self.assertEqual(normalize_vademecum_response({"items": [1, 2]}), [1, 2])

    @override_settings(
        QBI2_VADEMECUM_PATH="/apirecipe/GetMedicamento/{search}",
        QBI2_VADEMECUM_PAGE_PARAM="numeroPagina",
        QBI2_CLIENT_APP_ID="563",
        QBI2_CLIENT_APP_ID_PARAM="clienteAppId",
        QBI2_INCLUDE_CLIENT_APP_ID_IN_VADEMECUM=True,
    )
    def test_builds_provider_query(self):
        client = FakeClient()
        result = VademecumService(client=client).buscar("atorva", page=2)

        self.assertEqual(result["items"][0]["regNo"], "24818")
        self.assertEqual(result["page_info"], {"numeroPagina": 1, "tieneMasResultados": True})
        self.assertEqual(client.calls[0][0], "/apirecipe/GetMedicamento/atorva")
        self.assertEqual(client.calls[0][1]["numeroPagina"], 2)
        self.assertEqual(client.calls[0][1]["clienteAppId"], "563")

    def test_normalizes_medicamento_display(self):
        item = normalize_medicamento(
            {
                "nombreProducto": "AMPLIAR",
                "nombreDroga": "atorvastatin",
                "presentacion": "20 mg comp.x 30",
                "regNo": "24818",
            }
        )

        self.assertEqual(item["display"], "AMPLIAR - atorvastatin - 20 mg comp.x 30")
        self.assertEqual(item["regNo"], "24818")


class VademecumViewTests(SimpleTestCase):
    def test_requires_query(self):
        request = RequestFactory().get("/qbi2/api/vademecum/buscar/")
        response = buscar_vademecum(request)

        self.assertEqual(response.status_code, 400)

    def test_vademecum_page_renders_search_ui(self):
        request = RequestFactory().get("/vademecum/")
        response = vademecum_page(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"vademecum-input", response.content)
        self.assertIn(b"/qbi2/api/vademecum/buscar/", response.content)

    def test_receta_poc_page_renders_poc_ui(self):
        request = RequestFactory().get("/receta-poc/")
        response = receta_poc_page(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Proof Of Concept", response.content)
        self.assertIn(b"Emitir receta HML", response.content)
        self.assertIn(b"34959", response.content)

    def test_receta_poc_endpoint_requires_post(self):
        request = RequestFactory().get("/qbi2/api/receta/poc/emitir/")
        response = emitir_receta_poc(request)

        self.assertEqual(response.status_code, 405)

    def test_pacientes_portal_page_renders_poc_ui(self):
        request = RequestFactory().get("/PoC-pacientes-portal/")
        response = pacientes_portal_page(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"PoC-pacientes-portal", response.content)
        self.assertIn(b"Ped\xc3\xad tu Receta", response.content)
        self.assertIn(b"seleccionar hasta 10 medicamentos", response.content)
        self.assertIn(b"Diagn\xc3\xb3stico", response.content)
        self.assertNotIn(b"observacionPaciente", response.content)
        self.assertIn(b"pedi tu receta", response.content)
        self.assertIn(b"/qbi2/api/pacientes-portal/vademecum/buscar/", response.content)
        self.assertIn(b"/qbi2/api/pacientes-portal/validar/", response.content)


class RecetaPocTests(SimpleTestCase):
    @override_settings(QBI2_CLIENT_APP_ID="563")
    def test_builds_hml_receta_payload_with_lotrial_reg_no(self):
        payload = build_hml_receta_poc_payload(nro_doc="99999999")

        self.assertEqual(payload["clienteAppId"], 563)
        self.assertEqual(payload["diagnostico"], "Hipertension arterial")
        self.assertEqual(payload["paciente"]["nroDoc"], "99999999")
        self.assertEqual(payload["medicamentos"][0]["regNo"], "34959")
        self.assertEqual(payload["medicamentos"][0]["nombreProducto"], "LOTRIAL")

    def test_summarizes_receta_response(self):
        summary = summarize_receta_response(
            {
                "recetas": [
                    {
                        "id": "HASH",
                        "fecha": "21/05/2026",
                        "idReceta": "9600000255038",
                        "s3Link": "https://example.invalid/receta.pdf",
                        "verificador": "https://example.invalid/verificador",
                    }
                ],
                "errores": [],
                "response": [{"status": "OK", "fechavencimiento": "20/06/2026"}],
                "idTransaccion": "tx",
            }
        )

        self.assertEqual(summary["id"], "HASH")
        self.assertEqual(summary["idReceta"], "9600000255038")
        self.assertEqual(summary["status"], "OK")

    def test_builds_payload_with_multiple_selected_medications(self):
        class Patient:
            numDoc = "12345678"
            nombre = "Ana"
            apellido = "Perez"
            sexo = "M"
            fechaNac = None
            mail = ""
            celular = ""
            telefono = ""
            localidad = ""
            direccion = ""

        class Request:
            paciente = Patient()
            medicamento_reg_no = "34959"
            medicamento_nombre_producto = "LOTRIAL"
            medicamento_nombre_droga = "enalapril"
            medicamento_presentacion = "10 mg comp.x 30"
            auditoria = {
                "medicamentos": [
                    {
                        "regNo": "34959",
                        "nombreProducto": "LOTRIAL",
                        "nombreDroga": "enalapril",
                        "presentacion": "10 mg comp.x 30",
                    },
                    {
                        "regNo": "24818",
                        "nombreProducto": "AMPLIAR",
                        "nombreDroga": "atorvastatin",
                        "presentacion": "20 mg comp.x 30",
                    },
                    {
                        "regNo": "7799",
                        "nombreProducto": "LOTRIAL",
                        "nombreDroga": "enalapril",
                        "presentacion": "5 mg comp.x 50",
                    },
                ]
            }

        payload = build_receta_payload_from_solicitud(
            Request(),
            diagnostico="Hipertension arterial",
            posologia="Tomar segun indicacion medica.",
        )

        self.assertEqual(len(payload["medicamentos"]), 2)
        self.assertEqual(payload["medicamentos"][0]["regNo"], "34959")
        self.assertEqual(payload["medicamentos"][1]["regNo"], "24818")


class PacientesPortalTests(TestCase):
    def test_normalizes_document(self):
        self.assertEqual(normalize_document("12.345.678"), "12345678")

    def test_rejects_when_patient_has_no_history(self):
        request = RequestFactory().post(
            "/qbi2/api/pacientes-portal/validar/",
            data=json.dumps({"apellido": "Perez", "documento": "12345678"}),
            content_type="application/json",
        )
        request._dont_enforce_csrf_checks = True
        original = views.find_patient_history
        views.find_patient_history = lambda apellido, documento: (None, None)
        try:
            response = views.validar_paciente_portal(request)
        finally:
            views.find_patient_history = original

        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content)["message"], "No tenes Historia Clinica")

    def test_accepts_when_patient_has_history(self):
        class Patient:
            id = 10
            nombre = "Ana"
            apellido = "Perez"
            numDoc = "12345678"

        class History:
            id = 20

        class Request:
            id = 30
            estado = "pendiente"
            auditoria = {"medicamentos": []}

        selected_medications = [
            {"regNo": "34959", "nombreProducto": "LOTRIAL"},
            {"regNo": "24818", "nombreProducto": "AMPLIAR"},
            {"regNo": "7799", "nombreProducto": "LOTRIAL"},
        ]
        request = RequestFactory().post(
            "/qbi2/api/pacientes-portal/validar/",
            data=json.dumps(
                {
                    "apellido": "Perez",
                    "documento": "12345678",
                    "regNo": "34959",
                    "nombreProducto": "LOTRIAL",
                    "medicamentosJson": json.dumps(selected_medications),
                    "diagnostico": "Hipertension arterial",
                }
            ),
            content_type="application/json",
        )
        request._dont_enforce_csrf_checks = True
        original_find = views.find_patient_history
        original_create = views.create_prescription_request
        captured = []
        views.find_patient_history = lambda apellido, documento: (Patient(), History())
        def fake_create(*args, **kwargs):
            captured.append({"args": args, "kwargs": kwargs})
            return Request()
        views.create_prescription_request = fake_create
        try:
            response = views.validar_paciente_portal(request)
        finally:
            views.find_patient_history = original_find
            views.create_prescription_request = original_create

        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["solicitud"]["estado"], "pendiente")
        self.assertEqual(len(data["solicitudes"]), 2)
        self.assertEqual(data["paciente"]["documento"], "12345678")
        self.assertEqual(len(captured), 2)
        self.assertEqual(captured[0]["args"][2]["regNo"], "34959")
        self.assertEqual(len(captured[0]["kwargs"]["medicamentos"]), 2)
        self.assertEqual(captured[0]["kwargs"]["medicamentos"][1]["regNo"], "24818")
        self.assertEqual(captured[0]["kwargs"]["receta_orden"], 1)
        self.assertEqual(captured[0]["kwargs"]["total_recetas"], 2)
        self.assertEqual(captured[0]["kwargs"]["diagnostico"], "Hipertension arterial")
        self.assertEqual(captured[1]["args"][2]["regNo"], "7799")
        self.assertEqual(len(captured[1]["kwargs"]["medicamentos"]), 1)
        self.assertEqual(captured[1]["kwargs"]["receta_orden"], 2)


class SolicitudRecetaQueueTests(TestCase):
    def setUp(self):
        tipo_doc = TipoDocumento.objects.create(nombre="DNI", descripcion="Documento")
        self.paciente = Paciente.objects.create(
            idTipoDoc=tipo_doc,
            numDoc="12345678",
            nombre="Ana",
            apellido="Perez",
            sexo="M",
        )
        self.historia = HistoriaClinica.objects.create(paciente=self.paciente)
        self.user = User.objects.create_user(username="omar", password="test")

    def test_internal_queue_lists_pending_requests(self):
        SolicitudReceta.objects.create(
            paciente=self.paciente,
            historia_clinica=self.historia,
            medicamento_reg_no="34959",
            medicamento_nombre_producto="LOTRIAL",
        )

        request = RequestFactory().get("/receta-poc/solicitudes/")
        request.user = self.user
        response = views.solicitudes_receta_page(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"LOTRIAL", response.content)
        self.assertIn(b"Pendiente", response.content)

    def test_approve_pending_request(self):
        solicitud = SolicitudReceta.objects.create(
            paciente=self.paciente,
            historia_clinica=self.historia,
            medicamento_reg_no="34959",
            medicamento_nombre_producto="LOTRIAL",
            medicamento_nombre_droga="enalapril",
            medicamento_presentacion="10 mg comp.x 30",
        )

        self.client.force_login(self.user)
        original_emitir = views.emitir_receta_payload
        views.emitir_receta_payload = lambda payload: RecetaPocResult(
            payload=payload,
            response={
                "recetas": [{"idReceta": "9600000255038", "s3Link": "https://example.invalid/receta.pdf"}],
                "errores": [],
                "response": [{"status": "OK"}],
            },
        )
        try:
            response = self.client.post(
                f"/qbi2/api/solicitudes-receta/{solicitud.id}/aprobar/",
                {
                    "diagnostico": "Hipertension arterial",
                    "posologia": "Tomar segun indicacion medica.",
                    "observacion_medico": "Autorizada",
                },
            )
        finally:
            views.emitir_receta_payload = original_emitir
        solicitud.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(solicitud.estado, SolicitudReceta.Estado.EMITIDA)
        self.assertEqual(solicitud.observacion_medico, "Autorizada")
        self.assertEqual(solicitud.diagnostico, "Hipertension arterial")
        self.assertEqual(solicitud.qbi2_pdf_url, "https://example.invalid/receta.pdf")
        self.assertEqual(solicitud.payload_qbi2["paciente"]["nroDoc"], "12345678")
        self.assertEqual(solicitud.payload_qbi2["medicamentos"][0]["regNo"], "34959")

    def test_builds_payload_from_request_patient_and_medication(self):
        self.paciente.mail = "ana@example.invalid"
        self.paciente.telefono = "1122223333"
        self.paciente.localidad = "Lanus"
        self.paciente.direccion = "Av Siempre Viva 742"
        self.paciente.save()
        solicitud = SolicitudReceta.objects.create(
            paciente=self.paciente,
            historia_clinica=self.historia,
            medicamento_reg_no="34959",
            medicamento_nombre_producto="LOTRIAL",
            medicamento_nombre_droga="enalapril",
            medicamento_presentacion="10 mg comp.x 30",
        )

        payload = build_receta_payload_from_solicitud(
            solicitud,
            diagnostico="Hipertension arterial",
            posologia="Tomar 1 comprimido por dia.",
        )

        self.assertEqual(payload["paciente"]["apellido"], "Perez")
        self.assertEqual(payload["paciente"]["email"], "ana@example.invalid")
        self.assertEqual(payload["paciente"]["domicilio"]["calle"], "Av Siempre Viva")
        self.assertEqual(payload["paciente"]["domicilio"]["numero"], "742")
        self.assertEqual(payload["medicamentos"][0]["nombreProducto"], "LOTRIAL")
