import csv
from django.core.management.base import BaseCommand
from main.models import CondicionMedica

class Command(BaseCommand):
    help = 'Cargar datos de Condiciones desde el archivo CSV de Enfermedades'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='La ruta del archivo CSV a procesar')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        with open(csv_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    # Crear o actualizar Condicion
                    condicion, created = CondicionMedica.objects.update_or_create(
                        nombre=row['nombre'],
                        defaults={
                            'descripcion': '',
                            'tipo': 'otro',  # Tipo genérico que luego se podrá modificar en admin
                            'orden': int(row['orden'])
                        }
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Condición '{row['nombre']}' creada exitosamente."))
                    else:
                        self.stdout.write(self.style.WARNING(f"Condición '{row['nombre']}' actualizada."))

                except Exception as e:
                    error_msg = f"Error al procesar la fila {row}: {e}"
                    self.stderr.write(self.style.ERROR(error_msg))
                    continue

        self.stdout.write(self.style.SUCCESS('Datos de Condiciones cargados exitosamente'))
