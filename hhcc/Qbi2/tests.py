import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase, override_settings
from django.urls import resolve, Resolver404

from Qbi2 import views
from Qbi2.client import Qbi2HTTPError
from Qbi2.models import SolicitudReceta
from Qbi2.portal import normalize_document
from Qbi2.recipes import RecetaPocResult
from Qbi2.spontaneous import (
    SpontaneousPocResult,
    build_spontaneous_payload,
    summarize_document_response,
)
from main.models import HistoriaClinica, Paciente, TipoDocumento
from main import views as main_views


class VademecumLegacyViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="legacy", password="test")

    def test_legacy_page_requires_login(self):
        response = self.client.get("/qbi2-poc/medicamentos/directo/")

        self.assertEqual(response.status_code, 302)

    def test_legacy_page_renders_after_login(self):
        request = RequestFactory().get("/qbi2-poc/medicamentos/directo/")
        request.user = self.user

        response = views.vademecum_legacy(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"qbi2 poc", response.content)

    @patch("Qbi2.views.VademecumService")
    def test_legacy_api_uses_direct_service_shape(self, service_class):
        service = service_class.return_value
        service.buscar.return_value = {
            "query": "atorva",
            "page": 1,
            "items": [{"regNo": "1", "nombreProducto": "Atorva"}],
            "page_info": {"numeroPagina": 1, "cantidadPaginas": 1, "tieneMasResultados": False},
            "raw": {"items": [{"regNo": "1"}]},
        }
        self.client.force_login(self.user)

        response = self.client.get("/qbi2-poc/api/medicamentos/directo/", {"q": "atorva", "page": "1"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["items"][0]["nombreProducto"], "Atorva")
        service.buscar.assert_called_once_with("atorva", page=1, extra_params={})


class Qbi2PocRoutingTests(TestCase):
    def test_canonical_routes_resolve_under_single_prefix(self):
        expected = {
            "/qbi2-poc/": "qbi2_poc:home",
            "/qbi2-poc/medicamentos/directo/": "qbi2_poc:medicamentos_directo",
            "/qbi2-poc/paciente/recetas/nueva/": "qbi2_poc:paciente_receta_nueva",
            "/qbi2-poc/medico/solicitudes/": "qbi2_poc:medico_solicitudes",
            "/qbi2-poc/lab/receta/": "qbi2_poc:lab_receta",
            "/qbi2-poc/lab/rcta-espontanea/": "qbi2_poc:lab_espontanea",
            "/qbi2-poc/lab/rcta-espontanea-2/": "qbi2_poc:lab_espontanea_2",
            "/qbi2-poc/api/medicamentos/directo/": "qbi2_poc:api_medicamentos_directo",
            "/qbi2-poc/api/lab/espontanea/preview/": "qbi2_poc:api_lab_espontanea_preview",
            "/qbi2-poc/api/lab/espontanea-2/preview/": "qbi2_poc:api_lab_espontanea_2_preview",
            "/qbi2-poc/api/lab/espontanea-2/pacientes/": "qbi2_poc:api_lab_espontanea_2_pacientes",
            "/qbi2-poc/api/lab/espontanea-2/emitir/": "qbi2_poc:api_lab_espontanea_2_emitir",
            "/qbi2-poc/api/lab/espontanea/emitir/": "qbi2_poc:api_lab_espontanea_emitir",
            "/qbi2-poc/api/lab/espontanea/anular/": "qbi2_poc:api_lab_espontanea_anular",
        }

        for path, view_name in expected.items():
            self.assertEqual(resolve(path).view_name, view_name)

    def test_old_legacy_routes_do_not_resolve(self):
        old_paths = [
            "/vademecum/",
            "/qbi2/vademecum-demo/",
            "/receta-poc/",
            "/poc-recetas/",
            "/poc-recetas/solicitudes/",
            "/PoC-pacientes-portal/",
        ]

        for path in old_paths:
            with self.assertRaises(Resolver404):
                resolve(path)


class RecetaPortalViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="medico", password="test")

    def test_receta_poc_page_renders(self):
        request = RequestFactory().get("/qbi2-poc/lab/receta/")
        request.user = self.user

        response = views.receta_poc_page(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Proof Of Concept", response.content)
        self.assertIn(b"Emitir receta HML", response.content)
        self.assertIn(b"34959", response.content)

    def test_pacientes_portal_page_renders(self):
        response = views.pacientes_portal_page(RequestFactory().get("/qbi2-poc/paciente/recetas/nueva/"))

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"QBI2 PoC", response.content)
        self.assertIn(b"/qbi2-poc/api/paciente/medicamentos/directo/", response.content)
        self.assertIn(b"/qbi2-poc/api/paciente/validar-y-solicitar/", response.content)

    def test_solicitudes_page_renders_empty_queue(self):
        request = RequestFactory().get("/qbi2-poc/medico/solicitudes/")
        request.user = self.user

        response = views.solicitudes_receta_page(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Solicitudes de receta", response.content)
        self.assertIn(b"No hay solicitudes", response.content)


@override_settings(
    QBI2_PROFILE_YAML_PATH=str(
        Path(__file__).resolve().parents[1] / "private" / "qbi2" / "profile.example.yaml"
    )
)
class EspontaneaPocTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="espontanea", password="test")
        self.client.force_login(self.user)
        document_type = TipoDocumento.objects.create(nombre="DNI", descripcion="Documento nacional")
        self.patient = Paciente.objects.create(
            idTipoDoc=document_type,
            numDoc="23101065",
            nombre="Ezequiel",
            apellido="Bergonzi",
            fechaNac=date(1972, 12, 18),
            sexo="H",
            mail="ezequiel@example.com",
            direccion="Zelarrayan 1492",
            localidad="CAPITAL",
            obraSocial="OSDE",
            plan="310",
            afiliado="62333891101",
            celular="1558467544",
        )

    def test_page_renders_direct_medical_request_form(self):
        request = RequestFactory().get("/qbi2-poc/lab/rcta-espontanea/")
        request.user = self.user

        response = views.espontanea_poc_page(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Prueba piloto Pedido espont", response.content)
        self.assertIn(b"Receta", response.content)
        self.assertIn("Práctica".encode(), response.content)

    def test_simplified_page_starts_without_patient_and_keeps_two_step_flow(self):
        request = RequestFactory().get("/qbi2-poc/lab/rcta-espontanea-2/")
        request.user = self.user

        response = views.espontanea_poc_2_page(request)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Bergonzi", response.content)
        self.assertNotIn(b"23101065", response.content)
        self.assertIn("Seleccioná un paciente".encode(), response.content)
        self.assertIn(b"Cambiar paciente", response.content)
        self.assertIn(b"Editar datos del paciente", response.content)
        self.assertIn(b"QBI2 homologaci", response.content)
        self.assertNotIn(b"Perfil de receta", response.content)
        self.assertNotIn(b"recipe-v2-heading", response.content)
        self.assertNotIn(b"recipe-v2-safe-badge", response.content)
        self.assertNotIn(b"<h1>Crear receta</h1>", response.content)
        self.assertIn("💊".encode(), response.content)
        self.assertIn(b"sin paciente", response.content)
        self.assertIn(b"Escribir un diagn", response.content)
        self.assertIn(b"Usar texto", response.content)
        self.assertIn(b"/qbi2-poc/api/lab/espontanea-2/pacientes/", response.content)
        self.assertIn(b"/qbi2-poc/api/lab/espontanea-2/preview/", response.content)
        self.assertIn(b"/qbi2-poc/api/lab/espontanea-2/emitir/", response.content)
        self.assertLess(response.content.index(b"Medicamentos"), response.content.index(b"Indicaciones"))
        self.assertLess(response.content.index(b"Indicaciones"), response.content.index(b"Otras configuraciones"))

    def test_simplified_profile_payload_comes_from_external_yaml(self):
        defaults = views._espontanea_2_defaults(self.patient)

        self.assertEqual(defaults["payload"]["medicoNombre"], "Omar")
        self.assertEqual(defaults["payload"]["medicoApellido"], "Prieto")
        self.assertEqual(defaults["payload"]["medicoMatriculaNumero"], "109347")
        self.assertEqual(defaults["payload"]["consultorioNombre"], "Cardiología Integral")

    def test_simplified_patient_search_returns_hhcc_data(self):
        response = self.client.get(
            "/qbi2-poc/api/lab/espontanea-2/pacientes/",
            {"q": "bergonzi"},
        )

        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["items"][0]["patient"]["id"], self.patient.id)
        self.assertEqual(data["items"][0]["patient"]["document"], "23101065")
        self.assertEqual(data["items"][0]["patient"]["edit_url"], f"/pacientes/{self.patient.id}/editar/")
        self.assertEqual(data["items"][0]["patient"]["sex_label"], "Masculino")
        self.assertEqual(data["items"][0]["coverage"]["name"], "OSDE")
        self.assertEqual(data["items"][0]["coverage"]["plan_id"], "43")
        self.assertEqual(data["items"][0]["coverage"]["member_number"], "62333891101")

    def test_simplified_patient_refresh_by_id_returns_current_hhcc_data(self):
        response = self.client.get(
            "/qbi2-poc/api/lab/espontanea-2/pacientes/",
            {"id": self.patient.id},
        )

        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["items"][0]["patient"]["id"], self.patient.id)
        self.assertEqual(data["items"][0]["patient"]["edit_url"], f"/pacientes/{self.patient.id}/editar/")

    def test_canonical_patient_editor_returns_control_to_recipe_popup(self):
        request = RequestFactory().post(
            f"/pacientes/{self.patient.id}/editar/?recipe_context=1",
            data={
                "_recipe_context": "1",
                "idTipoDoc": self.patient.idTipoDoc_id,
                "numDoc": self.patient.numDoc,
                "nombre": self.patient.nombre,
                "apellido": self.patient.apellido,
                "fechaNac": "1972-12-18",
                "sexo": "H",
                "mail": self.patient.mail,
                "direccion": self.patient.direccion,
                "localidad": self.patient.localidad,
                "obraSocial": self.patient.obraSocial,
                "plan": self.patient.plan,
                "afiliado": self.patient.afiliado,
                "telefono": "1144445555",
                "celular": self.patient.celular,
                "profesion": "Médico",
                "referente": "",
            },
        )
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)
        response = main_views.editar_paciente(request, self.patient.id)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"hhcc:patient-updated", response.content)
        self.assertIn(f"patientId: {self.patient.id}".encode(), response.content)
        self.assertIn(b"window.opener.focus()", response.content)
        self.assertIn(b"window.close()", response.content)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.telefono, "1144445555")

    def test_simplified_preview_rejects_unknown_patient(self):
        response = self.client.post(
            "/qbi2-poc/api/lab/espontanea-2/preview/",
            data=json.dumps(
                {
                    "pacienteId": 999999,
                    "diagnostico": "Hipertension arterial",
                    "medicamentos": [{"regNo": "34959", "nombreProducto": "LOTRIAL"}],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("no existe", response.json()["message"])

    @patch("Qbi2.views.emit_spontaneous_payload")
    def test_simplified_preview_never_emits_and_server_owns_patient_identity(self, emit):
        response = self.client.post(
            "/qbi2-poc/api/lab/espontanea-2/preview/",
            data=json.dumps(
                {
                    "operation": "receta",
                    "pacienteId": self.patient.id,
                    "pacienteNombre": "Otra",
                    "pacienteApellido": "Persona",
                    "pacienteNroDoc": "99999999",
                    "diagnostico": "Hipertension arterial",
                    "codigoDiagnostico": "I10",
                    "medicamentos": [
                        {
                            "regNo": "34959",
                            "nombreProducto": "LOTRIAL",
                            "nombreDroga": "enalapril",
                            "presentacion": "10 mg comp.x 30",
                            "cantidad": 1,
                            "posologia": "Tomar un comprimido por dia.",
                            "diagnostico": "Diagnóstico inyectado",
                            "codigoDiagnostico": "Z99",
                            "forzarDuplicado": True,
                        },
                        {
                            "regNo": "24818",
                            "nombreProducto": "AMPLIAR",
                            "nombreDroga": "atorvastatina",
                            "presentacion": "20 mg x 30",
                            "cantidad": 1,
                            "posologia": "Tomar segun indicacion medica.",
                        },
                    ],
                }
            ),
            content_type="application/json",
        )

        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["mode"], "preview_only")
        self.assertEqual(data["payload"]["paciente"]["nombre"], "Ezequiel")
        self.assertEqual(data["payload"]["paciente"]["apellido"], "Bergonzi")
        self.assertEqual(data["payload"]["paciente"]["nroDoc"], "23101065")
        self.assertEqual(data["payload"]["paciente"]["email"], "ezequiel@example.com")
        self.assertEqual(data["payload"]["paciente"]["telefono"], "1558467544")
        self.assertEqual(data["payload"]["paciente"]["domicilio"]["calle"], "Zelarrayan")
        self.assertEqual(data["payload"]["paciente"]["domicilio"]["numero"], "1492")
        self.assertEqual(data["payload"]["paciente"]["cobertura"]["idFinanciador"], "28")
        self.assertEqual(data["payload"]["paciente"]["cobertura"]["numero"], "62333891101")
        self.assertEqual(data["payload"]["paciente"]["cobertura"]["planId"], 43)
        self.assertEqual(data["payload"]["paciente"]["cobertura"]["plan"], "Plan310")
        self.assertEqual(len(data["payload"]["medicamentos"]), 2)
        self.assertNotIn("diagnostico", data["payload"]["medicamentos"][0])
        self.assertNotIn("codigoDiagnostico", data["payload"]["medicamentos"][0])
        self.assertFalse(data["payload"]["medicamentos"][0]["forzarDuplicado"])
        self.assertEqual(data["payload"]["diagnostico"], "I10")
        self.assertNotIn("fechaNacimiento", data["payload"]["medico"])
        self.assertNotIn("idTributario", data["payload"]["medico"])
        emit.assert_not_called()

    @patch("Qbi2.views.emit_spontaneous_payload")
    def test_simplified_emit_uses_server_owned_patient_identity(self, emit):
        emit.return_value = SpontaneousPocResult(
            operation="receta",
            endpoint="/apirecipe/Receta",
            payload={"paciente": {"nombre": "Ezequiel", "apellido": "Bergonzi", "nroDoc": "23101065"}},
            response={
                "recetas": [{"id": "hash-v2", "idReceta": "100-v2", "s3Link": "https://example.invalid/v2.pdf"}],
                "errores": [],
                "response": [{"status": "OK"}],
            },
            summary={"id": "hash-v2", "idReceta": "100-v2", "status": "OK"},
        )

        response = self.client.post(
            "/qbi2-poc/api/lab/espontanea-2/emitir/",
            data=json.dumps(
                {
                    "pacienteId": self.patient.id,
                    "pacienteNombre": "Otra",
                    "pacienteApellido": "Persona",
                    "pacienteNroDoc": "99999999",
                    "diagnostico": "Hipertension arterial",
                    "codigoDiagnostico": "I10",
                    "medicamentos": [{"regNo": "34959", "nombreProducto": "LOTRIAL", "cantidad": 1}],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary"]["idReceta"], "100-v2")
        safe_data, operation = emit.call_args.args
        self.assertEqual(operation, "receta")
        self.assertEqual(safe_data["pacienteNombre"], "Ezequiel")
        self.assertEqual(safe_data["pacienteApellido"], "Bergonzi")
        self.assertEqual(safe_data["pacienteNroDoc"], "23101065")

    def test_simplified_preview_requires_diagnosis_and_medicine(self):
        no_diagnosis = self.client.post(
            "/qbi2-poc/api/lab/espontanea-2/preview/",
            data=json.dumps({"pacienteId": self.patient.id, "medicamentos": []}),
            content_type="application/json",
        )
        no_medicine = self.client.post(
            "/qbi2-poc/api/lab/espontanea-2/preview/",
            data=json.dumps({"pacienteId": self.patient.id, "diagnostico": "Control cardiologico", "medicamentos": []}),
            content_type="application/json",
        )

        self.assertEqual(no_diagnosis.status_code, 400)
        self.assertEqual(no_medicine.status_code, 400)
        self.assertIn("diagnóstico es obligatorio", no_diagnosis.json()["message"])
        self.assertIn("al menos un medicamento", no_medicine.json()["message"])

    @patch("Qbi2.views.emit_spontaneous_payload")
    def test_simplified_preview_accepts_free_text_diagnosis_without_catalog_code(self, emit):
        response = self.client.post(
            "/qbi2-poc/api/lab/espontanea-2/preview/",
            data=json.dumps(
                {
                    "pacienteId": self.patient.id,
                    "diagnostico": "Control cardiológico por palpitaciones",
                    "codigoDiagnostico": "",
                    "medicamentos": [{"regNo": "34959", "nombreProducto": "LOTRIAL"}],
                }
            ),
            content_type="application/json",
        )

        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["payload"]["diagnostico"], "Control cardiológico por palpitaciones")
        self.assertNotIn("codigoDiagnostico", data["payload"])
        self.assertNotIn("diagnostico", data["payload"]["medicamentos"][0])
        emit.assert_not_called()

    def test_simplified_preview_rejects_overlong_free_text_diagnosis(self):
        response = self.client.post(
            "/qbi2-poc/api/lab/espontanea-2/preview/",
            data=json.dumps(
                {
                    "pacienteId": self.patient.id,
                    "diagnostico": "x" * 256,
                    "medicamentos": [{"regNo": "34959", "nombreProducto": "LOTRIAL"}],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("255 caracteres", response.json()["message"])

    @patch("Qbi2.views.emit_spontaneous_payload")
    def test_simplified_emit_preserves_direct_provider_error(self, emit):
        emit.side_effect = Qbi2HTTPError(
            "QBI2 devolvio un error HTTP.",
            status_code=400,
            payload={"error": "QBI184", "mensaje": "EL NÚMERO DE AFILIADO INGRESADO ES INVÁLIDO"},
        )

        response = self.client.post(
            "/qbi2-poc/api/lab/espontanea-2/emitir/",
            data=json.dumps(
                {
                    "pacienteId": self.patient.id,
                    "diagnostico": "Hipertension arterial",
                    "medicamentos": [{"regNo": "34959", "nombreProducto": "LOTRIAL"}],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["provider_payload"]["error"], "QBI184")
        self.assertIn("AFILIADO", response.json()["provider_payload"]["mensaje"])

    def test_receta_payload_uses_catalog_identifiers(self):
        endpoint, payload = build_spontaneous_payload(
            {
                "regNo": "34959",
                "nombreProducto": "LOTRIAL",
                "nombreDroga": "enalapril",
                "presentacion": "10 mg comp.x 30",
                "cantidad": "2",
                "diagnostico": "Hipertension arterial",
                "codigoDiagnostico": "I10",
            },
            "receta",
        )

        self.assertEqual(endpoint, "/apirecipe/Receta")
        self.assertEqual(payload["medicamentos"][0]["regNo"], "34959")
        self.assertEqual(payload["medicamentos"][0]["codigoDiagnostico"], "I10")

    def test_practica_payload_keeps_qbi2_id_and_snomed_separate(self):
        endpoint, payload = build_spontaneous_payload(
            {
                "practicaId": "42",
                "practicaNombre": "Ecocardiograma Doppler",
                "practicaCodSnomed": "40701008",
                "practicaCodigoPropio": "ECO-01",
                "practicaCantidad": "1",
                "diagnostico": "Control cardiologico",
            },
            "practica",
        )

        item = payload["prescripcion"][0]
        self.assertEqual(endpoint, "/apirecipe/prescribirPractica")
        self.assertEqual(item["id"], 42)
        self.assertEqual(item["codSnomed"], "40701008")
        self.assertEqual(item["codigo"], "ECO-01")

    @patch("Qbi2.views.emit_spontaneous_payload")
    def test_emit_api_returns_document_summary_and_provider_response(self, emit):
        emit.return_value = SpontaneousPocResult(
            operation="receta",
            endpoint="/apirecipe/Receta",
            payload={"medicamentos": [{"regNo": "34959"}]},
            response={
                "recetas": [{"id": "hash-1", "idReceta": "100", "s3Link": "https://example.invalid/receta.pdf"}],
                "errores": [],
            },
            summary={"id": "hash-1", "idReceta": "100", "s3Link": "https://example.invalid/receta.pdf"},
        )

        response = self.client.post(
            "/qbi2-poc/api/lab/espontanea/emitir/",
            data=json.dumps({"operation": "receta", "regNo": "34959"}),
            content_type="application/json",
        )

        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["summary"]["id"], "hash-1")
        self.assertEqual(data["response"]["recetas"][0]["idReceta"], "100")

    @patch("Qbi2.views.emit_spontaneous_payload")
    def test_emit_api_preserves_exact_qbi2_error_payload(self, emit):
        emit.side_effect = Qbi2HTTPError(
            "QBI2 devolvio un error HTTP.",
            status_code=400,
            payload={"errores": [{"error": "QBI136", "mensaje": "Dato invalido"}]},
        )

        response = self.client.post(
            "/qbi2-poc/api/lab/espontanea/emitir/",
            data=json.dumps({"operation": "receta", "regNo": "34959"}),
            content_type="application/json",
        )

        data = response.json()
        self.assertEqual(response.status_code, 502)
        self.assertEqual(data["provider_status"], 400)
        self.assertEqual(data["provider_payload"]["errores"][0]["error"], "QBI136")

    @patch("Qbi2.views.anular_documento_hash")
    def test_anular_api_uses_hash_and_operation(self, anular):
        anular.return_value = {"ok": True}

        response = self.client.post(
            "/qbi2-poc/api/lab/espontanea/anular/",
            data=json.dumps({"operation": "practica", "hash": "hash-practica"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        anular.assert_called_once_with("hash-practica", "practica")

    def test_anular_rejects_missing_hash(self):
        response = self.client.post(
            "/qbi2-poc/api/lab/espontanea/anular/",
            data=json.dumps({"operation": "receta"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("hash QBI2 es obligatorio", response.json()["message"])

    def test_summary_distinguishes_document_hash_from_prescription_number(self):
        summary = summarize_document_response(
            {
                "prescripciones": [
                    {"id": "hash-practica", "numeroPrescripcion": "P-100", "verificador": "https://example.invalid/verificar"}
                ],
                "response": [{"status": "OK"}],
            },
            operation="practica",
        )

        self.assertEqual(summary["id"], "hash-practica")
        self.assertEqual(summary["numeroPrescripcion"], "P-100")


class PacientesPortalTests(TestCase):
    def test_normalizes_document(self):
        self.assertEqual(normalize_document("12.345.678"), "12345678")

    def test_rejects_when_patient_has_no_history(self):
        request = RequestFactory().post(
            "/qbi2-poc/api/paciente/validar-y-solicitar/",
            data=json.dumps({"apellido": "Perez", "documento": "12345678"}),
            content_type="application/json",
        )
        request._dont_enforce_csrf_checks = True

        with patch("Qbi2.views.find_patient_history", return_value=(None, None)):
            response = views.validar_paciente_portal(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content)["message"], "No tenes Historia Clinica")

    def test_accepts_when_patient_has_history_and_splits_medications(self):
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
            "/qbi2-poc/api/paciente/validar-y-solicitar/",
            data=json.dumps(
                {
                    "apellido": "Perez",
                    "documento": "12345678",
                    "medicamentosJson": json.dumps(selected_medications),
                    "diagnostico": "Hipertension arterial",
                }
            ),
            content_type="application/json",
        )
        request._dont_enforce_csrf_checks = True
        captured = []

        def fake_create(*args, **kwargs):
            captured.append({"args": args, "kwargs": kwargs})
            return Request()

        with (
            patch("Qbi2.views.find_patient_history", return_value=(Patient(), History())),
            patch("Qbi2.views.create_prescription_request", side_effect=fake_create),
        ):
            response = views.validar_paciente_portal(request)

        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["solicitudes"]), 2)
        self.assertEqual(len(captured[0]["kwargs"]["medicamentos"]), 2)
        self.assertEqual(captured[0]["kwargs"]["receta_orden"], 1)
        self.assertEqual(captured[1]["args"][2]["regNo"], "7799")


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
        self.user = get_user_model().objects.create_user(username="omar", password="test")

    def test_reject_pending_request(self):
        solicitud = SolicitudReceta.objects.create(
            paciente=self.paciente,
            historia_clinica=self.historia,
            medicamento_reg_no="34959",
            medicamento_nombre_producto="LOTRIAL",
        )
        self.client.force_login(self.user)

        response = self.client.post(
            f"/qbi2-poc/api/medico/solicitudes/{solicitud.id}/rechazar/",
            {"observacion_medico": "No corresponde"},
        )
        solicitud.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(solicitud.estado, SolicitudReceta.Estado.RECHAZADA)
        self.assertEqual(solicitud.observacion_medico, "No corresponde")

    def test_approve_pending_request_marks_emitted_when_qbi2_returns_pdf(self):
        solicitud = SolicitudReceta.objects.create(
            paciente=self.paciente,
            historia_clinica=self.historia,
            medicamento_reg_no="34959",
            medicamento_nombre_producto="LOTRIAL",
            medicamento_nombre_droga="enalapril",
            medicamento_presentacion="10 mg comp.x 30",
        )
        self.client.force_login(self.user)

        with patch(
            "Qbi2.views.emitir_receta_payload",
            return_value=RecetaPocResult(
                payload={"paciente": {"nroDoc": "12345678"}, "medicamentos": [{"regNo": "34959"}]},
                response={
                    "recetas": [{"idReceta": "9600000255038", "s3Link": "https://example.invalid/receta.pdf"}],
                    "errores": [],
                    "response": [{"status": "OK"}],
                },
            ),
        ):
            response = self.client.post(
                f"/qbi2-poc/api/medico/solicitudes/{solicitud.id}/aprobar/",
                {
                    "diagnostico": "Hipertension arterial",
                    "posologia": "Tomar segun indicacion medica.",
                    "observacion_medico": "Autorizada",
                },
            )
        solicitud.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(solicitud.estado, SolicitudReceta.Estado.EMITIDA)
        self.assertEqual(solicitud.qbi2_pdf_url, "https://example.invalid/receta.pdf")
        self.assertEqual(solicitud.diagnostico, "Hipertension arterial")
