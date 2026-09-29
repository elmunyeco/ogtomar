"""Carga segura del perfil profesional QBI2 desde un YAML externo."""

import copy
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from django.conf import settings

from .client import Qbi2ConfigurationError


def load_professional_profile() -> dict[str, Any]:
    raw_path = str(getattr(settings, "QBI2_PROFILE_YAML_PATH", "") or "").strip()
    if not raw_path:
        raise Qbi2ConfigurationError("Falta configurar QBI2_PROFILE_YAML_PATH.")

    path = Path(raw_path).expanduser()
    try:
        stat = path.stat()
    except OSError as exc:
        raise Qbi2ConfigurationError(f"No se pudo leer el perfil QBI2: {path}.") from exc

    profile = copy.deepcopy(_load_profile_file(str(path.resolve()), stat.st_mtime_ns))
    profile["_config_dir"] = str(path.resolve().parent)
    return profile


@lru_cache(maxsize=8)
def _load_profile_file(path: str, _mtime_ns: int) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise Qbi2ConfigurationError(f"El perfil QBI2 no es un YAML válido: {path}.") from exc

    if not isinstance(raw, dict):
        raise Qbi2ConfigurationError("El perfil QBI2 debe contener un objeto YAML.")
    for section in ("medico", "consultorio"):
        if not isinstance(raw.get(section), dict):
            raise Qbi2ConfigurationError(f"Falta la sección '{section}' en el perfil QBI2.")

    medico = raw["medico"]
    matricula = medico.get("matricula")
    if not isinstance(matricula, dict):
        raise Qbi2ConfigurationError("Falta la sección 'medico.matricula' en el perfil QBI2.")
    for label, value in (
        ("medico.nombre", medico.get("nombre")),
        ("medico.apellido", medico.get("apellido")),
        ("medico.numero_documento", medico.get("numero_documento")),
        ("medico.matricula.tipo", matricula.get("tipo")),
        ("medico.matricula.numero", matricula.get("numero")),
    ):
        if not str(value or "").strip():
            raise Qbi2ConfigurationError(f"Falta el dato obligatorio '{label}' en el perfil QBI2.")
    return raw


def resolve_profile_asset(profile: dict[str, Any], raw_path: Any) -> str:
    value = str(raw_path or "").strip()
    if not value:
        return ""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path(str(profile.get("_config_dir") or "")) / path
    return str(path.resolve())
