# Implementacion busqueda global por trigramas

## Rama

- Rama de trabajo: `feat/busqueda-global-trigramas`.
- Base: `master` sincronizada con `origin/master`.

## Decisiones aplicadas

- La busqueda global se implementa como indice materializado en MySQL.
- No se usa `LIKE '%...%'` como camino principal.
- No se ejecuta busqueda global con queries de 1 o 2 caracteres.
- Campos indexados:
  - `pacientes.id` con peso 100.
  - `historias_clinicas.id` con peso 100.
  - `pacientes.numDoc` con peso 100.
  - `pacientes.apellido` con peso 90.
  - `pacientes.nombre` con peso 80.

## Paso 1 - Documentacion base

- Se agrego `BUSQUEDA_IDENTIFICATORIA_TRIGRAMAS.md`.
- Se agrego `BUSQUEDA_IDENTIFICATORIA_TRIGRAMAS_PDF.css`.
- Se agrego `generar_pdf_busqueda_trigramas.sh` para regenerar el PDF local.

## Paso 2 - Modelo de datos

Se agregaron dos modelos en `main`:

- `GlobalSearchDocument`: representa un paciente/historia buscable.
- `GlobalSearchGram`: representa los trigramas indexados de cada documento.

Cada documento agrupa los datos identificatorios y mantiene enlaces a `Paciente` y, si existe, `HistoriaClinica`.

## Paso 3 - Servicio de busqueda

Se agrego `main/global_search.py` con:

- Normalizacion de texto.
- Generacion de trigramas.
- Validacion de longitud minima.
- Indexacion de paciente/historia.
- Reconstruccion completa del indice.
- Busqueda y ranking de resultados.
- Armado de acciones: paciente, historia y estudios.

El pool inicial de candidatos se mantiene deliberadamente mas amplio que el limite visible para no perder coincidencias numericas cortas. Por ejemplo, `576` debe poder encontrar `2576`, aunque existan muchos otros IDs o documentos que contengan el mismo trigrama.

El ranking agrega boost para coincidencias por sufijo en ID/documento, porque ese patron es clinicamente util cuando se recuerda el final de un numero.

En empates de score textual, el desempate se hace alfabeticamente por titulo del documento (`Apellido, Nombre`). Esto evita que una busqueda por fragmento de nombre, por ejemplo `quiel`, esconda apellidos esperables solo porque sus IDs son mas antiguos.

La busqueda global queda paginada de a 10 resultados, con navegacion anterior/siguiente en la home. Esto evita forzar scores artificiales o mostrar una lista demasiado larga cuando una query parcial, por ejemplo `quiel`, trae muchos pacientes validos.

Cuando hay mas de 6 paginas, el paginador usa una marca visual tipo Google con variantes `Prieto`, `Prieeto`, `Prieeeto`, etc. Los enlaces usan una escala de tonos rojos alineada con el color principal del sitio.

## Paso 4 - Comando operativo

Se agrego el comando:

```bash
python manage.py rebuild_global_search_index
```

Este comando borra y reconstruye el indice desde las tablas clinicas principales.

## Paso 5 - Actualizacion incremental

Se conectaron señales en `main/signals.py`:

- Al guardar un `Paciente`, se reindexan sus historias asociadas o su documento sin historia.
- Al guardar una `HistoriaClinica`, se reindexa ese documento de historia.

La actualizacion se ejecuta con `transaction.on_commit` para evitar indexar datos que todavia no fueron confirmados en la base.

## Paso 6 - Home como buscador global

La vista `index` ahora lee el parametro `q` y ejecuta la busqueda global.

La plantilla `index.html` deja de estar vacia y pasa a mostrar:

- Caja unica de busqueda.
- Mensaje de error si la query tiene menos de 3 caracteres.
- Resultados agrupados por paciente/historia.
- El indicador `Historia #...` tambien es link directo a la historia clinica.
- Enlaces accionables a:
  - Edicion de paciente.
  - Historia clinica.
  - Estudios categorizados por tipo y fecha en formato compacto, por ejemplo `ECO 12/05/2026`.

La presentacion de acciones queda deliberadamente condensada: `PACIENTE`, `HISTORIA` y chips de estudios con tipo azul y fecha negra.

## Paso 7 - Estilo visual

Se agregaron estilos en `main/static/main/css/style.css` para que la primera pantalla funcione como buscador principal del sistema, manteniendo la paleta y lenguaje visual existente.
