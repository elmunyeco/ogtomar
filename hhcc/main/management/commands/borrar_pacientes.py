from django.core.management.base import BaseCommand
from django.db import connection, transaction
from main.models import Paciente, HistoriaClinica

class Command(BaseCommand):
    help = 'Borra todos los pacientes y sus correspondientes historias clínicas de la base de datos y resetea las secuencias'

    def handle(self, *args, **kwargs):
        try:
            with transaction.atomic():
                # Borrar todas las historias clínicas
                HistoriaClinica.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Todas las historias clínicas han sido borradas.'))

                # Borrar todos los pacientes
                Paciente.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Todos los pacientes han sido borrados.'))

                # Resetear las secuencias de autoincremento
                self.reset_sequences()

        except Exception as e:
            self.stderr.write(f"Error al intentar borrar los pacientes y sus historias clínicas: {e}")

    def reset_sequences(self):
        with connection.cursor() as cursor:
            # Resetear secuencia de Paciente
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='main_paciente';")
            self.stdout.write(self.style.SUCCESS('Secuencia de Paciente reseteada.'))

            # Resetear secuencia de HistoriaClinica
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='main_historiaclinica';")
            self.stdout.write(self.style.SUCCESS('Secuencia de HistoriaClinica reseteada.'))
