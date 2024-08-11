from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from main.models import Paciente, HistoriaClinica


@receiver(post_save, sender=Paciente)
def crear_historia_clinica(sender, instance, created, **kwargs):
    if created:
        try:                                                                                        
            with transaction.atomic():
                HistoriaClinica.objects.create(paciente=instance, fechaalta=instance.fechaalta)
        except Exception as e:
            print(f"Error al crear Historia Clínica: {e}")
            instance.delete()
            raise e

