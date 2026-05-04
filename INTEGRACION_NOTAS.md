# Notas de Integracion

## Alcance permanente
- `/home/eze/omar-codex` y `/home/eze/omar` son dos repositorios de un mismo negocio.
- Cualquier análisis o cambio debe considerar ambos repos como un contexto único y asociado de forma permanente.

## Docker / Deploy
- Imagen app: `hhcc_app:latest`
- Imagen DB: `nuevo_cardioprieto:latest`
- Nginx reverse proxy: puerto 80 -> app:8000
- `ALLOWED_HOSTS = ["*"]` en `hhcc/hhcc/settings.py`.
- `Dockerfile` incluye dependencias para PDF (pango/cairo) y `tzdata`.

## Restore de datos
- Dump local usado para QA: `deploy/cardioprieto_dump.sql`.
- `deploy/start_fresh.sh` restaura DB si existe el dump.

## Migracion DB (viejo -> nuevo)
- Carpeta: `migracion_db/`
- Docs principales: `migracion_db/MIGRACION_DB.md`
- Scripts: `00_dump_old.sh`, `01_load_old.sh`, `02_migrar.sql`
- Ubicacion sugerida del dump legacy: `migracion_db/data/` (ej. `cardioprieto_old_YYYYMMDD.sql`)
- Regla operativa: antes de re-migrar datos legacy, limpiar datos de negocio migrables pero **no** migrar ni dejar mandando al legacy sobre el circuito de usuarios/auth del sistema nuevo.
- Dump definitivo usado para la carga final en `3307`: `migracion_db/data/cardioprieto_old_20260415.sql`
- Carga final ejecutada preservando `auth_*` y `django_*` del sistema nuevo.

## Comentarios
- En migracion se consolidan comentarios por historia+tipo en `comentarios_visitas`.
- Tipo `Visita` -> `EVOL`, `Indicaciones` -> `INDIC`.

## Signos vitales
- No hay UNIQUE por (`historia_id`, `fecha`).
- La UI toma **solo el primero** de cada fecha.
- Si hay multiples por dia, quedan guardados pero solo uno se ve.
