# utils.py

from django.contrib.staticfiles import finders


def isInt(value):
    if not value and value != 0:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def isFloat(value):
    if not value and value != 0:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def process_signos_vitales(data):
   campos_int = ['presion_sistolica', 'presion_diastolica', 'colesterol', 'glucemia']
   campos_float = ['peso']
   
   signos_vitales = {}
   for campo in data['signos_vitales']:
       valor = data['signos_vitales'][campo]
       if campo in campos_int:
           signos_vitales[campo] = isInt(valor) 
       elif campo in campos_float:
           val = isFloat(valor)
           signos_vitales[campo] = round(val, 2) if val is not None else None
           
   return signos_vitales


def static_file_url(static_path: str) -> str:
    """
    Return a file:// URL for a static asset so WeasyPrint can load it
    without relying on absolute filesystem paths that differ per server.
    """
    fs_path = finders.find(static_path)
    if not fs_path:
        return ""
    return f"file://{fs_path}"
