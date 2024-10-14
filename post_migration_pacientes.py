#CORRER EN SHELL DE MANAGE PY. python manage.py shell -i ipython
from main.models import Paciente, TipoDocumento

for paciente in Paciente.objects.all():
    # Asignar el tipo de documento correcto en función del valor temporal
    tipo_documento = TipoDocumento.objects.get(id=paciente.idTipoDoc_temp)
    paciente.idTipoDoc = tipo_documento
    paciente.save()
