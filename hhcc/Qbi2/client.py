import json
import logging
import socket
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)


class Qbi2Error(Exception):
    """Error base del cliente Qbi2."""


class Qbi2ConfigurationError(Qbi2Error):
    """Configuracion insuficiente para invocar Qbi2."""


class Qbi2HTTPError(Qbi2Error):
    def __init__(self, message: str, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


@dataclass(frozen=True)
class Qbi2ClientConfig:
    base_url: str
    bearer_token: str
    client_app_id: str
    timeout_seconds: float
    auth_mode: str

    @classmethod
    def from_settings(cls) -> "Qbi2ClientConfig":
        return cls(
            base_url=getattr(settings, "QBI2_BASE_URL", "").rstrip("/") + "/",
            bearer_token=getattr(settings, "QBI2_BEARER_TOKEN", ""),
            client_app_id=str(getattr(settings, "QBI2_CLIENT_APP_ID", "")),
            timeout_seconds=float(getattr(settings, "QBI2_TIMEOUT_SECONDS", 15)),
            auth_mode=getattr(settings, "QBI2_AUTH_MODE", "auto"),
        )


class Qbi2Client:
    def __init__(self, config: Qbi2ClientConfig | None = None):
        self.config = config or Qbi2ClientConfig.from_settings()

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, params=params)

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        return self._request("POST", path, payload=payload)

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        if not self.config.base_url:
            raise Qbi2ConfigurationError("QBI2_BASE_URL no esta configurado.")

        url = urljoin(self.config.base_url, path.lstrip("/"))
        if params:
            clean_params = {key: value for key, value in params.items() if value not in (None, "")}
            if clean_params:
                url = f"{url}?{urlencode(clean_params)}"

        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        if self.config.auth_mode == "required" and not self.config.bearer_token:
            raise Qbi2ConfigurationError("QBI2_BEARER_TOKEN es obligatorio con QBI2_AUTH_MODE=required.")
        if self.config.auth_mode != "none" and self.config.bearer_token:
            headers["Authorization"] = f"Bearer {self.config.bearer_token}"

        request = Request(url, data=body, headers=headers, method=method)

        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                response_body = response.read()
                return self._decode_response(response_body)
        except HTTPError as exc:
            payload = self._decode_response(exc.read())
            logger.warning("Qbi2 devolvio HTTP %s en %s %s", exc.code, method, self._safe_url(url))
            raise Qbi2HTTPError("Qbi2 devolvio un error HTTP.", status_code=exc.code, payload=payload) from exc
        except URLError as exc:
            logger.warning("No se pudo conectar con Qbi2 en %s %s: %s", method, self._safe_url(url), exc)
            raise Qbi2HTTPError("No se pudo conectar con Qbi2.", payload=str(exc)) from exc
        except (TimeoutError, socket.timeout) as exc:
            logger.warning("Timeout invocando Qbi2 en %s %s", method, self._safe_url(url))
            raise Qbi2HTTPError("Timeout esperando respuesta de Qbi2.", payload=str(exc)) from exc

    def _decode_response(self, response_body: bytes) -> Any:
        if not response_body:
            return None
        text = response_body.decode("utf-8", errors="replace")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def _safe_url(self, url: str) -> str:
        return url.split("?")[0]
