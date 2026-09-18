import re
import socket
from email import policy
from email.message import EmailMessage
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.conf import settings


PRESCRIPTION_EMAIL_SUBJECT = "Receta emitida por Dr. Omar Prieto Cardiología Integral"
PRESCRIPTION_EMAIL_BODY = """Su receta está disponible a continuación.

Saludos cordiales,
Dr. Omar Prieto
Cardiología Integral
"""


class PrescriptionNotificationError(Exception):
    """No se pudo preparar el borrador de notificación."""


def download_prescription_pdf(url: str) -> bytes:
    parsed = urlparse(url or "")
    if parsed.scheme != "https" or not parsed.netloc:
        raise PrescriptionNotificationError("La receta no tiene un enlace PDF seguro.")

    timeout = float(getattr(settings, "QBI2_TIMEOUT_SECONDS", 15))
    max_bytes = max(
        1024,
        int(getattr(settings, "QBI2_NOTIFICATION_MAX_PDF_BYTES", 20 * 1024 * 1024)),
    )
    request = Request(
        url,
        headers={
            "Accept": "application/pdf,application/octet-stream;q=0.9",
            "User-Agent": "Cardiologia-Integral/recetas",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            final_url = urlparse(response.geturl())
            if final_url.scheme != "https":
                raise PrescriptionNotificationError("El PDF redirigió a un enlace no seguro.")
            pdf = response.read(max_bytes + 1)
    except PrescriptionNotificationError:
        raise
    except HTTPError as exc:
        raise PrescriptionNotificationError(
            f"El servidor del PDF respondió con HTTP {exc.code}."
        ) from exc
    except (URLError, TimeoutError, socket.timeout) as exc:
        raise PrescriptionNotificationError("No se pudo descargar el PDF de la receta.") from exc

    if len(pdf) > max_bytes:
        raise PrescriptionNotificationError("El PDF supera el tamaño permitido.")
    if b"%PDF-" not in pdf[:1024]:
        raise PrescriptionNotificationError("El archivo recibido no es un PDF válido.")
    return pdf


def build_prescription_email_draft(solicitud, pdf: bytes) -> bytes:
    recipient = (solicitud.paciente.mail or "").strip()
    if "\n" in recipient or "\r" in recipient:
        recipient = ""

    message = EmailMessage(policy=policy.SMTP)
    message["To"] = recipient
    message["Subject"] = PRESCRIPTION_EMAIL_SUBJECT
    message["X-Unsent"] = "1"
    message.set_content(PRESCRIPTION_EMAIL_BODY)
    message.add_attachment(
        pdf,
        maintype="application",
        subtype="pdf",
        filename=_prescription_pdf_filename(solicitud),
    )
    return message.as_bytes()


def prescription_draft_filename(solicitud) -> str:
    identifier = solicitud.qbi2_id_receta or solicitud.pk
    safe_identifier = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(identifier)).strip("-._")
    return f"receta-{safe_identifier or solicitud.pk}.eml"


def _prescription_pdf_filename(solicitud) -> str:
    identifier = solicitud.qbi2_id_receta or solicitud.pk
    safe_identifier = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(identifier)).strip("-._")
    return f"receta-{safe_identifier or solicitud.pk}.pdf"
