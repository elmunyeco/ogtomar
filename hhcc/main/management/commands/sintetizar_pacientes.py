# mi_app/management/commands/agregar_pacientes_sinteticos.py

from django.core.management.base import BaseCommand
from main.models import Paciente, TipoDocumento
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Agrega pacientes sintéticos a la base de datos'

    def handle(self, *args, **kwargs):
        tipo_doc, created = TipoDocumento.objects.get_or_create(nombre="DNI", descripcion="Documento Nacional de Identidad")
        sexo_choices = [choice[0] for choice in Paciente.SEXO_CHOICES]

        for i in range(100):
            Paciente.objects.create(
                idtipodoc=tipo_doc,
                mail=f'paciente{i}@example.com',
                plan=f'Plan_{i % 10}',
                sexo=random.choice(sexo_choices),
                debaja=False,
                nombre=f'Nombre_{i+1}',
                numdoc=f'{i+1:08d}',
                celular=f'12345678{i % 10}',
                afiliado=f'Afiliado_{i % 20}',
                apellido=f'Apellido_{i+1}',
                fechanac=timezone.now().date(),
                telefono=f'87654321{i % 10}',
                direccion=f'Calle Falsa {i+1}',
                fechaalta=timezone.now().date(),
                localidad=f'Localidad_{i % 30}',
                profesion=f'Profesion_{i % 15}',
                referente=f'Referente_{i % 5}',
                obrasocial=f'ObraSocial_{i % 7}'
            )

        self.stdout.write(self.style.SUCCESS('100 pacientes sintéticos agregados con éxito'))
