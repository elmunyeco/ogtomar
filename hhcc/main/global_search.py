import re
import unicodedata
from dataclasses import dataclass

from django.db import transaction
from django.db.models import Count, Sum
from django.urls import reverse

from .models import (
    GlobalSearchDocument,
    GlobalSearchGram,
    HistoriaClinica,
    Paciente,
)


MIN_GLOBAL_SEARCH_LENGTH = 3
FIELD_WEIGHTS = {
    "paciente_id": 100,
    "historia_id": 100,
    "documento": 100,
    "apellido": 90,
    "nombre": 80,
}


@dataclass(frozen=True)
class SearchValidation:
    ok: bool
    normalized_query: str
    message: str = ""


def normalize_search_text(value):
    if value is None:
        return ""
    text = str(value).lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def search_tokens(value):
    normalized = normalize_search_text(value)
    return re.findall(r"[a-z0-9]+", normalized)


def token_trigrams(token):
    if len(token) < MIN_GLOBAL_SEARCH_LENGTH:
        return []
    return [token[index:index + MIN_GLOBAL_SEARCH_LENGTH] for index in range(len(token) - 2)]


def query_trigrams(query):
    grams = []
    for token in search_tokens(query):
        grams.extend(token_trigrams(token))
    return sorted(set(grams))


def validate_global_query(query):
    normalized = normalize_search_text(query)
    compact = normalized.replace(" ", "")
    if not compact:
        return SearchValidation(False, normalized)
    if len(compact) < MIN_GLOBAL_SEARCH_LENGTH:
        return SearchValidation(
            False,
            normalized,
            "La busqueda global requiere al menos 3 caracteres. Para busquedas de 1 o 2 caracteres, use la busqueda clasica de Historia o Paciente.",
        )
    if not query_trigrams(normalized):
        return SearchValidation(
            False,
            normalized,
            "La busqueda global requiere al menos 3 caracteres utiles.",
        )
    return SearchValidation(True, normalized)


def build_document_payload(paciente, historia=None):
    historia_id = historia.id if historia else None
    parts = [
        paciente.id,
        historia_id,
        paciente.numDoc,
        paciente.apellido,
        paciente.nombre,
    ]
    title = f"{paciente.apellido}, {paciente.nombre}".strip(", ")
    subtitle_bits = [f"Doc {paciente.numDoc}", f"Paciente #{paciente.id}"]
    if historia_id:
        subtitle_bits.append(f"Historia #{historia_id}")
    return {
        "document_key": f"historia:{historia_id}" if historia_id else f"paciente:{paciente.id}",
        "paciente": paciente,
        "historia": historia,
        "title": title,
        "subtitle": " - ".join(str(bit) for bit in subtitle_bits if bit),
        "search_text_normalized": normalize_search_text(" ".join(str(part) for part in parts if part)),
    }


def build_weighted_grams(paciente, historia=None):
    weighted = {}
    weighted_fields = [
        (paciente.id, FIELD_WEIGHTS["paciente_id"]),
        (historia.id if historia else None, FIELD_WEIGHTS["historia_id"]),
        (paciente.numDoc, FIELD_WEIGHTS["documento"]),
        (paciente.apellido, FIELD_WEIGHTS["apellido"]),
        (paciente.nombre, FIELD_WEIGHTS["nombre"]),
    ]
    for value, weight in weighted_fields:
        for token in search_tokens(value):
            for gram in token_trigrams(token):
                weighted[gram] = max(weighted.get(gram, 0), weight)
    return weighted


@transaction.atomic
def index_patient_history(paciente, historia=None):
    payload = build_document_payload(paciente, historia)
    document, _created = GlobalSearchDocument.objects.update_or_create(
        document_key=payload["document_key"],
        defaults={
            "paciente": payload["paciente"],
            "historia": payload["historia"],
            "title": payload["title"],
            "subtitle": payload["subtitle"],
            "search_text_normalized": payload["search_text_normalized"],
        },
    )
    GlobalSearchGram.objects.filter(document=document).delete()
    grams = [
        GlobalSearchGram(document=document, gram=gram, weight=weight)
        for gram, weight in build_weighted_grams(paciente, historia).items()
    ]
    GlobalSearchGram.objects.bulk_create(grams, batch_size=1000)
    return document


def index_paciente(paciente):
    historias = list(HistoriaClinica.objects.filter(paciente=paciente).order_by("id"))
    if historias:
        for historia in historias:
            index_patient_history(paciente, historia)
        GlobalSearchDocument.objects.filter(
            document_key=f"paciente:{paciente.id}",
            historia__isnull=True,
        ).delete()
        return
    index_patient_history(paciente, None)


def index_historia(historia):
    index_patient_history(historia.paciente, historia)


@transaction.atomic
def rebuild_global_search_index():
    GlobalSearchGram.objects.all().delete()
    GlobalSearchDocument.objects.all().delete()

    indexed_patient_ids = set()
    for historia in HistoriaClinica.objects.select_related("paciente").order_by("id").iterator():
        index_patient_history(historia.paciente, historia)
        indexed_patient_ids.add(historia.paciente_id)

    for paciente in Paciente.objects.exclude(id__in=indexed_patient_ids).order_by("id").iterator():
        index_patient_history(paciente, None)


def exact_boost(document, normalized_query):
    score = 0
    paciente_id = str(document.paciente_id)
    historia_id = str(document.historia_id or "")
    paciente = document.paciente
    documento = normalize_search_text(paciente.numDoc)
    apellido = normalize_search_text(paciente.apellido)
    nombre = normalize_search_text(paciente.nombre)

    if normalized_query == historia_id:
        score += 10000
    if normalized_query == paciente_id:
        score += 9500
    if normalized_query == documento:
        score += 9000
    if normalized_query == apellido:
        score += 7000
    if normalized_query == nombre:
        score += 5500
    if normalized_query and normalized_query in apellido:
        score += 3500
    if normalized_query and normalized_query in documento:
        score += 3200
    if normalized_query and documento.endswith(normalized_query):
        score += 1600
    if normalized_query and normalized_query in nombre:
        score += 2500
    if normalized_query and normalized_query in paciente_id:
        score += 2200
    if normalized_query and paciente_id.endswith(normalized_query):
        score += max(0, 1800 - len(paciente_id) * 80)
    if normalized_query and historia_id and normalized_query in historia_id:
        score += 2200
    if normalized_query and historia_id and historia_id.endswith(normalized_query):
        score += max(0, 1800 - len(historia_id) * 80)
    return score


def study_links_for_historia(historia):
    if not historia:
        return []

    from carotidas.models import CarotidasEstudio
    from ecocardiograma.models import EstudioEcocardiograma
    from ecostress.models import EcostressEstudio
    from mmii.models import MmiiEstudio

    links = []
    for estudio in EstudioEcocardiograma.objects.filter(historia=historia).order_by("-fecha", "-id"):
        links.append({
            "type": "study",
            "kind": "Eco",
            "label": "ECO",
            "date": estudio.fecha,
            "url": reverse("ecocardiograma:estudio_editar", args=[estudio.id]),
            "description": estudio.fecha.strftime("%d/%m/%Y"),
        })
    for estudio in EcostressEstudio.objects.filter(historia=historia).order_by("-fecha_estudio", "-id_stress"):
        links.append({
            "type": "study",
            "kind": "Stress",
            "label": "Stress",
            "date": estudio.fecha_estudio,
            "url": reverse("ecostress:estudio_editar", args=[estudio.id_stress]),
            "description": estudio.fecha_estudio.strftime("%d/%m/%Y") if estudio.fecha_estudio else "Sin fecha",
        })
    for estudio in CarotidasEstudio.objects.filter(historia=historia).order_by("-fecha_estudio", "-id"):
        links.append({
            "type": "study",
            "kind": "Carotidas",
            "label": "Carotidas",
            "date": estudio.fecha_estudio,
            "url": reverse("carotidas:estudio_editar", args=[estudio.id]),
            "description": estudio.fecha_estudio.strftime("%d/%m/%Y"),
        })
    for estudio in MmiiEstudio.objects.filter(historia=historia).order_by("-fecha_estudio", "-id_mmii"):
        links.append({
            "type": "study",
            "kind": "MMII",
            "label": "MMII",
            "date": estudio.fecha_estudio,
            "url": reverse("mmii:estudio_editar", args=[estudio.id_mmii]),
            "description": estudio.fecha_estudio.strftime("%d/%m/%Y"),
        })
    return sorted(links, key=lambda item: (item["date"] is None, item["date"]), reverse=True)


def global_search(query, page=1, per_page=10):
    page = max(int(page or 1), 1)
    per_page = max(int(per_page or 10), 1)
    visible_until = page * per_page
    validation = validate_global_query(query)
    if not validation.ok:
        return {
            "query": query,
            "error": validation.message,
            "results": [],
            "page": page,
            "per_page": per_page,
            "has_previous": False,
            "has_next": False,
        }

    grams = query_trigrams(validation.normalized_query)
    candidate_pool_size = max((visible_until + per_page) * 80, 1000)
    candidate_ids = (
        GlobalSearchGram.objects.filter(gram__in=grams)
        .values("document_id")
        .annotate(matched_grams=Count("gram", distinct=True), gram_score=Sum("weight"))
        .order_by("-matched_grams", "-gram_score")
        .values_list("document_id", flat=True)[:candidate_pool_size]
    )
    documents = (
        GlobalSearchDocument.objects.filter(id__in=list(candidate_ids))
        .select_related("paciente", "historia")
    )
    ranked = []
    for document in documents:
        boost = exact_boost(document, validation.normalized_query)
        gram_score = sum(
            gram.weight
            for gram in document.grams.filter(gram__in=grams)
        )
        matched = document.grams.filter(gram__in=grams).count()
        ranked.append((boost + gram_score + matched * 25, matched, document))

    ranked.sort(key=lambda item: (-item[0], -item[1], item[2].title.casefold(), item[2].id))
    page_start = (page - 1) * per_page
    page_end = page_start + per_page
    page_items = ranked[page_start:page_end]

    results = []
    for score, matched, document in page_items:
        historia = document.historia
        paciente = document.paciente
        actions = [
            {
                "type": "primary",
                "kind": "Paciente",
                "label": "Editar paciente",
                "url": reverse("editar_paciente", args=[paciente.id]),
            }
        ]
        if historia:
            actions.append({
                "type": "primary",
                "kind": "Historia",
                "label": "Abrir historia",
                "url": reverse("detalle_historia_con_historial", args=[historia.id]),
            })
        actions.extend(study_links_for_historia(historia))
        results.append({
            "document": document,
            "paciente": paciente,
            "historia": historia,
            "score": score,
            "matched_grams": matched,
            "actions": actions,
        })

    return {
        "query": query,
        "error": "",
        "results": results,
        "page": page,
        "per_page": per_page,
        "has_previous": page > 1,
        "previous_page": page - 1,
        "has_next": len(ranked) > page_end,
        "next_page": page + 1,
        "approx_total": len(ranked),
    }
