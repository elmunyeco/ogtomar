# Verificacion HHCC y QBI2

Fecha: 2026-08-11.

## Alcance verificado

La verificacion cubre el nucleo de Historias Clinicas que usa la integracion QBI2 y la prueba piloto de receta/practica espontanea.

- `main`: creacion de paciente e historia clinica asociada, rutas principales y proteccion de acceso.
- `Qbi2`: cache/vademecum existente, portal de solicitud, cola de aprobacion y receta espontanea.
- Receta espontanea: payload de receta, payload de practica, catalogos por contrato, emision simulada, error exacto del proveedor, anulacion por hash y separacion entre hash y numero documental.

No certifica exhaustivamente los modulos clinicos especializados (`ecocardiograma`, `carotidas`, `ecostress`, `mmii`). Esos modulos no tienen cobertura automatizada propia suficiente y requieren una etapa de pruebas separada.

## Correccion incorporada

Al crear un paciente, la señal que genera su historia clinica normaliza `fechaAlta` a fecha local. Evita que una creacion cercana a medianoche UTC asigne a la historia un dia distinto del paciente.

## Comandos ejecutados

```bash
.venv/bin/python hhcc/manage.py test main Qbi2 --keepdb
.venv/bin/python hhcc/manage.py check
.venv/bin/python hhcc/manage.py makemigrations --check --dry-run
git diff --check
```

Resultado de la suite focalizada: 34 pruebas correctas.

## Nota sobre descubrimiento

En este entorno, `manage.py test` sin etiquetas informa cero pruebas. La ejecucion canónica para esta cobertura es explicita por apps:

```bash
.venv/bin/python hhcc/manage.py test main Qbi2 --keepdb
```
