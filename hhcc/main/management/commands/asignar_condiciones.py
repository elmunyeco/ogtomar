import random
from django.core.management.base import BaseCommand
from main.models import HistoriaClinica, CondicionMedica, Antecedente

class Command(BaseCommand):
    help = 'Asigna un conjunto aleatorio de condiciones médicas como antecedentes a cada historia clínica.'

    def handle(self, *args, **kwargs):
        # Obtén todas las condiciones médicas
        condiciones = list(CondicionMedica.objects.all())

        # Itera sobre todas las historias clínicas
        historias_clinicas = HistoriaClinica.objects.all()
        for historia in historias_clinicas:
            # Decide cuántas condiciones asignar (entre 0 y el total de condiciones disponibles)
            num_condiciones = random.randint(0, len(condiciones))
            
            # Selecciona aleatoriamente las condiciones para asignar
            condiciones_asignadas = random.sample(condiciones, num_condiciones)
            
            # Asigna las condiciones como antecedentes a la historia clínica
            for condicion in condiciones_asignadas:
                Antecedente.objects.create(
                    historia_clinica=historia,
                    condicion_medica=condicion
                )

            self.stdout.write(self.style.SUCCESS(
                f"Historia clínica '{historia.id}' asignada con {num_condiciones} antecedente(s)."
            ))

        self.stdout.write(self.style.SUCCESS('Asignación de antecedentes completada.'))
