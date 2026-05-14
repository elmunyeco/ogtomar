from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .client import Qbi2ConfigurationError, Qbi2HTTPError
from .services import VademecumService


def vademecum_page(request):
    return render(request, "Qbi2/vademecum.html")


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
