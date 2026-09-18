import json
from datetime import date
from email import policy
from email.parser import BytesParser
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import resolve, Resolver404

from Qbi2 import views
from Qbi2.client import Qbi2HTTPError
from Qbi2.models import EmisionSolicitudReceta, SolicitudReceta
from Qbi2.notifications import (
    PRESCRIPTION_EMAIL_BODY,
    PRESCRIPTION_EMAIL_SUBJECT,
    PrescriptionNotificationError,
    download_prescription_pdf,
)
from Qbi2.portal import find_patient_history, normalize_document
from Qbi2.services import VademecumService
from Qbi2.rcta import (
    RctaResult,
    build_rcta_payload,
    summarize_receta_response,
)
from main.models import HistoriaClinica, Paciente, TipoDocumento
from main import views as main_views


class MedicamentosViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="medicamentos", password="test")

    def test_page_requires_login(self):
        response = self.client.get("/recetas/medicamentos/")

        self.assertEqual(response.status_code, 302)

    def test_page_renders_after_login(self):
        request = RequestFactory().get("/recetas/medicamentos/")
        request.user = self.user

        response = views.medicamentos_page(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"RCTA", response.content)

    @patch("Qbi2.views.VademecumService")
    def test_api_uses_direct_service_shape(self, service_class):
        service = service_class.return_value
        service.buscar.return_value = {
            "query": "atorva",
            "page": 1,
            "items": [{"regNo": "1", "nombreProducto": "Atorva"}],
            "page_info": {"numeroPagina": 1, "cantidadPaginas": 1, "tieneMasResultados": False},
            "raw": {"items": [{"regNo": "1"}]},
        }
        self.client.force_login(self.user)

        response = self.client.get("/recetas/api/medicamentos/", {"q": "atorva", "page": "1"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["items"][0]["nombreProducto"], "Atorva")
        service.buscar.assert_called_once_with("atorva", page=1, extra_params={})


class VademecumRelevantSearchTests(SimpleTestCase):
    def test_scans_provider_pages_and_prioritizes_commercial_name_prefix(self):
        pages = {
            1: [
                {
                    "regNo": "1",
                    "nombreProducto": "AMLOTENS",
                    "nombreDroga": "AMLODIPINA",
                    "presentacion": "10 mg",
                }
            ],
            2: [],
            3: [],
            4: [],
            5: [
                {
                    "regNo": "34959",
                    "nombreProducto": "LOTRIAL",
                    "nombreDroga": "ENALAPRIL",
                    "presentacion": "10 mg",
                }
            ],
        }

        class Client:
            def __init__(self):
                self.requested_pages = []

            def get(self, path, params):
                page = params["numeroPagina"]
                self.requested_pages.append(page)
                return {
                    "medicamentos": pages[page],
                    "pageInfo": {"numeroPagina": page, "cantidadPaginas": 5},
                }

        client = Client()
        result = VademecumService(client=client).buscar_relevante("Lot")

        self.assertEqual(client.requested_pages, [1, 2, 3, 4, 5])
        self.assertEqual(result["items"][0]["nombreProducto"], "LOTRIAL")
        self.assertEqual(result["page_info"]["paginasConsultadas"], [1, 2, 3, 4, 5])
        self.assertFalse(result["page_info"]["tieneMasResultados"])

    def test_limits_each_scan_and_exposes_the_next_provider_page(self):
        class Client:
            def get(self, path, params):
                page = params["numeroPagina"]
                return {
                    "medicamentos": [
                        {
                            "regNo": str(page),
                            "nombreProducto": f"Producto {page}",
                            "nombreDroga": "droga",
                        }
                    ],
                    "pageInfo": {"numeroPagina": page, "cantidadPaginas": 12},
                }

        result = VademecumService(client=Client()).buscar_relevante(
            "Lot",
            max_pages=2,
        )

        self.assertEqual(result["page_info"]["paginasConsultadas"], [1, 2])
        self.assertTrue(result["page_info"]["tieneMasResultados"])
        self.assertEqual(result["page_info"]["proximaPagina"], 3)

    def test_does_not_drop_drug_matches_after_the_first_forty_results(self):
        medications = [
            {
                "regNo": str(index),
                "nombreProducto": f"Marca {index:03}",
                "nombreDroga": "enalapril",
            }
            for index in range(60)
        ]
        medications.append(
            {
                "regNo": "34959",
                "nombreProducto": "LOTRIAL",
                "nombreDroga": "enalapril",
            }
        )

        class Client:
            def get(self, path, params):
                return {
                    "medicamentos": medications,
                    "pageInfo": {"numeroPagina": 1, "cantidadPaginas": 1},
                }

        result = VademecumService(client=Client()).buscar_relevante("enal")

        self.assertEqual(len(result["items"]), 61)
        self.assertIn("LOTRIAL", [item["nombreProducto"] for item in result["items"]])
        self.assertEqual(result["page_info"]["resultadosOmitidos"], 0)

    def test_prioritizes_drug_prefix_before_internal_product_match(self):
        class Client:
            def get(self, path, params):
                return {
                    "medicamentos": [
                        {
                            "regNo": "unrelated",
                            "nombreProducto": "PROAVENAL",
                            "nombreDroga": "aceite de avena",
                        },
                        {
                            "regNo": "34959",
                            "nombreProducto": "LOTRIAL",
                            "nombreDroga": "enalapril",
                        },
                    ],
                    "pageInfo": {"numeroPagina": 1, "cantidadPaginas": 1},
                }

        result = VademecumService(client=Client()).buscar_relevante("enal")

        self.assertEqual(result["items"][0]["nombreProducto"], "LOTRIAL")


class RecetasRoutingTests(TestCase):
    def test_canonical_routes_resolve_under_single_prefix(self):
        expected = {
            "/recetas/": "recetas:home",
            "/recetas/medicamentos/": "recetas:medicamentos",
            "/recetas/paciente/ingresar/": "recetas:paciente_login",
            "/recetas/paciente/salir/": "recetas:paciente_logout",
            "/recetas/paciente/recetas/nueva/": "recetas:paciente_receta_nueva",
            "/recetas/medico/solicitudes/": "recetas:medico_solicitudes",
            "/recetas/medico/recetas/nueva/": "recetas:medico_receta_nueva",
            "/recetas/api/medicamentos/": "recetas:api_medicamentos",
            "/recetas/api/paciente/perfil/actualizar/": "recetas:api_paciente_perfil_actualizar",
            "/recetas/api/catalogos/medicamentos/": "recetas:api_catalogo",
            "/recetas/api/medico/recetas/preview/": "recetas:api_receta_preview",
            "/recetas/api/medico/recetas/pacientes/": "recetas:api_receta_pacientes",
            "/recetas/api/medico/recetas/emitir/": "recetas:api_receta_emitir",
            "/recetas/api/medico/solicitudes/1/correo/": "recetas:api_medico_solicitud_correo",
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
            "/recetas/lab/receta/",
            "/recetas/api/lab/receta/emitir/",
            "/recetas/lab/rcta-espontanea/",
            "/recetas/lab/rcta-espontanea-2/",
            "/recetas/api/lab/espontanea/emitir/",
            "/recetas/api/lab/espontanea/anular/",
        ]

        for path in old_paths:
            with self.assertRaises(Resolver404):
                resolve(path)

    def test_active_pagination_style_does_not_turn_recipe_submenu_blue(self):
        stylesheet = (
            Path(__file__).resolve().parents[1] / "main" / "static" / "main" / "css" / "style.css"
        ).read_text(encoding="utf-8")

        self.assertNotIn("\n.active a {", stylesheet)
        self.assertEqual(stylesheet.count(".pagination .active a {"), 2)


class RecetaPortalViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="medico", password="test")

    def test_home_does_not_link_removed_recipe_lab(self):
        request = RequestFactory().get("/recetas/")
        request.user = self.user

        response = views.recetas_home(request)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"/recetas/lab/receta/", response.content)

    def test_pacientes_portal_requires_patient_session(self):
        response = self.client.get("/recetas/paciente/recetas/nueva/")

        self.assertRedirects(
            response,
            "/recetas/paciente/ingresar/",
            fetch_redirect_response=False,
        )

    def test_solicitudes_page_renders_empty_queue(self):
        request = RequestFactory().get("/recetas/medico/solicitudes/")
        request.user = self.user

        response = views.solicitudes_receta_page(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Cola m\xc3\xa9dica", response.content)
        self.assertIn(b"No hay solicitudes", response.content)
        self.assertIn(b'href="/recetas/medico/solicitudes/"', response.content)
        self.assertIn(b">Recetas</a>", response.content)
        self.assertIn(b">Gesti\xc3\xb3n</a>", response.content)
        self.assertIn(b'href="/recetas/medico/recetas/nueva/"', response.content)
        self.assertIn(b">Emisi\xc3\xb3n</a>", response.content)
        self.assertNotIn(b"/recetas/lab/receta/", response.content)


@override_settings(
    QBI2_PROFILE_YAML_PATH=str(
        Path(__file__).resolve().parents[1] / "private" / "qbi2" / "profile.example.yaml"
    )
)
class RecetaMedicoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="recetas", password="test")
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

    def test_page_starts_without_patient_and_keeps_two_step_flow(self):
        request = RequestFactory().get("/recetas/medico/recetas/nueva/")
        request.user = self.user

        response = views.receta_medico_page(request)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Bergonzi", response.content)
        self.assertNotIn(b"23101065", response.content)
        self.assertIn("Seleccioná un paciente".encode(), response.content)
        self.assertNotIn(b"Cambiar paciente", response.content)
        self.assertIn(b'id="patient-search-panel" class="recipe-patient-search"', response.content)
        self.assertIn(b'class="global-search-input-wrap"', response.content)
        self.assertIn(b'id="patient-search-form"', response.content)
        self.assertIn(b"autofocus", response.content)
        self.assertIn(b'id="recipe-coverage-hhcc"', response.content)
        self.assertIn(b'id="recipe-coverage-none"', response.content)
        self.assertIn(b"Sin cobertura", response.content)
        self.assertIn(b"usarCobertura: state.useCoverage", response.content)
        self.assertIn(b"Editar datos del paciente", response.content)
        self.assertIn(b"QBI2 homologaci", response.content)
        self.assertNotIn(b"Perfil de receta", response.content)
        self.assertNotIn(b"recipe-heading", response.content)
        self.assertNotIn(b"recipe-safe-badge", response.content)
        self.assertNotIn(b"<h1>Crear receta</h1>", response.content)
        self.assertIn("💊".encode(), response.content)
        self.assertIn(b"exclusivo Ezequiel", response.content)
        self.assertNotIn(b"sin mapeo QBI2", response.content)
        self.assertIn(
            b'<button id="emit-recipe" class="recipe-emit-button" type="button">Emitir en HML</button>',
            response.content,
        )
        self.assertNotIn(b"Revis\xc3\xa1 nuevamente el payload antes de emitir", response.content)
        self.assertNotIn(b"emitButton.disabled", response.content)
        self.assertIn(b"Escribir un diagn", response.content)
        self.assertIn(b"Usar texto", response.content)
        self.assertIn(b"/recetas/api/medico/recetas/pacientes/", response.content)
        self.assertIn(b"/recetas/api/medico/recetas/preview/", response.content)
        self.assertIn(b"/recetas/api/medico/recetas/emitir/", response.content)
        self.assertLess(response.content.index(b"Medicamentos"), response.content.index(b"Indicaciones"))
        self.assertLess(response.content.index(b"Indicaciones"), response.content.index(b"Otras configuraciones"))

    def test_simplified_profile_payload_comes_from_external_yaml(self):
        defaults = views._receta_defaults(self.patient)

        self.assertEqual(defaults["payload"]["medicoNombre"], "Omar")
        self.assertEqual(defaults["payload"]["medicoApellido"], "Prieto")
        self.assertEqual(defaults["payload"]["medicoMatriculaNumero"], "109347")
        self.assertEqual(defaults["payload"]["consultorioNombre"], "Cardiología Integral")

    def test_simplified_patient_search_returns_hhcc_data(self):
        response = self.client.get(
            "/recetas/api/medico/recetas/pacientes/",
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
        self.assertEqual(data["items"][0]["coverage"]["plan_id"], "")
        self.assertNotIn("mapped", data["items"][0]["coverage"])
        self.assertEqual(data["items"][0]["coverage"]["member_number"], "62333891101")

    def test_simplified_patient_refresh_by_id_returns_current_hhcc_data(self):
        response = self.client.get(
            "/recetas/api/medico/recetas/pacientes/",
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
            "/recetas/api/medico/recetas/preview/",
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

    @patch("Qbi2.views.emit_rcta_payload")
    def test_simplified_preview_never_emits_and_server_owns_patient_identity(self, emit):
        response = self.client.post(
            "/recetas/api/medico/recetas/preview/",
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
        self.assertEqual(data["payload"]["paciente"]["cobertura"]["numero"], "62333891101")
        self.assertNotIn("idFinanciador", data["payload"]["paciente"]["cobertura"])
        self.assertNotIn("planId", data["payload"]["paciente"]["cobertura"])
        self.assertEqual(data["payload"]["paciente"]["cobertura"]["plan"], "310")
        self.assertEqual(len(data["payload"]["medicamentos"]), 2)
        self.assertNotIn("diagnostico", data["payload"]["medicamentos"][0])
        self.assertNotIn("codigoDiagnostico", data["payload"]["medicamentos"][0])
        self.assertFalse(data["payload"]["medicamentos"][0]["forzarDuplicado"])
        self.assertEqual(data["payload"]["diagnostico"], "I10")
        self.assertNotIn("fechaNacimiento", data["payload"]["medico"])
        self.assertNotIn("idTributario", data["payload"]["medico"])
        emit.assert_not_called()

    @patch("Qbi2.views.emit_rcta_payload")
    def test_simplified_preview_can_omit_patient_coverage(self, emit):
        response = self.client.post(
            "/recetas/api/medico/recetas/preview/",
            data=json.dumps(
                {
                    "pacienteId": self.patient.id,
                    "usarCobertura": False,
                    "diagnostico": "Hipertension arterial",
                    "codigoDiagnostico": "I10",
                    "medicamentos": [{"regNo": "34959", "nombreProducto": "LOTRIAL"}],
                }
            ),
            content_type="application/json",
        )

        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("cobertura", data["payload"]["paciente"])
        emit.assert_not_called()

    @patch("Qbi2.views.emit_rcta_payload")
    def test_simplified_emit_uses_server_owned_patient_identity(self, emit):
        emit.return_value = RctaResult(
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
            "/recetas/api/medico/recetas/emitir/",
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
        (safe_data,) = emit.call_args.args
        self.assertEqual(safe_data["pacienteNombre"], "Ezequiel")
        self.assertEqual(safe_data["pacienteApellido"], "Bergonzi")
        self.assertEqual(safe_data["pacienteNroDoc"], "23101065")

    def test_simplified_preview_requires_diagnosis_and_medicine(self):
        no_diagnosis = self.client.post(
            "/recetas/api/medico/recetas/preview/",
            data=json.dumps({"pacienteId": self.patient.id, "medicamentos": []}),
            content_type="application/json",
        )
        no_medicine = self.client.post(
            "/recetas/api/medico/recetas/preview/",
            data=json.dumps({"pacienteId": self.patient.id, "diagnostico": "Control cardiologico", "medicamentos": []}),
            content_type="application/json",
        )

        self.assertEqual(no_diagnosis.status_code, 400)
        self.assertEqual(no_medicine.status_code, 400)
        self.assertIn("diagnóstico es obligatorio", no_diagnosis.json()["message"])
        self.assertIn("al menos un medicamento", no_medicine.json()["message"])

    @patch("Qbi2.views.emit_rcta_payload")
    def test_simplified_preview_accepts_free_text_diagnosis_without_catalog_code(self, emit):
        response = self.client.post(
            "/recetas/api/medico/recetas/preview/",
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
            "/recetas/api/medico/recetas/preview/",
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

    @patch("Qbi2.views.emit_rcta_payload")
    def test_simplified_emit_preserves_direct_provider_error(self, emit):
        emit.side_effect = Qbi2HTTPError(
            "QBI2 devolvio un error HTTP.",
            status_code=400,
            payload={"error": "QBI184", "mensaje": "EL NÚMERO DE AFILIADO INGRESADO ES INVÁLIDO"},
        )

        response = self.client.post(
            "/recetas/api/medico/recetas/emitir/",
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
        endpoint, payload = build_rcta_payload(
            {
                "medicamentos": [
                    {
                        "regNo": "34959",
                        "nombreProducto": "LOTRIAL",
                        "nombreDroga": "enalapril",
                        "presentacion": "10 mg comp.x 30",
                        "cantidad": "2",
                    }
                ],
                "diagnostico": "Hipertension arterial",
                "codigoDiagnostico": "I10",
            }
        )

        self.assertEqual(endpoint, "/apirecipe/Receta")
        self.assertEqual(payload["medicamentos"][0]["regNo"], "34959")
        self.assertEqual(payload["medicamentos"][0]["codigoDiagnostico"], "I10")

    def test_summary_extracts_recipe_identifiers(self):
        summary = summarize_receta_response(
            {
                "recetas": [
                    {"id": "hash-receta", "idReceta": "R-100", "verificador": "https://example.invalid/verificar"}
                ],
                "response": [{"status": "OK"}],
            }
        )

        self.assertEqual(summary["id"], "hash-receta")
        self.assertEqual(summary["idReceta"], "R-100")


class PacientesPortalTests(TestCase):
    def setUp(self):
        tipo_doc = TipoDocumento.objects.create(nombre="DNI", descripcion="Documento")
        self.paciente = Paciente.objects.create(
            idTipoDoc=tipo_doc,
            numDoc="12345678",
            nombre="Ana",
            apellido="De la Fuente",
            sexo="M",
            obraSocial="OSDE",
            afiliado="ORIGINAL-1",
        )

    def login_patient(self, apellido="De la Fuente"):
        return self.client.post(
            "/recetas/paciente/ingresar/",
            {"documento": "12.345.678", "apellido": apellido},
        )

    def test_normalizes_document(self):
        self.assertEqual(normalize_document("12.345.678"), "12345678")

    def test_login_requires_complete_compound_surname(self):
        paciente, _ = find_patient_history(apellido="Fuente", documento="12.345.678")
        self.assertIsNone(paciente)

        response = self.login_patient(apellido="  DE   LA fuente ")
        self.assertRedirects(
            response,
            "/recetas/paciente/recetas/nueva/",
            fetch_redirect_response=False,
        )

    def test_authenticated_page_only_exposes_non_clinical_patient_fields(self):
        self.login_patient()
        request = RequestFactory().get("/recetas/paciente/recetas/nueva/")
        request.session = self.client.session
        response = views.pacientes_portal_page(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Portal de pacientes")
        self.assertContains(response, "name=\"sexo\"")
        self.assertContains(response, "name=\"direccion\"")
        self.assertContains(response, "name=\"telefono\"")
        self.assertContains(response, "name=\"celular\"")
        self.assertContains(response, "name=\"mail\"")
        self.assertContains(response, "name=\"obraSocial\"")
        self.assertContains(response, "name=\"afiliado\"")
        self.assertContains(
            response,
            "Solicitar medicación. Mantener actualizados los datos, o las recetas no podrán emitirse",
        )
        self.assertContains(
            response,
            "El Dr. Omar Prieto revisará el pedido antes de decidir.",
        )
        self.assertNotContains(response, "Tu identidad y cobertura son datos de sólo lectura.")
        self.assertNotContains(
            response,
            "Desde este portal sólo se pueden modificar sexo, dirección, teléfonos y correo.",
        )
        self.assertNotContains(response, "name=\"diagnostico\"")
        self.assertNotContains(response, "QBI2 PoC")
        self.assertNotContains(response, ">Gestión</a>")
        self.assertNotContains(response, ">Emisión</a>")

    def test_profile_update_changes_coverage_but_ignores_identity_and_plan(self):
        self.login_patient()
        response = self.client.post(
            "/recetas/api/paciente/perfil/actualizar/",
            {
                "sexo": "H",
                "direccion": "Calle Nueva 123",
                "telefono": "1111-2222",
                "celular": "15-3333-4444",
                "mail": "ana@example.com",
                "nombre": "Nombre alterado",
                "apellido": "Apellido alterado",
                "numDoc": "99999999",
                "obraSocial": "Cobertura alterada",
                "afiliado": "ALTERADO",
                "plan": "Plan alterado",
            },
        )
        self.paciente.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.paciente.sexo, "H")
        self.assertEqual(self.paciente.direccion, "Calle Nueva 123")
        self.assertEqual(self.paciente.telefono, "1111-2222")
        self.assertEqual(self.paciente.celular, "15-3333-4444")
        self.assertEqual(self.paciente.mail, "ana@example.com")
        self.assertEqual(self.paciente.nombre, "Ana")
        self.assertEqual(self.paciente.apellido, "De la Fuente")
        self.assertEqual(self.paciente.numDoc, "12345678")
        self.assertEqual(self.paciente.obraSocial, "Cobertura alterada")
        self.assertEqual(self.paciente.afiliado, "ALTERADO")
        self.assertIsNone(self.paciente.plan)

    @patch("Qbi2.views.VademecumService")
    def test_patient_medication_search_uses_relevant_multi_page_scan(self, service_class):
        service_class.return_value.buscar_relevante.return_value = {
            "query": "Lot",
            "page": 1,
            "items": [{"regNo": "34959", "nombreProducto": "LOTRIAL"}],
            "page_info": {
                "numeroPagina": 1,
                "cantidadPaginas": 9,
                "paginasConsultadas": list(range(1, 10)),
                "tieneMasResultados": False,
                "proximaPagina": None,
            },
        }
        self.login_patient()

        response = self.client.get(
            "/recetas/api/paciente/medicamentos/directo/",
            {"q": "Lot", "scanPage": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"][0]["nombreProducto"], "LOTRIAL")
        service_class.return_value.buscar_relevante.assert_called_once_with(
            "Lot",
            start_page=1,
            extra_params={},
        )

    def test_patient_apis_require_patient_session(self):
        response = self.client.post(
            "/recetas/api/paciente/validar-y-solicitar/",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_rejects_when_patient_has_no_history(self):
        self.paciente.historias_clinicas.all().delete()
        self.login_patient()
        response = self.client.post(
            "/recetas/api/paciente/validar-y-solicitar/",
            data=json.dumps({"medicamentosJson": "[]"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404, response.content)
        self.assertEqual(response.json()["message"], "No tenes Historia Clinica")

    def test_accepts_patient_request_as_one_order_with_up_to_ten_medications(self):
        HistoriaClinica.objects.create(paciente=self.paciente)
        self.login_patient()
        selected_medications = [
            {"regNo": str(34959 + index), "nombreProducto": f"MEDICAMENTO {index + 1}"}
            for index in range(10)
        ]
        response = self.client.post(
            "/recetas/api/paciente/validar-y-solicitar/",
            data=json.dumps(
                {
                    "medicamentosJson": json.dumps(selected_medications),
                }
            ),
            content_type="application/json",
        )

        data = response.json()
        solicitudes = list(SolicitudReceta.objects.order_by("id"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["solicitudes"]), 1)
        self.assertEqual(len(solicitudes), 1)
        self.assertEqual(len(solicitudes[0].auditoria["medicamentos"]), 10)
        self.assertNotIn("receta_orden", solicitudes[0].auditoria)
        self.assertEqual(solicitudes[0].medicamento_reg_no, "34959")
        self.assertEqual(solicitudes[0].diagnostico, "")


@override_settings(
    QBI2_PROFILE_YAML_PATH=str(
        Path(__file__).resolve().parents[1] / "private" / "qbi2" / "profile.example.yaml"
    )
)
class SolicitudRecetaQueueTests(TestCase):
    def setUp(self):
        tipo_doc = TipoDocumento.objects.create(nombre="DNI", descripcion="Documento")
        self.paciente = Paciente.objects.create(
            idTipoDoc=tipo_doc,
            numDoc="12345678",
            nombre="Ana",
            apellido="Perez",
            sexo="M",
            fechaNac=date(1980, 1, 2),
            mail="ana@example.com",
            celular="1155554444",
            direccion="Calle Nueva 123",
            localidad="Monte Grande",
            obraSocial="OSDE",
            plan="310",
            afiliado="23200126801",
        )
        self.historia = HistoriaClinica.objects.create(paciente=self.paciente)
        self.user = get_user_model().objects.create_user(username="omar", password="test")

    @patch("Qbi2.views.VademecumService")
    def test_medical_catalog_uses_same_relevant_scan_as_patient_portal(self, service_class):
        service_class.return_value.buscar_relevante.return_value = {
            "items": [{"regNo": "34959", "nombreProducto": "LOTRIAL"}],
            "page_info": {"tieneMasResultados": True, "proximaPagina": 8},
        }
        self.client.force_login(self.user)

        response = self.client.get(
            "/recetas/api/catalogos/medicamentos/",
            {"q": "enal", "scanPage": "7"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"][0]["nombreProducto"], "LOTRIAL")
        service_class.return_value.buscar_relevante.assert_called_once_with(
            "enal",
            start_page=7,
            extra_params={},
        )

    def test_pending_queue_matches_medical_editor_and_links_canonical_patient_edit(self):
        solicitud = SolicitudReceta.objects.create(
            paciente=self.paciente,
            historia_clinica=self.historia,
            medicamento_reg_no="34959",
            medicamento_nombre_producto="LOTRIAL",
            medicamento_nombre_droga="enalapril",
        )
        request = RequestFactory().get("/recetas/medico/solicitudes/")
        request.user = self.user
        response = views.solicitudes_receta_page(request)

        self.assertContains(response, "Editar datos del paciente")
        self.assertContains(
            response,
            f'/pacientes/{self.paciente.id}/editar/?recipe_context=1',
        )
        self.assertContains(response, "Buscar por nombre comercial o droga")
        self.assertContains(response, "Hasta 10 por pedido")
        self.assertContains(response, "Preparar correo con PDF", count=0)
        self.assertContains(response, "product === needle")
        self.assertContains(response, "product.startsWith(needle)")
        self.assertContains(response, "drug === needle")
        self.assertContains(response, "drug.startsWith(needle)")
        self.assertContains(response, "product.includes(needle)")
        self.assertContains(response, "drug.includes(needle)")
        self.assertContains(response, "hhcc:patient-updated")
        self.assertContains(response, "scanPage")

    def test_reject_pending_request(self):
        solicitud = SolicitudReceta.objects.create(
            paciente=self.paciente,
            historia_clinica=self.historia,
            medicamento_reg_no="34959",
            medicamento_nombre_producto="LOTRIAL",
        )
        self.client.force_login(self.user)

        response = self.client.post(
            f"/recetas/api/medico/solicitudes/{solicitud.id}/rechazar/",
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

        def fake_emit(recipe_data):
            endpoint, payload = build_rcta_payload(recipe_data)
            provider_response = {
                "recetas": [
                    {"idReceta": "9600000255038", "s3Link": "https://example.invalid/receta.pdf"}
                ],
                "errores": [],
                "response": [{"status": "OK"}],
            }
            return RctaResult(
                operation="receta",
                endpoint=endpoint,
                payload=payload,
                response=provider_response,
                summary=summarize_receta_response(provider_response),
            )

        with patch("Qbi2.views.emit_rcta_payload", side_effect=fake_emit):
            response = self.client.post(
                f"/recetas/api/medico/solicitudes/{solicitud.id}/aprobar/",
                {
                    "diagnostico": "Hipertension arterial",
                    "posologia": "Tomar segun indicacion medica.",
                    "observacion_medico": "Autorizada",
                    "next": "/recetas/medico/solicitudes/?estado=pendiente",
                    "medicamentosJson": json.dumps(
                        [
                            {
                                "regNo": "24818",
                                "nombreProducto": "AMPLIAR",
                                "nombreDroga": "droga editada",
                                "presentacion": "20 comprimidos",
                            }
                        ]
                    ),
                },
            )
        solicitud.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            f"/recetas/medico/solicitudes/?estado=pendiente&resultado={solicitud.id}#resultado-emision",
        )
        self.assertEqual(solicitud.estado, SolicitudReceta.Estado.EMITIDA)
        self.assertEqual(solicitud.qbi2_pdf_url, "https://example.invalid/receta.pdf")
        self.assertEqual(solicitud.emisiones.count(), 1)
        self.assertEqual(
            solicitud.emisiones.get().estado,
            EmisionSolicitudReceta.Estado.EMITIDA,
        )
        self.assertEqual(solicitud.diagnostico, "Hipertension arterial")
        self.assertEqual(solicitud.medicamento_reg_no, "24818")
        self.assertEqual(solicitud.auditoria["medicamentos"][0]["nombreProducto"], "AMPLIAR")
        self.assertTrue(solicitud.auditoria["medicamentos_editados_por_medico"])
        self.assertEqual(solicitud.payload_qbi2["paciente"]["cobertura"]["numero"], "23200126801")
        self.assertEqual(solicitud.payload_qbi2["paciente"]["cobertura"]["plan"], "310")
        self.assertNotIn("idFinanciador", solicitud.payload_qbi2["paciente"]["cobertura"])
        self.assertEqual(solicitud.payload_qbi2["medico"]["matricula"]["tipo"], "MN")
        self.assertEqual(solicitud.payload_qbi2["medico"]["matricula"]["numero"], "109347")
        self.assertIn("MP 332792", solicitud.payload_qbi2["medico"]["sello"]["linea3"])
        self.assertTrue(solicitud.payload_qbi2["medico"]["firmabase64"])
        self.assertTrue(solicitud.payload_qbi2["medico"]["logoInstitucion"])
        self.assertEqual(
            solicitud.payload_qbi2["lugarAtencion"]["nombreConsultorio"],
            "Cardiología Integral",
        )

        feedback = self.client.get(response.url.split("#", 1)[0])
        self.assertContains(feedback, "emission-feedback success")
        self.assertContains(
            feedback,
            f"La solicitud #{solicitud.id} fue emitida correctamente",
        )
        self.assertContains(feedback, "Ver PDF 1 de 1")
        self.assertContains(feedback, "Preparar correo con todos los PDF")
        self.assertContains(feedback, 'href="?estado=pendiente"')
        self.assertNotContains(feedback, 'class="request-card"')

    def test_approval_sends_complete_patient_order_in_one_rcta_payload(self):
        medicamentos = [
            {
                "regNo": str(1000 + index),
                "nombreProducto": f"MEDICAMENTO {index}",
                "nombreDroga": f"droga {index}",
            }
            for index in range(1, 11)
        ]
        solicitud = SolicitudReceta.objects.create(
            paciente=self.paciente,
            historia_clinica=self.historia,
            medicamento_reg_no=medicamentos[0]["regNo"],
            medicamento_nombre_producto=medicamentos[0]["nombreProducto"],
            auditoria={"medicamentos": medicamentos},
        )
        self.client.force_login(self.user)

        groups = [medicamentos[0:3], medicamentos[3:6], medicamentos[6:9], medicamentos[9:10]]
        provider_response = {
            "recetas": [
                {
                    "idReceta": f"RECETA-{index}",
                    "s3Link": f"https://example.invalid/receta-{index}.pdf",
                }
                for index in range(1, 5)
            ],
            "errores": [],
            "response": [
                {"status": "OK", "medicamentos": group}
                for group in groups
            ],
        }
        result = RctaResult(
            operation="receta",
            endpoint="/apirecipe/Receta",
            payload={"medicamentos": medicamentos},
            response=provider_response,
            summary=summarize_receta_response(provider_response),
        )
        with patch("Qbi2.views.emit_rcta_payload", return_value=result) as emit:
            response = self.client.post(
                f"/recetas/api/medico/solicitudes/{solicitud.id}/aprobar/",
                {
                    "diagnostico": "Hipertensión arterial",
                    "next": "/recetas/medico/solicitudes/?estado=pendiente",
                    "medicamentosJson": json.dumps(medicamentos),
                },
            )

        solicitud.refresh_from_db()
        emisiones = list(solicitud.emisiones.all())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(solicitud.estado, SolicitudReceta.Estado.EMITIDA)
        self.assertEqual(emit.call_count, 1)
        self.assertEqual(len(emisiones), 4)
        self.assertEqual(
            [len(item.medicamentos) for item in emisiones],
            [3, 3, 3, 1],
        )
        self.assertEqual(
            [item.qbi2_id_receta for item in emisiones],
            ["RECETA-1", "RECETA-2", "RECETA-3", "RECETA-4"],
        )
        self.assertEqual(len(emit.call_args.args[0]["medicamentos"]), 10)

    def test_complete_order_preserves_provider_error_without_splitting(self):
        medicamentos = [
            {"regNo": str(2000 + index), "nombreProducto": f"MED {index}"}
            for index in range(5)
        ]
        solicitud = SolicitudReceta.objects.create(
            paciente=self.paciente,
            historia_clinica=self.historia,
            medicamento_reg_no=medicamentos[0]["regNo"],
            auditoria={"medicamentos": medicamentos},
        )
        self.client.force_login(self.user)
        provider_error = Qbi2HTTPError(
            "QBI2 rechazó la receta.",
            status_code=400,
            payload={"mensaje": "Medicamento inválido"},
        )

        with patch("Qbi2.views.emit_rcta_payload", side_effect=provider_error) as emit:
            response = self.client.post(
                f"/recetas/api/medico/solicitudes/{solicitud.id}/aprobar/",
                {
                    "diagnostico": "Hipertensión arterial",
                    "medicamentosJson": json.dumps(medicamentos),
                },
            )

        solicitud.refresh_from_db()
        emisiones = list(solicitud.emisiones.all())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(solicitud.estado, SolicitudReceta.Estado.ERROR_EMISION)
        self.assertEqual(emit.call_count, 1)
        self.assertEqual(len(emisiones), 1)
        self.assertEqual(emisiones[0].estado, EmisionSolicitudReceta.Estado.ERROR)
        self.assertEqual(
            [item["regNo"] for item in emisiones[0].medicamentos],
            [item["regNo"] for item in medicamentos],
        )
        self.assertEqual(solicitud.error_qbi2, "QBI2 rechazó la receta.")
        self.assertEqual(
            response.url,
            f"/recetas/medico/solicitudes/?estado=pendiente&resultado={solicitud.id}#resultado-emision",
        )
        feedback = self.client.get(response.url.split("#", 1)[0])
        self.assertContains(feedback, "emission-feedback error")
        self.assertContains(feedback, f"No se pudo emitir la solicitud #{solicitud.id}")
        self.assertContains(feedback, "QBI2 rechazó la receta.")

    @patch("Qbi2.views.download_prescription_pdf", return_value=b"%PDF-1.7\nmock")
    def test_emitted_request_downloads_unsent_email_with_pdf_attached(self, download_pdf):
        solicitud = SolicitudReceta.objects.create(
            paciente=self.paciente,
            historia_clinica=self.historia,
            medicamento_reg_no="34959",
            medicamento_nombre_producto="LOTRIAL",
            estado=SolicitudReceta.Estado.EMITIDA,
            qbi2_id_receta="9600000255038",
            qbi2_pdf_url="https://example.invalid/receta.pdf",
        )
        self.client.force_login(self.user)

        response = self.client.get(
            f"/recetas/api/medico/solicitudes/{solicitud.id}/correo/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "message/rfc822")
        self.assertIn("receta-9600000255038.eml", response["Content-Disposition"])
        message = BytesParser(policy=policy.default).parsebytes(response.content)
        self.assertEqual(message["To"], "ana@example.com")
        self.assertEqual(message["Subject"], PRESCRIPTION_EMAIL_SUBJECT)
        self.assertEqual(message["X-Unsent"], "1")
        self.assertEqual(
            message.get_body(preferencelist=("plain",)).get_content().replace("\r\n", "\n"),
            PRESCRIPTION_EMAIL_BODY,
        )
        attachments = list(message.iter_attachments())
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].get_filename(), "receta-9600000255038.pdf")
        self.assertEqual(attachments[0].get_content(), b"%PDF-1.7\nmock")
        download_pdf.assert_called_once_with("https://example.invalid/receta.pdf")

    @patch("Qbi2.views.download_prescription_pdf")
    def test_email_draft_attaches_every_available_emission_pdf(self, download_pdf):
        download_pdf.side_effect = [b"%PDF-1.7\none", b"%PDF-1.7\ntwo"]
        solicitud = SolicitudReceta.objects.create(
            paciente=self.paciente,
            historia_clinica=self.historia,
            medicamento_reg_no="34959",
            estado=SolicitudReceta.Estado.EMITIDA,
        )
        for order in (1, 2):
            EmisionSolicitudReceta.objects.create(
                solicitud=solicitud,
                orden=order,
                total=2,
                medicamentos=[{"regNo": str(order)}],
                estado=EmisionSolicitudReceta.Estado.EMITIDA,
                qbi2_id_receta=f"RECETA-{order}",
                qbi2_pdf_url=f"https://example.invalid/receta-{order}.pdf",
            )
        self.client.force_login(self.user)

        response = self.client.get(
            f"/recetas/api/medico/solicitudes/{solicitud.id}/correo/"
        )

        message = BytesParser(policy=policy.default).parsebytes(response.content)
        attachments = list(message.iter_attachments())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(attachments), 2)
        self.assertEqual(
            [attachment.get_filename() for attachment in attachments],
            ["receta-1-RECETA-1.pdf", "receta-2-RECETA-2.pdf"],
        )
        self.assertEqual(download_pdf.call_count, 2)

    @patch("Qbi2.views.download_prescription_pdf")
    def test_email_draft_is_not_available_until_rcta_marks_request_emitted(self, download_pdf):
        solicitud = SolicitudReceta.objects.create(
            paciente=self.paciente,
            historia_clinica=self.historia,
            medicamento_reg_no="34959",
            estado=SolicitudReceta.Estado.PENDIENTE,
            qbi2_pdf_url="https://example.invalid/receta.pdf",
        )
        request = RequestFactory().get(
            f"/recetas/api/medico/solicitudes/{solicitud.id}/correo/"
        )
        request.user = self.user

        with self.assertRaises(Http404):
            views.preparar_correo_receta(request, solicitud.id)
        download_pdf.assert_not_called()

    def test_emitted_queue_shows_notification_button(self):
        solicitud = SolicitudReceta.objects.create(
            paciente=self.paciente,
            historia_clinica=self.historia,
            medicamento_reg_no="34959",
            estado=SolicitudReceta.Estado.EMITIDA,
            qbi2_pdf_url="https://example.invalid/receta.pdf",
        )
        request = RequestFactory().get("/recetas/medico/solicitudes/?estado=emitida")
        request.user = self.user
        response = views.solicitudes_receta_page(request)

        self.assertContains(response, "Preparar correo con todos los PDF")
        self.assertContains(
            response,
            f"/recetas/api/medico/solicitudes/{solicitud.id}/correo/",
        )


class PrescriptionNotificationSecurityTests(SimpleTestCase):
    def test_pdf_download_rejects_non_https_links(self):
        with self.assertRaises(PrescriptionNotificationError):
            download_prescription_pdf("http://example.invalid/receta.pdf")
