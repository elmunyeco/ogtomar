import json
from datetime import timedelta
from typing import Any
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import resolve, Resolver404
from django.utils import timezone

from Qbi2 import views
from Qbi2.cache import MySQLCache, hash_key
from Qbi2.models import Qbi2CacheEntry, SolicitudReceta
from Qbi2.portal import normalize_document
from Qbi2.recipes import RecetaPocResult
from Qbi2.vademecum_cache import CachedVademecumService, VademecumCachePolicy
from main.models import HistoriaClinica, Paciente, TipoDocumento


class FakeVademecumService:
    def __init__(self):
        self.calls: list[tuple[str, int, dict[str, Any]]] = []
        self.responses: list[Any] = []
        self.by_regno: dict[str, dict[str, Any]] = {}
        self.fail = False

    def buscar(self, query: str, page: int = 1, extra_params: dict[str, Any] | None = None):
        self.calls.append((query, page, extra_params or {}))
        if self.fail:
            raise RuntimeError("qbi2 caido")
        if self.responses:
            return self.responses.pop(0)
        return {"items": []}

    def obtener_por_regno(self, reg_no: str):
        if self.fail:
            raise RuntimeError("qbi2 caido")
        return self.by_regno.get(reg_no, {})


class MySQLCacheTests(TestCase):
    def test_set_get_persists_in_mysql(self):
        cache = MySQLCache()

        cache.set(
            "qbi2:vademecum:test",
            {"items": [{"regNo": "1"}]},
            timedelta(days=15),
            stale_ttl=timedelta(days=75),
            metadata={"normalized_query": "at", "page": 1},
        )

        self.assertEqual(Qbi2CacheEntry.objects.count(), 1)
        result = MySQLCache().get("qbi2:vademecum:test")

        self.assertTrue(result.hit)
        self.assertFalse(result.stale)
        self.assertEqual(result.value, {"items": [{"regNo": "1"}]})

    def test_defensive_copy_on_get(self):
        cache = MySQLCache()
        cache.set(
            "copy:test",
            {"items": [{"nombreProducto": "A"}]},
            timedelta(days=15),
            stale_ttl=timedelta(days=75),
        )

        result = cache.get("copy:test")
        result.value["items"][0]["nombreProducto"] = "mutado"

        again = cache.get("copy:test")
        self.assertEqual(again.value["items"][0]["nombreProducto"], "A")

    def test_stale_and_lease_are_per_key(self):
        cache = MySQLCache()
        cache.set("a", {"value": 1}, timedelta(days=15), stale_ttl=timedelta(days=75))
        entry = Qbi2CacheEntry.objects.get(key_hash=hash_key("a"))
        entry.fresh_until = timezone.now() - timedelta(seconds=1)
        entry.stale_until = timezone.now() + timedelta(days=1)
        entry.save(update_fields=["fresh_until", "stale_until"])

        stale = cache.get("a", allow_stale=True)
        lease_a = cache.try_acquire_refresh_lease("a")
        lease_a_again = cache.try_acquire_refresh_lease("a")
        lease_b = cache.try_acquire_refresh_lease("b")

        self.assertTrue(stale.hit)
        self.assertTrue(stale.stale)
        self.assertTrue(lease_a.acquired)
        self.assertFalse(lease_a_again.acquired)
        self.assertTrue(lease_b.acquired)


class CachedVademecumServiceTests(TestCase):
    def build_service(self, live: FakeVademecumService | None = None):
        policy = VademecumCachePolicy(
            fresh_ttl=timedelta(days=15),
            stale_ttl=timedelta(days=75),
            lease_ttl=timedelta(seconds=45),
        )
        return CachedVademecumService(
            live or FakeVademecumService(),
            policy=policy,
            cliente_app_id=563,
            base_url="https://apirecipe.hml.qbitos.com",
        )

    def test_autocomplete_from_two_letters_is_cached_by_prefix(self):
        live = FakeVademecumService()
        live.responses.extend(
            [
                {"items": [{"regNo": "1", "nombreProducto": "Atorva"}]},
                {"items": [{"regNo": "1", "nombreProducto": "Atorva"}]},
            ]
        )
        service = self.build_service(live)

        self.assertEqual(service.buscar("a"), [])
        service.buscar("at")
        service.buscar("ato")
        service.buscar(" at ")

        self.assertEqual([call[0] for call in live.calls], ["at", "ato"])
        self.assertEqual(Qbi2CacheEntry.objects.count(), 2)

    def test_stale_refreshes_only_requested_key(self):
        live = FakeVademecumService()
        live.responses.extend(
            [
                {"items": [{"regNo": "1"}]},
                {"items": [{"regNo": "2"}]},
                {"items": [{"regNo": "3"}]},
            ]
        )
        service = self.build_service(live)

        service.buscar("at")
        service.buscar("bi")

        for entry in Qbi2CacheEntry.objects.all():
            entry.fresh_until = timezone.now() - timedelta(seconds=1)
            entry.stale_until = timezone.now() + timedelta(days=1)
            entry.save(update_fields=["fresh_until", "stale_until"])

        service.buscar("at")

        self.assertEqual(len(live.calls), 3)
        self.assertEqual(live.calls[-1][0], "at")

    def test_stale_provider_error_records_error_and_returns_stale(self):
        live = FakeVademecumService()
        live.responses.append({"items": [{"regNo": "1"}]})
        service = self.build_service(live)

        service.buscar("at")
        entry = Qbi2CacheEntry.objects.get()
        entry.fresh_until = timezone.now() - timedelta(seconds=1)
        entry.stale_until = timezone.now() + timedelta(days=1)
        entry.save(update_fields=["fresh_until", "stale_until"])
        live.fail = True

        result = service.buscar("at", include_cache_metadata=True)
        entry.refresh_from_db()

        self.assertTrue(result["cache"]["stale"])
        self.assertEqual(result["cache"]["refresh"], "provider_error")
        self.assertIn("qbi2 caido", entry.last_refresh_error)

    def test_validation_uses_live_service_not_cache(self):
        live = FakeVademecumService()
        live.by_regno["123"] = {
            "regNo": "123",
            "nombreProducto": "Atorva",
            "presentacion": "20 mg x 30",
        }
        service = self.build_service(live)

        result = service.validar_medicamento_seleccionado(
            {
                "regNo": "123",
                "nombreProducto": "Atorva",
                "presentacion": "10 mg x 30",
            }
        )

        self.assertFalse(result.valid)
        self.assertEqual(result.status, "changed")


class VademecumDemoViewTests(TestCase):
    def test_search_api_short_query_does_not_call_provider(self):
        response = self.client.get("/qbi2-poc/api/medicamentos/cache/", {"q": "a"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["cache"]["status"], "too_short")
        self.assertEqual(payload["data"], [])

    def test_recent_cache_api_returns_rows(self):
        MySQLCache().set(
            "recent:test",
            {"items": [{"regNo": "1"}]},
            timedelta(days=15),
            stale_ttl=timedelta(days=75),
            metadata={"namespace": "vademecum", "normalized_query": "recent", "page": 1},
        )

        response = self.client.get("/qbi2-poc/api/cache/recientes/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["rows"][0]["query"], "recent")


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
            "/qbi2-poc/medicamentos/cache/": "qbi2_poc:medicamentos_cache",
            "/qbi2-poc/paciente/recetas/nueva/": "qbi2_poc:paciente_receta_nueva",
            "/qbi2-poc/medico/solicitudes/": "qbi2_poc:medico_solicitudes",
            "/qbi2-poc/lab/receta/": "qbi2_poc:lab_receta",
            "/qbi2-poc/api/medicamentos/directo/": "qbi2_poc:api_medicamentos_directo",
            "/qbi2-poc/api/medicamentos/cache/": "qbi2_poc:api_medicamentos_cache",
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
