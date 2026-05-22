import json

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from .client import Qbi2ConfigurationError, Qbi2HTTPError
from .recipes import build_hml_receta_poc_payload, emitir_receta_payload, summarize_receta_response
from .services import VademecumService


def vademecum_page(request):
    return render(request, "Qbi2/vademecum.html")


def receta_poc_page(request):
    payload = build_hml_receta_poc_payload(nro_doc="99999999")
    return render(request, "Qbi2/receta_poc.html", {"payload": payload})


@require_GET
def health(request):
    from django.conf import settings

    return JsonResponse(
        {
            "status": "ok",
            "base_url": getattr(settings, "QBI2_BASE_URL", ""),
            "auth_mode": getattr(settings, "QBI2_AUTH_MODE", "auto"),
            "token_configured": bool(getattr(settings, "QBI2_BEARER_TOKEN", "")),
            "client_app_id_configured": bool(getattr(settings, "QBI2_CLIENT_APP_ID", "")),
            "vademecum_path": getattr(settings, "QBI2_VADEMECUM_PATH", ""),
        }
    )


@require_GET
def buscar_vademecum(request):
    query = request.GET.get("q") or request.GET.get("query") or ""
    raw = request.GET.get("raw") == "1"
    extra_params = {
        key.removeprefix("qbi2_"): value
        for key, value in request.GET.items()
        if key.startswith("qbi2_")
    }

    try:
        page = int(request.GET.get("page") or request.GET.get("pagina") or "1")
        result = VademecumService().buscar(query, page=page, extra_params=extra_params)
    except ValidationError as exc:
        return JsonResponse({"status": "error", "message": "; ".join(exc.messages)}, status=400)
    except ValueError:
        return JsonResponse({"status": "error", "message": "La pagina debe ser numerica."}, status=400)
    except Qbi2ConfigurationError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=503)
    except Qbi2HTTPError as exc:
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
                "provider_status": exc.status_code,
                "provider_payload": exc.payload,
            },
            status=502,
        )

    response = {
        "status": "success",
        "query": result["query"],
        "page": result["page"],
        "count": len(result["items"]),
        "pageInfo": result["page_info"],
        "items": result["items"],
    }
    if raw:
        response["raw"] = result["raw"]
    return JsonResponse(response)


@csrf_protect
@require_POST
def emitir_receta_poc(request):
    try:
        form_data = json.loads(request.body.decode("utf-8") or "{}")
        payload = build_hml_receta_poc_payload(
            reg_no=form_data.get("regNo") or "34959",
            nombre_producto=form_data.get("nombreProducto") or "LOTRIAL",
            nombre_droga=form_data.get("nombreDroga") or "enalapril",
            presentacion=form_data.get("presentacion") or "10 mg comp.x 30",
            nro_doc=form_data.get("pacienteNroDoc"),
            paciente_nombre=form_data.get("pacienteNombre") or "Prueba",
            paciente_apellido=form_data.get("pacienteApellido") or "Paciente",
            paciente_sexo=form_data.get("pacienteSexo") or "M",
            paciente_fecha_nacimiento=form_data.get("pacienteFechaNacimiento") or "1980-01-01",
            diagnostico=form_data.get("diagnostico") or "Hipertension arterial",
            posologia=form_data.get("posologia") or "Tomar 1 comprimido por dia segun indicacion medica.",
            cantidad=int(form_data.get("cantidad") or 1),
            tratamiento=int(form_data.get("tratamiento") or 0),
            medico_nombre=form_data.get("medicoNombre") or "Prueba",
            medico_apellido=form_data.get("medicoApellido") or "Medico",
            medico_matricula_tipo=form_data.get("medicoMatriculaTipo") or "MN",
            medico_matricula_numero=form_data.get("medicoMatriculaNumero") or "123456",
            medico_especialidad=form_data.get("medicoEspecialidad") or "Cardiologia",
            medico_profesion=form_data.get("medicoProfesion") or "Medico",
            medico_nro_doc=form_data.get("medicoNroDoc") or "11111111",
            medico_id_tributario=form_data.get("medicoIdTributario") or "20111111112",
            consultorio_nombre=form_data.get("consultorioNombre") or "Consultorio HML Prueba",
            consultorio_direccion=form_data.get("consultorioDireccion") or "Gral. Las Heras 459",
            consultorio_email=form_data.get("consultorioEmail") or "consultorio.prueba@example.com",
            consultorio_contacto=form_data.get("consultorioContacto") or "1100000002",
        )
        result = emitir_receta_payload(payload)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        return JsonResponse({"status": "error", "message": f"Payload invalido: {exc}"}, status=400)
    except Qbi2ConfigurationError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=503)
    except Qbi2HTTPError as exc:
        return JsonResponse(
            {
                "status": "error",
                "message": str(exc),
                "provider_status": exc.status_code,
                "provider_payload": exc.payload,
            },
            status=502,
        )

    return JsonResponse(
        {
            "status": "success",
            "summary": summarize_receta_response(result.response),
            "response": result.response,
        }
    )
