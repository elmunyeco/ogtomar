import csv
import datetime
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import Paciente, TipoDocumento

# Configuración del logger
logger = logging.getLogger('django')

class Command(BaseCommand):
    help = 'Cargar datos de Paciente y HistoriaClinica desde un archivo CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='La ruta del archivo CSV a procesar')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        with open(csv_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    with transaction.atomic():
                        # Verificar si el campo idtipodoc está presente y es válido
                        idtipodoc_value = row.get('idtipodoc')
                        if not idtipodoc_value:
                            error_msg = f"El campo 'idtipodoc' está ausente o es inválido en la fila: {row}"
                            self.stdout.write(self.style.WARNING(error_msg))
                            logger.error(error_msg)
                            idtipodoc_value = 1  # Asignar DNI por defecto
                            # continue  

                        # Validar idtipodoc
                        try:
                            idtipodoc = TipoDocumento.objects.get(id=idtipodoc_value)
                        except (TipoDocumento.DoesNotExist, ValueError) as e:
                            error_msg = f"idtipodoc inválido {idtipodoc_value} en la fila. Saltando esta fila. Error: {e}"
                            self.stdout.write(self.style.WARNING(error_msg))
                            logger.error(error_msg, exc_info=True)
                            idtipodoc = TipoDocumento.objects.get(id=1)  # Asignar DNI por defecto
                            # continue

                        # Manejar campos de fecha
                        try:
                            fechanac = datetime.datetime.strptime(row['fechanac'], '%Y-%m-%d').date() if row['fechanac'] and row['fechanac'] != '0000-00-00' else None
                        except ValueError as e:
                            fechanac = None
                            error_msg = f"Formato de fecha inválido para fechanac en la fila. Establecido en None. Error: {e}"
                            self.stdout.write(self.style.WARNING(error_msg))
                            logger.error(error_msg, exc_info=True)

                        try:
                            fechaalta = datetime.datetime.strptime(row['fechaalta'], '%Y-%m-%d').date() if row['fechaalta'] and row['fechaalta'] != '0000-00-00' else None
                        except ValueError as e:
                            fechaalta = None
                            error_msg = f"Formato de fecha inválido para fechaalta en la fila. Establecido en None. Error: {e}"
                            self.stdout.write(self.style.WARNING(error_msg))
                            logger.error(error_msg, exc_info=True)

                        # Crear la instancia de Paciente (esto automáticamente creará la HistoriaClinica por la señal)
                        Paciente.objects.create(
                            idtipodoc=idtipodoc,
                            mail=row['mail'] if row['mail'] else None,
                            plan=row['plan'] if row['plan'] else None,
                            sexo=row['sexo'],
                            debaja=row['debaja'] == '1',
                            nombre=row['nombre'],
                            numdoc=row['numdoc'],
                            celular=row['celular'] if row['celular'] else None,
                            afiliado=row['afiliado'] if row['afiliado'] else None,
                            apellido=row['apellido'],
                            fechanac=fechanac,
                            telefono=row['telefono'] if row['telefono'] else None,
                            direccion=row['direccion'] if row['direccion'] else None,
                            fechaalta=fechaalta,
                            localidad=row['localidad'],
                            profesion=row['profesion'] if row['profesion'] else None,
                            referente=row['referente'] if row['referente'] else None,
                            obrasocial=row['obrasocial'] if row['obrasocial'] else None
                        )

                except Exception as e:
                    error_msg = f"Error al crear Paciente y su HistoriaClinica para el paciente con datos {row}: {e}"
                    self.stderr.write(f"{error_msg}\n")
                    self.stdout.write(self.style.ERROR(error_msg))
                    logger.error(error_msg, exc_info=True)
                    # continue

        self.stdout.write(self.style.SUCCESS('Datos de Paciente cargados exitosamente'))
