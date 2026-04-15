from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.formats import date_format
from main.utils import static_file_url

from weasyprint import HTML

from main.models import HistoriaClinica

from .forms import EcostressForm
from .models import EcostressEstudio


DEFAULT_INFORME_ERGOMETRIA = (
    "El paciente no refirió angor ni disnea.\n"
    "No presentó cambios en el segmento ST en relación con el ejercicio\n"
    "No presento arritmias\n"
    "Adecuada respuesta de la presión arterial.\n"
    "Prueba ergometrica máxima, sin evidencias de isquemia miocárdica."
)

DEFAULT_DATOS_ECO = (
    "Funcion sistólica del ventrículo izquierdo conservada.\n"
    "Fraccion de eyección estimada en:  %\n"
    "Motilidad parietal conservada.\n"
    "Estructuras valvulares sin anormalidades.\n"
    "Presion sistólica estimada en la arteria pulmonar:"
)

DEFAULT_CONCLUSION = "Estudio negativo para isquemia miocárdica hasta la frecuencia cardiaca alcanzada"


def nuevo_estudio(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, pk=historia_id)
    action = (request.GET.get("action") or "").lower()
    force_new = action in ("crear", "nuevo")
    estudio = None
    if action == "recuperar":
        estudio_id = request.GET.get("estudio")
        if estudio_id:
            estudio = EcostressEstudio.objects.filter(pk=estudio_id, historia=historia).first()
    if not estudio and not force_new:
        estudio = EcostressEstudio.objects.filter(historia=historia).first()

    initial = {"historia": historia}
    if not estudio:
        initial.update(
            {
                "informe_ergometria": DEFAULT_INFORME_ERGOMETRIA,
                "datos_ecocardiograficos_basales": DEFAULT_DATOS_ECO,
                "datos_ecocardiograficos_post_esfuerzo_inmediato": DEFAULT_DATOS_ECO,
                "conclusion": DEFAULT_CONCLUSION,
                "tipo_apremio": "Físico",
            }
        )

    if request.method == "POST":
        form = EcostressForm(request.POST, instance=estudio, initial=initial)
        if form.is_valid():
            estudio = form.save(commit=False)
            if not estudio.fecha_estudio:
                estudio.fecha_estudio = timezone.localdate()
            estudio.save()
            messages.success(request, "Estudio de ecostrés cardíaco guardado.")
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "estudio_id": estudio.pk,
                        "historia_id": historia.pk,
                    }
                )
            return redirect("ecostress:ecostress_nuevo", historia_id=historia.pk)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        form = EcostressForm(instance=estudio, initial=initial)
        if not estudio:
            form.initial["fecha_estudio"] = timezone.localdate()

    return render(
        request,
        "ecostress/nuevo_estudio.html",
        {
            "form": form,
            "historia": historia,
            "paciente": historia.paciente,
            "estudio": estudio,
            "default_informe": DEFAULT_INFORME_ERGOMETRIA,
            "default_datos_eco": DEFAULT_DATOS_ECO,
            "default_conclusion": DEFAULT_CONCLUSION,
        },
    )


def imprimir_estudio(request, estudio_id, historia_id):
    estudio = get_object_or_404(EcostressEstudio, pk=estudio_id)
    if estudio.historia_id != historia_id:
        return JsonResponse({"success": False, "error": "Historia clínica no coincide."}, status=404)

    def non_empty(value):
        return value.strip() if value else ""

    datos_estudio = []
    def add_dato(label, value):
        value = non_empty(value)
        if value:
            datos_estudio.append((label, value))

    add_dato("Fecha del estudio:", date_format(estudio.fecha_estudio, "j \\d\\e F \\d\\e Y") if estudio.fecha_estudio else "")
    add_dato("Indicacion del estudio:", estudio.indicacion_estudio)
    add_dato("Tipo de apremio:", estudio.tipo_apremio)
    add_dato("Medicacion al momento del estudio:", estudio.medicacion_momento_estudio)
    add_dato("Medico solicitante:", estudio.medico_solicitante)

    prueba_items = []
    def add_prueba(label, value, suffix=""):
        value = non_empty(value)
        if value:
            prueba_items.append((label, f"{value}{suffix}"))

    add_prueba("Frecuencia cardiaca basal:", estudio.frecuencia_cardiaca_basal, " Lpm")
    add_prueba(
        "Frecuencia cardíaca máxima alcanzada:",
        estudio.frecuencia_cardiaca_maxima,
        " Lpm",
    )
    presion_basal_inicial = non_empty(estudio.presion_arterial_basal_inicial)
    presion_basal_final = non_empty(estudio.presion_arterial_basal_final)
    presion_maxima_inicial = non_empty(estudio.presion_arterial_maxima_inicial)
    presion_maxima_final = non_empty(estudio.presion_arterial_maxima_final)

    if presion_basal_inicial and presion_basal_final:
        presion_basal = f"{presion_basal_inicial} / {presion_basal_final} mmHg"
    elif presion_basal_inicial:
        presion_basal = f"{presion_basal_inicial} mmHg"
    elif presion_basal_final:
        presion_basal = f"{presion_basal_final} mmHg"
    else:
        presion_basal = ""

    if presion_maxima_inicial and presion_maxima_final:
        presion_maxima = f"{presion_maxima_inicial} / {presion_maxima_final} mmHg"
    elif presion_maxima_inicial:
        presion_maxima = f"{presion_maxima_inicial} mmHg"
    elif presion_maxima_final:
        presion_maxima = f"{presion_maxima_final} mmHg"
    else:
        presion_maxima = ""

    add_prueba("Presión arterial basal:", presion_basal)
    add_prueba("Presión arterial máxima alcanzada:", presion_maxima)

    texto_items = []
    def add_texto(label, value):
        value = non_empty(value)
        if value:
            texto_items.append((label, value))

    add_texto("Informe ergometria", estudio.informe_ergometria)
    add_texto("Datos ecocardiograficos basales", estudio.datos_ecocardiograficos_basales)
    add_texto(
        "Datos ecocardiograficos post esfuerzo inmediato",
        estudio.datos_ecocardiograficos_post_esfuerzo_inmediato,
    )
    add_texto("Conclusion", estudio.conclusion)

    context = {
        "estudio": estudio,
        "historia": estudio.historia,
        "paciente": estudio.historia.paciente,
        "fecha_estudio": estudio.fecha_estudio or timezone.localdate(),
        "datos_estudio": datos_estudio,
        "prueba_items": prueba_items,
        "texto_items": texto_items,
        "print_logo_path": static_file_url("main/images/logo_omar_prieto.svg"),
        "print_site_text": "www.cardioprieto.com",
        "print_header_text": "Consultorio Cardiológico Doctor Omar Prieto",
        "print_css_path": static_file_url("main/css/print.css"),
        "print_show_signature": request.GET.get("firma") == "1",
    }
    html = render_to_string("ecostress/imprimir_estudio.html", context)
    pdf = HTML(string=html).write_pdf()
    filename = f"ecostress_{estudio_id}_{historia_id}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename={filename}"
    return response


def listar_estudios(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, pk=historia_id)
    estudios = (
        EcostressEstudio.objects.filter(historia=historia)
        .order_by("-id_stress")
        .values_list("id_stress", "fecha_estudio")
    )
    lines = [f"<div>{eid} - {fecha.strftime('%Y-%m-%d')}</div>" for eid, fecha in estudios]
    if not lines:
        lines = ["<div>Sin estudios</div>"]
    return HttpResponse("\n".join(lines))
