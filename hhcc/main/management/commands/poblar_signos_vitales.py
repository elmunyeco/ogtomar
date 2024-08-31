import csv
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from main.models import HistoriaClinica, Visita, SignosVitales

class Command(BaseCommand):
    help = 'Popula los signos vitales desde un archivo CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Ruta al archivo CSV con los signos vitales')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']

        try:
            with open(csv_file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        idhc = int(row['idhc'])

                        # Limitar el procesamiento a idhc de 1 a 100
                        if idhc < 1 or idhc > 100:
                            continue

                        peso = float(row['peso']) if row['peso'] else None
                        fecha = datetime.strptime(row['fecha'], '%Y-%m-%d').date()
                        glucemia = float(row['glucemia']) if row['glucemia'] else None
                        colesterol = float(row['colesterol']) if row['colesterol'] else None
                        presion_sistolica = int(row['presionsistolica']) if row['presionsistolica'] else None
                        presion_diastolica = int(row['presiondiastolica']) if row['presiondiastolica'] else None

                        # Obtener la historia clínica y la visita correspondientes
                        historia_clinica = HistoriaClinica.objects.get(id=idhc)
                        visita, created = Visita.objects.get_or_create(historia_clinica=historia_clinica, fecha=fecha)

                        # Crear y guardar los signos vitales
                        signos_vitales = SignosVitales(
                            visita=visita,
                            peso=peso,
                            glucemia=glucemia,
                            colesterol=colesterol,
                            presion_sistolica=presion_sistolica,
                            presion_diastolica=presion_diastolica
                        )
                        signos_vitales.save()

                        self.stdout.write(self.style.SUCCESS(f'Signos vitales agregados para HC {idhc} en {fecha}'))

                    except HistoriaClinica.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"Historia clínica con id {idhc} no encontrada. Fila: {row}"))
                    except ValueError as e:
                        self.stdout.write(self.style.ERROR(f"Error de conversión de datos en la fila {row}: {e}"))
                    except KeyError as e:
                        self.stdout.write(self.style.ERROR(f"Error: Campo faltante {e} en la fila {row}"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error desconocido al procesar la fila {row}: {e}"))

        except FileNotFoundError:
            raise CommandError(f"Error: El archivo '{csv_file_path}' no se encuentra.")
        except Exception as e:
            raise CommandError(f"Error al abrir el archivo '{csv_file_path}': {e}")
