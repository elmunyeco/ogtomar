from datetime import date, datetime, time, timedelta
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from main.models import HistoriaClinica, Paciente, TipoDocumento
from .history_filters import history_range
from .models import EmisionSolicitudReceta, SolicitudReceta
from .views import _solicitudes_result_url


class CalendarRangeTests(SimpleTestCase):
    def test_calendar_months_and_leap_year(self):
        cases = [
            (date(2024, 3, 31), "mes", date(2024, 2, 29)),
            (date(2024, 2, 29), "anio", date(2023, 2, 28)),
            (date(2026, 10, 9), "seis_meses", date(2026, 4, 9)),
            (date(2026, 10, 9), "semana", date(2026, 10, 3)),
        ]
        for today, period, expected in cases:
            with self.subTest(today=today, period=period):
                selection = history_range({"periodo": period}, today)
                self.assertEqual(selection["start"], expected)
                self.assertEqual(selection["end"], today)

    def test_invalid_ranges_do_not_fall_back_to_all_records(self):
        for start, end in [("", ""), ("2026-10-10", "2026-10-09"), ("bad", "2026-10-09"), ("2026-10-09", "9999-12-31")]:
            with self.subTest(start=start, end=end):
                self.assertTrue(history_range({"modo": "fechas", "desde": start, "hasta": end})["error"])

    def test_feedback_return_keeps_filters_and_cannot_redirect_elsewhere(self):
        result = _solicitudes_result_url(
            "https://example.org/?estado=emitida&modo=fechas&desde=2026-10-01&hasta=2026-10-09&pagina=2", 7,
        )
        parsed = urlsplit(result)
        self.assertEqual(parsed.path, "/recetas/medico/solicitudes/")
        self.assertEqual(parsed.netloc, "")
        self.assertEqual(parse_qs(parsed.query)["desde"], ["2026-10-01"])
        self.assertEqual(parse_qs(parsed.query)["pagina"], ["2"])
        self.assertEqual(parse_qs(parsed.query)["resultado"], ["7"])
        self.assertEqual(parsed.fragment, "resultado-emision")


@override_settings(ALLOWED_HOSTS=["testserver"])
class HistoryViewTests(TestCase):
    def setUp(self):
        tipo = TipoDocumento.objects.create(nombre="DNI", descripcion="Documento")
        self.patient = Paciente.objects.create(idTipoDoc=tipo, numDoc="12345678", nombre="Prueba", apellido="Historial")
        self.history = HistoriaClinica.objects.create(paciente=self.patient)
        self.client.force_login(get_user_model().objects.create_user(username="doctor", password="test"))
        self.day = date(2026, 10, 9)
        self.start = timezone.make_aware(datetime.combine(self.day, time.min))
        self.params = {"modo": "fechas", "desde": self.day.isoformat(), "hasta": self.day.isoformat(), "estado": "todas"}

    def create_request(self, timestamp, state="pendiente"):
        item = SolicitudReceta.objects.create(paciente=self.patient, historia_clinica=self.history, medicamento_reg_no="test", estado=state)
        SolicitudReceta.objects.filter(pk=item.pk).update(created_at=timestamp)
        return item

    def test_inclusive_local_dates_exclude_adjacent_days(self):
        self.create_request(self.start - timedelta(microseconds=1))
        first = self.create_request(self.start)
        last = self.create_request(self.start + timedelta(days=1, microseconds=-1), "emitida")
        self.create_request(self.start + timedelta(days=1))
        response = self.client.get("/recetas/medico/solicitudes/", self.params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual({item.pk for item in response.context["solicitudes"]}, {first.pk, last.pk})
        self.assertEqual(response.context["pending_count"], 1)
        self.assertEqual(response.context["pending_outside"], 2)
        self.assertContains(response, "Ver todos los pendientes")
        response = self.client.get("/recetas/medico/solicitudes/", {**self.params, "estado": "emitida"})
        self.assertEqual([item.pk for item in response.context["solicitudes"]], [last.pk])

    def test_invalid_dates_show_error_and_no_records(self):
        self.create_request(self.start)
        response = self.client.get("/recetas/medico/solicitudes/", {**self.params, "desde": "bad"})
        self.assertEqual(response.context["solicitudes"], [])
        self.assertContains(response, "Ingresar fechas válidas")

    def test_pagination_keeps_filters_and_does_not_truncate_results(self):
        for _ in range(21):
            self.create_request(self.start)
        first = self.client.get("/recetas/medico/solicitudes/", self.params)
        second = self.client.get("/recetas/medico/solicitudes/", {**self.params, "pagina": "2"})
        self.assertEqual(len(first.context["solicitudes"]), 20)
        self.assertEqual(len(second.context["solicitudes"]), 1)
        self.assertEqual(first.context["page"].paginator.count, 21)
        self.assertIn("desde=2026-10-09", first.context["current_query"])

    def test_default_month_warns_about_older_pending_and_feedback_stays_visible(self):
        old = self.create_request(self.start - timedelta(days=90), "error_emision")
        self.create_request(self.start - timedelta(days=90))
        with patch("Qbi2.history_filters.timezone.localdate", return_value=self.day):
            response = self.client.get("/recetas/medico/solicitudes/", {"resultado": old.pk})
        self.assertEqual(response.context["solicitudes"], [])
        self.assertEqual(response.context["resultado_solicitud"].pk, old.pk)
        self.assertContains(response, "Emisión fallida")
        self.assertContains(response, "Ver todos los pendientes")

    def test_remove_error_preserves_audit_documents_and_filters(self):
        item = self.create_request(self.start, "error_emision")
        emission = EmisionSolicitudReceta.objects.create(
            solicitud=item, orden=1, total=2, estado="emitida",
            qbi2_pdf_url="https://example.com/receta.pdf",
        )
        before = self.client.get("/recetas/medico/solicitudes/", self.params)
        self.assertContains(before, "Quitar del historial")
        self.assertContains(before, "Esta acción no los anula")
        url = f"/recetas/api/medico/solicitudes/{item.pk}/quitar-error/"
        response = self.client.post(url, {"next": "/recetas/medico/solicitudes/?estado=error_emision&modo=fechas&desde=2026-10-09&hasta=2026-10-09"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("desde=2026-10-09", response.url)
        self.assertNotIn("resultado", response.url)
        item.refresh_from_db()
        self.assertIsNotNone(item.hidden_from_history_at)
        self.assertIn("history_removed_by", item.auditoria)
        self.assertTrue(EmisionSolicitudReceta.objects.filter(pk=emission.pk).exists())
        after = self.client.get("/recetas/medico/solicitudes/", {**self.params, "resultado": item.pk})
        self.assertEqual(after.context["solicitudes"], [])
        self.assertIsNone(after.context["resultado_solicitud"])
        self.assertEqual(self.client.post(url).status_code, 302)

    def test_remove_is_authenticated_post_and_csrf_protected(self):
        item = self.create_request(self.start, "error_emision")
        url = f"/recetas/api/medico/solicitudes/{item.pk}/quitar-error/"
        self.assertEqual(self.client.get(url).status_code, 405)
        anonymous = Client()
        self.assertEqual(anonymous.post(url).status_code, 302)
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(get_user_model().objects.get(username="doctor"))
        self.assertEqual(protected.post(url).status_code, 403)
        item.refresh_from_db()
        self.assertIsNone(item.hidden_from_history_at)

    def test_only_error_state_can_be_removed(self):
        for state in ["pendiente", "emitida", "aprobada", "rechazada", "anulada"]:
            with self.subTest(state=state):
                item = self.create_request(self.start, state)
                response = self.client.post(f"/recetas/api/medico/solicitudes/{item.pk}/quitar-error/")
                self.assertEqual(response.status_code, 409)
                item.refresh_from_db()
                self.assertIsNone(item.hidden_from_history_at)
