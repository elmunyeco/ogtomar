from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from main.utils import static_file_url

from weasyprint import HTML

from main.models import HistoriaClinica

from .forms import MmiiForm
from .models import MmiiEstudio


DEFAULT_ARTERIA = (
    "Arteria con estructura conservada libre de deformaciones. "
    "Análisis espectral acorde al vaso de estudio. "
    "Velocidades máximas dentro de los límites normales."
)

DEFAULT_CONCLUSION = "Estudio arterial de miembros inferiores dentro de límites normales."


def nuevo_estudio(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, pk=historia_id)
    action = (request.GET.get("action") or "").lower()
    force_new = action in ("crear", "nuevo")
    estudio = None
    if action == "recuperar":
        estudio_id = request.GET.get("estudio")
        if estudio_id:
            estudio = MmiiEstudio.objects.filter(pk=estudio_id, historia=historia).first()
    if not estudio and not force_new:
        estudio = MmiiEstudio.objects.filter(historia=historia).first()

    initial = {"historia": historia}
    if not estudio:
        initial.update(
            {
                "art_fem_comun_derecha": DEFAULT_ARTERIA,
                "art_fem_superficial_derecha": DEFAULT_ARTERIA,
                "art_fem_profunda_derecha": DEFAULT_ARTERIA,
                "art_poplitea_derecha": DEFAULT_ARTERIA,
                "art_infrapatelares_derecha": DEFAULT_ARTERIA,
                "art_fem_comun_izquierda": DEFAULT_ARTERIA,
                "art_fem_superficial_izquierda": DEFAULT_ARTERIA,
                "art_fem_profunda_izquierda": DEFAULT_ARTERIA,
                "art_poplitea_izquierda": DEFAULT_ARTERIA,
                "art_infrapatelares_izquierda": DEFAULT_ARTERIA,
                "conclusion": DEFAULT_CONCLUSION,
            }
        )

    if request.method == "POST":
        form = MmiiForm(request.POST, instance=estudio, initial=initial)
        if form.is_valid():
            estudio = form.save()
            messages.success(request, "Estudio doppler color de MMII guardado.")
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "estudio_id": estudio.pk,
                        "historia_id": historia.pk,
                    }
                )
            return redirect("mmii:mmii_nuevo", historia_id=historia.pk)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        form = MmiiForm(instance=estudio, initial=initial)

    return render(
        request,
        "mmii/nuevo_estudio.html",
        {
            "form": form,
            "historia": historia,
            "paciente": historia.paciente,
            "estudio": estudio,
            "default_arteria": DEFAULT_ARTERIA,
            "default_conclusion": DEFAULT_CONCLUSION,
        },
    )


def imprimir_estudio(request, estudio_id, historia_id):
    estudio = get_object_or_404(MmiiEstudio, pk=estudio_id)
    if estudio.historia_id != historia_id:
        return JsonResponse({"success": False, "error": "Historia clínica no coincide."}, status=404)

    def non_empty(value):
        return value.strip() if value else ""

    derecho_items = []
    izquierdo_items = []

    def add_item(items, label, value):
        value = non_empty(value)
        if value:
            items.append((label, value))

    add_item(derecho_items, "Arteria femoral común", estudio.art_fem_comun_derecha)
    add_item(derecho_items, "Arteria femoral superficial", estudio.art_fem_superficial_derecha)
    add_item(derecho_items, "Arteria femoral profunda (proximal)", estudio.art_fem_profunda_derecha)
    add_item(derecho_items, "Arteria poplítea", estudio.art_poplitea_derecha)
    add_item(
        derecho_items,
        "Arterias infrapatelares (tibial posterior y anterior)",
        estudio.art_infrapatelares_derecha,
    )

    add_item(izquierdo_items, "Arteria femoral común", estudio.art_fem_comun_izquierda)
    add_item(izquierdo_items, "Arteria femoral superficial", estudio.art_fem_superficial_izquierda)
    add_item(izquierdo_items, "Arteria femoral profunda (proximal)", estudio.art_fem_profunda_izquierda)
    add_item(izquierdo_items, "Arteria poplítea", estudio.art_poplitea_izquierda)
    add_item(
        izquierdo_items,
        "Arterias infrapatelares (tibial posterior y anterior)",
        estudio.art_infrapatelares_izquierda,
    )

    context = {
        "estudio": estudio,
        "historia": estudio.historia,
        "paciente": estudio.historia.paciente,
        "fecha_estudio": estudio.fecha_estudio or timezone.localdate(),
        "derecho_items": derecho_items,
        "izquierdo_items": izquierdo_items,
        "conclusion": non_empty(estudio.conclusion),
        "print_logo_path": static_file_url("main/images/logo_omar_prieto.svg"),
        "print_site_text": "www.cardioprieto.com",
        "print_header_text": "Consultorio Cardiológico Doctor Omar Prieto",
        "print_css_path": static_file_url("main/css/print.css"),
        "print_show_signature": request.GET.get("firma") == "1",
    }
    html = render_to_string("mmii/imprimir_estudio.html", context)
    pdf = HTML(string=html).write_pdf()
    filename = f"mmii_{estudio_id}_{historia_id}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename={filename}"
    return response


def listar_estudios(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, pk=historia_id)
    estudios = (
        MmiiEstudio.objects.filter(historia=historia)
        .order_by("-id_mmii")
        .values_list("id_mmii", "fecha_estudio")
    )
    lines = [f"<div>{eid} - {fecha.strftime('%Y-%m-%d')}</div>" for eid, fecha in estudios]
    if not lines:
        lines = ["<div>Sin estudios</div>"]
    return HttpResponse("\n".join(lines))
