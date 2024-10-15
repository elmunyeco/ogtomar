from main.models import Paciente, TipoDocumento

# Recorremos todos los pacientes y actualizamos el valor de idTipoDoc basado en idTipoDoc_temp
for paciente in Paciente.objects.all():
    try:
        # Buscamos el TipoDocumento con el ID que coincide con idTipoDoc_temp
        tipo_documento = TipoDocumento.objects.get(id=paciente.idTipoDoc_temp)
        
        # Actualizamos el campo idTipoDoc_id directamente en la base de datos
        Paciente.objects.filter(id=paciente.id).update(idTipoDoc=tipo_documento)
        
    except TipoDocumento.DoesNotExist:
        # Si el tipo de documento no existe, se puede manejar el error, por ejemplo:
        print(f"TipoDocumento con id {paciente.idTipoDoc_temp} no existe para el paciente {paciente.nombre} {paciente.apellido}")
