from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
from main.models import Paciente, HistoriaClinica


@receiver(post_save, sender=Paciente)
def crear_historia_clinica(sender, instance, created, **kwargs):
    if created:
        try:                                                                                        
            with transaction.atomic():
                fecha_alta = instance.fechaAlta
                if hasattr(fecha_alta, "date"):
                    fecha_alta = timezone.localdate(fecha_alta)
                HistoriaClinica.objects.create(paciente=instance, fechaAlta=fecha_alta)
        except Exception as e:
            print(f"Error al crear Historia Clínica: {e}")
            instance.delete()
            raise e


@receiver(post_save, sender=Paciente)
def actualizar_indice_busqueda_paciente(sender, instance, **kwargs):
    def _indexar():
        from main.global_search import index_paciente

        index_paciente(instance)

    transaction.on_commit(_indexar)


@receiver(post_save, sender=HistoriaClinica)
def actualizar_indice_busqueda_historia(sender, instance, **kwargs):
    def _indexar():
        from main.global_search import index_historia

        index_historia(instance)

    transaction.on_commit(_indexar)
