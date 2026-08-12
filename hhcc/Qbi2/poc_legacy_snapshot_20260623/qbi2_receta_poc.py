import json

from django.core.management.base import BaseCommand, CommandError

from Qbi2.client import Qbi2HTTPError
from Qbi2.recipes import (
    DEFAULT_LOTRIAL_REG_NO,
    build_hml_receta_poc_payload,
    emitir_receta_hml_poc,
    summarize_receta_response,
)


class Command(BaseCommand):
    help = "Construye o emite una receta PoC contra Qbi2 HML con datos ficticios."

    def add_arguments(self, parser):
        parser.add_argument("--send", action="store_true", help="Emite la receta en Qbi2 HML. Sin esto solo imprime payload.")
        parser.add_argument("--reg-no", default=DEFAULT_LOTRIAL_REG_NO, help="Registro de medicamento. Default: Lotrial 34959.")
        parser.add_argument("--nro-doc", default=None, help="DNI ficticio del paciente. Default: generado.")
        parser.add_argument("--diagnostico", default="Hipertension arterial", help="Diagnostico texto libre o CIE-10.")
        parser.add_argument("--raw", action="store_true", help="Imprime respuesta completa del proveedor.")

    def handle(self, *args, **options):
        if not options["send"]:
            payload = build_hml_receta_poc_payload(
                reg_no=options["reg_no"],
                nro_doc=options["nro_doc"],
                diagnostico=options["diagnostico"],
            )
            self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
            self.stdout.write(self.style.WARNING("Dry-run: agregar --send para emitir en Qbi2 HML."))
            return

        try:
            result = emitir_receta_hml_poc(
                reg_no=options["reg_no"],
                nro_doc=options["nro_doc"],
                diagnostico=options["diagnostico"],
            )
        except Qbi2HTTPError as exc:
            raise CommandError(
                json.dumps(
                    {
                        "message": str(exc),
                        "provider_status": exc.status_code,
                        "provider_payload": exc.payload,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            ) from exc

        if options["raw"]:
            self.stdout.write(json.dumps(result.response, ensure_ascii=False, indent=2))
            return

        self.stdout.write(json.dumps(summarize_receta_response(result.response), ensure_ascii=False, indent=2))
