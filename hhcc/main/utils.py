# utils.py


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
   campos_int = ['presion_sistolica', 'presion_diastolica', 'colesterol', 'glucemia' ]
   campos_float = ['peso']
   
   signos_vitales = {}
   for campo in data['signos_vitales']:
       valor = data['signos_vitales'][campo]
       if campo in campos_int:
           signos_vitales[campo] = isInt(valor) 
       elif campo in campos_float:
           signos_vitales[campo] = isFloat(valor)
           
   return signos_vitales

# A ver esta garompa?
