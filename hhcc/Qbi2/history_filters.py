"""Calendar ranges for the medical prescription history."""
import calendar
from datetime import date, datetime, time, timedelta

from django.utils import timezone


def history_range(params, today=None):
    today = today or timezone.localdate()
    mode = params.get("modo", "periodo")
    period = params.get("periodo", "mes")
    start_text = params.get("desde", "")
    end_text = params.get("hasta", "")
    error = ""
    start = end = today
    if mode == "fechas":
        try:
            start, end = date.fromisoformat(start_text), date.fromisoformat(end_text)
            if start > end:
                raise ValueError
            # The exclusive upper boundary must be representable.
            end + timedelta(days=1)
        except (ValueError, TypeError, OverflowError):
            error = "Ingresar fechas válidas; Desde debe ser anterior o igual a Hasta."
    else:
        mode = "periodo"
        if period not in {"semana", "mes", "seis_meses", "anio"}:
            period = "mes"
        if period == "semana":
            start = today - timedelta(days=6)
        else:
            months = {"mes": 1, "seis_meses": 6, "anio": 12}[period]
            year, month = divmod(today.year * 12 + today.month - 1 - months, 12)
            month += 1
            start = today.replace(year=year, month=month, day=min(today.day, calendar.monthrange(year, month)[1]))
        start_text, end_text = start.isoformat(), end.isoformat()
    return {
        "mode": mode, "period": period, "start": start, "end": end,
        "start_text": start_text, "end_text": end_text, "error": error,
    }


def filter_history(queryset, selection):
    if selection["error"]:
        return queryset.none()
    zone = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(selection["start"], time.min), zone)
    end = timezone.make_aware(datetime.combine(selection["end"] + timedelta(days=1), time.min), zone)
    return queryset.filter(created_at__gte=start, created_at__lt=end)
