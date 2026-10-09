import json
from datetime import timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from main.models import Paciente, TipoDocumento
from .models import EmisionSolicitudReceta, MedicamentoHabitualOculto, SolicitudReceta
from .patient_history import usual_medications
from .portal import PATIENT_SESSION_KEY


@override_settings(QBI2_PROFILE_YAML_PATH=str(Path(__file__).resolve().parents[1] / "private/qbi2/profile.example.yaml"))
class PatientHistoryTests(TestCase):
    def setUp(self):
        tipo = TipoDocumento.objects.create(nombre="DNI", descripcion="Documento")
        self.patient = Paciente.objects.create(idTipoDoc=tipo, numDoc="99000001", nombre="Prueba", apellido="Historial")
        self.other = Paciente.objects.create(idTipoDoc=tipo, numDoc="99000002", nombre="Otro", apellido="Paciente")
        session = self.client.session
        session[PATIENT_SESSION_KEY] = self.patient.pk
        session.save()
        self.doctor = get_user_model().objects.create_user(username="doctor", password="test")

    def order(self, keys, state="emitida", patient=None, days=0, note=""):
        patient = patient or self.patient
        meds = [{"regNo":key,"nombreProducto":f"Producto {key}","nombreDroga":"Droga","presentacion":f"Presentación {key}"} for key in keys]
        item = SolicitudReceta.objects.create(
            paciente=patient, historia_clinica=patient.historias_clinicas.get(), estado=state,
            medicamento_reg_no=keys[0], auditoria={"medicamentos":meds},
            fecha_decision=timezone.now()-timedelta(days=days), observacion_medico=note,
        )
        if state=="emitida":
            EmisionSolicitudReceta.objects.create(solicitud=item,orden=1,total=1,medicamentos=meds,estado="emitida",qbi2_pdf_url="https://example.com/p.pdf")
        return item

    def test_ranking_counts_distinct_complete_issued_orders_not_occasional_requests(self):
        self.order(["A", "B"], days=3)
        self.order(["A", "B"], days=2)
        self.order(["A", "occasional"], days=1)
        for state in ["pendiente", "rechazada", "aprobada", "error_emision"]:
            self.order(["not-issued"], state=state)
            self.order(["not-issued"], state=state)
        self.order(["private"], patient=self.other)
        self.order(["private"], patient=self.other)
        items=usual_medications(self.patient)
        self.assertEqual([i["regNo"] for i in items], ["A","B"])
        self.assertEqual([i["frequency"] for i in items], [3,2])

    def test_split_documents_duplicates_count_once_and_actual_issued_items_win(self):
        for _ in range(2):
            item=self.order(["requested"])
            doc=item.emisiones.get()
            doc.medicamentos=[{"regNo":"actual", "nombreProducto":"Corregido"}]*2
            doc.total=2
            doc.save()
            EmisionSolicitudReceta.objects.create(solicitud=item,orden=2,total=2,estado="emitida",medicamentos=doc.medicamentos,qbi2_pdf_url="https://example.com/p2.pdf")
        result=usual_medications(self.patient)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["regNo"],"actual")
        self.assertEqual(result[0]["frequency"],2)

    def test_ranking_tie_uses_recency_and_library_can_exceed_order_limit(self):
        for _ in range(2):
            self.order([str(i) for i in range(12)], days=2)
        self.order(["recent"],days=1)
        self.order(["recent"])
        items=usual_medications(self.patient)
        self.assertEqual(len(items),13)
        self.assertEqual(items[0]["regNo"],"recent")

    def test_remove_is_patient_scoped_persistent_and_preserves_history(self):
        for patient in [self.patient,self.other]:
            self.order(["A"],patient=patient)
            self.order(["A"],patient=patient)
        count=SolicitudReceta.objects.count()
        endpoint="/recetas/api/paciente/habituales/quitar/"
        response=self.client.post(endpoint,json.dumps({"regNo":"A","pacienteId":self.other.pk}),content_type="application/json")
        self.assertEqual(response.status_code,200)
        self.assertTrue(MedicamentoHabitualOculto.objects.filter(paciente=self.patient,reg_no="A").exists())
        self.assertFalse(MedicamentoHabitualOculto.objects.filter(paciente=self.other).exists())
        self.assertEqual(SolicitudReceta.objects.count(),count)
        self.order(["A"])
        self.assertEqual(usual_medications(self.patient),[])
        self.assertEqual(len(usual_medications(self.other)),1)

    def test_authentication_csrf_and_not_removing_unowned_medications(self):
        endpoints=["/recetas/api/paciente/habituales/","/recetas/api/paciente/pedidos/"]
        for url in endpoints:
            self.assertEqual(Client().get(url).status_code,401)
        url="/recetas/api/paciente/habituales/quitar/"
        self.assertEqual(self.client.get(url).status_code,405)
        self.assertEqual(Client().post(url,"{}",content_type="application/json").status_code,401)
        self.assertEqual(self.client.post(url,json.dumps({"regNo":"unknown"}),content_type="application/json").status_code,404)
        secure=Client(enforce_csrf_checks=True)
        session=secure.session; session[PATIENT_SESSION_KEY]=self.patient.pk; session.save()
        self.assertEqual(secure.post(url,"{}",content_type="application/json").status_code,403)

    def test_orders_expose_exact_decision_only_to_own_patient_with_pagination(self):
        note='Necesita consulta.\nMotivo completo: <ejemplo> "sin cambios".'
        rejected=self.order(["A"],state="rechazada",note=note)
        self.order(["B"],patient=self.other,note="Privado de otra persona")
        data=self.client.get("/recetas/api/paciente/pedidos/", {"pacienteId":self.other.pk}).json()
        self.assertEqual(data["count"],1)
        self.assertEqual(data["items"][0]["id"],rejected.pk)
        self.assertEqual(data["items"][0]["doctor_message"],note)
        for _ in range(10): self.order(["A"])
        self.assertEqual(len(self.client.get("/recetas/api/paciente/pedidos/").json()["items"]),10)
        self.assertEqual(len(self.client.get("/recetas/api/paciente/pedidos/?pagina=2").json()["items"]),1)

    def test_rejection_requires_reason_and_patient_gets_the_same_text(self):
        order=self.order(["A"],state="pendiente")
        doctor_client=Client(); doctor_client.force_login(self.doctor)
        url=f"/recetas/api/medico/solicitudes/{order.pk}/rechazar/"
        response=doctor_client.post(url,{"observacion_medico":"   "},follow=True)
        self.assertContains(response,"Indicar el motivo del rechazo")
        order.refresh_from_db(); self.assertEqual(order.estado,"pendiente")
        reason="Solicitar una consulta.\nNecesito revisar el tratamiento."
        doctor_client.post(url,{"observacion_medico":reason})
        order.refresh_from_db(); self.assertEqual(order.estado,"rechazada")
        self.assertEqual(self.client.get("/recetas/api/paciente/pedidos/").json()["items"][0]["doctor_message"],reason)

    def test_history_available_even_if_patient_cannot_request_and_unsafe_pdf_is_not_linked(self):
        order=self.order(["A"])
        order.emisiones.update(qbi2_pdf_url="javascript:alert(1)")
        history=self.patient.historias_clinicas.get(); history.fechaAlta=timezone.localdate()-timedelta(days=10*366); history.save()
        response=self.client.get("/recetas/api/paciente/pedidos/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()["items"][0]["documents"],[])
