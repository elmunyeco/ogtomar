"""Patient-owned prescription history and frequently issued presentations."""
from urllib.parse import urlsplit

from .models import MedicamentoHabitualOculto, SolicitudReceta

USUAL_MEDICATION_LIMIT = 9


def medication_items(raw):
    if not isinstance(raw, list):
        return []
    return [
        {key: str(item.get(key) or "").strip() for key in ("regNo", "nombreProducto", "nombreDroga", "presentacion")}
        for item in raw if isinstance(item, dict) and str(item.get("regNo") or "").strip()
    ]


def requested_medications(order):
    audit = order.auditoria if isinstance(order.auditoria, dict) else {}
    return medication_items(audit.get("medicamentos")) or [{
        "regNo": order.medicamento_reg_no,
        "nombreProducto": order.medicamento_nombre_producto,
        "nombreDroga": order.medicamento_nombre_droga,
        "presentacion": order.medicamento_presentacion,
    }]


def usual_medications(patient):
    excluded = set(MedicamentoHabitualOculto.objects.filter(paciente=patient).values_list("reg_no", flat=True))
    ranking = {}
    orders = SolicitudReceta.objects.filter(paciente=patient, estado=SolicitudReceta.Estado.EMITIDA).prefetch_related("emisiones").order_by("-fecha_decision", "-created_at", "-pk")
    for order in orders.iterator(chunk_size=100):
        emitted = [doc for doc in order.emisiones.all() if doc.estado == "emitida" and doc.qbi2_pdf_url]
        actual = [item for doc in emitted for item in medication_items(doc.medicamentos)]
        # Legacy complete emissions may have only a root PDF and the stored items.
        if not actual and (emitted or order.qbi2_pdf_url):
            actual = requested_medications(order)
        metadata = {item["regNo"]: item for item in requested_medications(order)}
        seen = set()
        issued_at = order.fecha_decision or order.created_at
        for item in actual:
            key = item["regNo"]
            if key in excluded or key in seen:
                continue
            seen.add(key)
            if key not in ranking:
                fallback = metadata.get(key, {})
                ranking[key] = {**{field: value or fallback.get(field, "") for field, value in item.items()}, "frequency": 0, "last_issued": issued_at}
            ranking[key]["frequency"] += 1
            ranking[key]["last_issued"] = max(ranking[key]["last_issued"], issued_at)
    return sorted(
        ranking.values(),
        key=lambda item: (-item["frequency"], -item["last_issued"].timestamp(), item["nombreProducto"].casefold(), item["regNo"]),
    )[:USUAL_MEDICATION_LIMIT]


def safe_pdf_url(value):
    try:
        parsed = urlsplit(value or "")
        return value if parsed.scheme == "https" and parsed.hostname else ""
    except ValueError:
        return ""


def patient_order_data(order):
    documents = []
    for doc in order.emisiones.all():
        url = safe_pdf_url(doc.qbi2_pdf_url)
        if doc.estado == "emitida" and url:
            documents.append({"url": url, "order": doc.orden})
    if not documents and safe_pdf_url(order.qbi2_pdf_url):
        documents.append({"url": order.qbi2_pdf_url, "order": 1})
    return {
        "id": order.pk, "state": order.estado, "state_label": order.get_estado_display(),
        "created_at": order.created_at, "decided_at": order.fecha_decision,
        "medications": requested_medications(order),
        "doctor_message": order.observacion_medico,
        "documents": documents,
    }
