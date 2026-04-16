from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from main.utils import static_file_url
from django.template.loader import render_to_string

from weasyprint import HTML

from main.models import HistoriaClinica

from .forms import CarotidasForm
from .models import CarotidasEstudio


def nuevo_estudio(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, pk=historia_id)
    action = (request.GET.get("action") or "").lower()
    force_new = action in ("crear", "nuevo")
    estudio = None
    if action == "recuperar":
        estudio_id = request.GET.get("estudio")
        if estudio_id:
            estudio = CarotidasEstudio.objects.filter(pk=estudio_id, historia=historia).first()
    if not estudio and not force_new:
        estudio = CarotidasEstudio.objects.filter(historia=historia).first()

    if request.method == "POST":
        form = CarotidasForm(request.POST, instance=estudio, initial={"historia": historia})
        if form.is_valid():
            estudio = form.save()
            messages.success(request, "Estudio doppler de vasos de cuello guardado.")
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "estudio_id": estudio.pk,
                        "historia_id": historia.pk,
                    }
                )
            return redirect("carotidas:estudio_editar", estudio_id=estudio.pk)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        form = CarotidasForm(instance=estudio, initial={"historia": historia})

    return render(
        request,
        "carotidas/nuevo_estudio.html",
        {
            "form": form,
            "historia": historia,
            "paciente": historia.paciente,
            "estudio": estudio,
        },
    )


def detalle_estudio(request, pk):
    return redirect("carotidas:estudio_editar", estudio_id=pk)


def editar_estudio(request, estudio_id):
    estudio = get_object_or_404(CarotidasEstudio, pk=estudio_id)
    historia = estudio.historia

    if request.method == "POST":
        form = CarotidasForm(request.POST, instance=estudio, initial={"historia": historia})
        if form.is_valid():
            estudio = form.save()
            messages.success(request, "Estudio doppler de vasos de cuello guardado.")
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "estudio_id": estudio.pk,
                        "historia_id": historia.pk,
                    }
                )
            return redirect("carotidas:estudio_editar", estudio_id=estudio.pk)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        form = CarotidasForm(instance=estudio, initial={"historia": historia})

    return render(
        request,
        "carotidas/nuevo_estudio.html",
        {
            "form": form,
            "historia": historia,
            "paciente": historia.paciente,
            "estudio": estudio,
        },
    )


def imprimir_estudio(request, estudio_id, historia_id):
    estudio = get_object_or_404(CarotidasEstudio, pk=estudio_id)
    if estudio.historia_id != historia_id:
        return JsonResponse({"success": False, "error": "Historia clínica no coincide."}, status=404)

    informe_items = []

    def add_item(label, *parts):
        contenido = " ".join([p for p in parts if p]).strip()
        if contenido:
            informe_items.append((label, contenido))

    add_item("Carótida Común Derecha:", estudio.com_der_texto(), estudio.com_derecha if not estudio.com_der_texto() else "")
    add_item("Carótida Interna Derecha:", estudio.int_derecha_texto())
    add_item("Carótida Externa Derecha:", estudio.ext_derecha_texto())
    add_item("Carótida Común Izquierda:", estudio.com_izq_texto(), estudio.com_izquierda if not estudio.com_izq_texto() else "")
    add_item("Carótida Interna Izquierda:", estudio.int_izquierda_texto())
    add_item("Carótida Externa Izquierda:", estudio.ext_izquierda_texto())
    add_item("Arterias Vertebrales:", estudio.art_vertebrales_texto())
    add_item("Imágenes agregadas y sugerencias:", estudio.sugerencias)

    espesor_items = []
    if estudio.esp_int_med_der is not None:
        espesor_items.append(("Derecha:", f"{estudio.esp_int_med_der} mm"))
    if estudio.esp_int_med_izq is not None:
        espesor_items.append(("Izquierda:", f"{estudio.esp_int_med_izq} mm"))

    context = {
        "estudio": estudio,
        "historia": estudio.historia,
        "paciente": estudio.historia.paciente,
        "fecha_estudio": estudio.fecha_estudio or timezone.localdate(),
        "informe_items": informe_items,
        "espesor_items": espesor_items,
        "print_logo_path": static_file_url("main/images/logo_omar_prieto.svg"),
        "print_site_text": "www.cardioprietohc.com",
        "print_header_text": "Consultorio Cardiológico Doctor Omar Prieto",
        "print_css_path": static_file_url("main/css/print.css"),
        "print_show_signature": request.GET.get("firma") == "1",
    }
    html = render_to_string("carotidas/imprimir_estudio.html", context)
    pdf = HTML(string=html).write_pdf()
    filename = f"carotidas_{estudio_id}_{historia_id}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename={filename}"
    return response


def listar_estudios(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, pk=historia_id)
    estudios = (
        CarotidasEstudio.objects.filter(historia=historia)
        .order_by("-id")
        .values_list("id", "fecha_estudio")
    )
    lines = [f"<div>{eid} - {fecha.strftime('%Y-%m-%d')}</div>" for eid, fecha in estudios]
    if not lines:
        lines = ["<div>Sin estudios</div>"]
    return HttpResponse("\n".join(lines))
