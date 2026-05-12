from django.core.management.base import BaseCommand

from main.global_search import rebuild_global_search_index
from main.models import GlobalSearchDocument, GlobalSearchGram


class Command(BaseCommand):
    help = "Reconstruye el indice materializado de busqueda global por trigramas."

    def handle(self, *args, **options):
        self.stdout.write("Reconstruyendo indice global de busqueda...")
        rebuild_global_search_index()
        self.stdout.write(
            self.style.SUCCESS(
                "Indice reconstruido: "
                f"{GlobalSearchDocument.objects.count()} documentos, "
                f"{GlobalSearchGram.objects.count()} trigramas."
            )
        )
