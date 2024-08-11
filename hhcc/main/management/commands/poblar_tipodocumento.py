import csv
from django.core.management.base import BaseCommand
from main.models import TipoDocumento

class Command(BaseCommand):
    help = 'import tipodocumento.csv'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='path a tiṕodocumento.csv')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        with open(csv_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                TipoDocumento.objects.create(
                    id=row['id'],
                    nombre=row['nombre'],
                    descripcion=row['descripcion']
                )
        self.stdout.write(self.style.SUCCESS('Successfully loaded TipoDocumento data'))
