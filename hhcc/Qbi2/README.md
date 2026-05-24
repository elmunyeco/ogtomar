# Qbi2 - Vademecum

Wrapper interno para consumir catalogos de Qbi2/RCTA desde Django sin exponer credenciales al frontend.

## Endpoints internos

- `GET /qbi2/health/`
- `GET /qbi2/api/vademecum/buscar/?q=atorva`
- `GET /qbi2/api/vademecum/buscar/?q=atorva&page=2`
- `GET /qbi2/api/vademecum/buscar/?q=atorva&raw=1`

Todos los endpoints quedan protegidos con `login_required`.

## Configuracion

Variables de entorno disponibles:

```text
QBI2_BASE_URL=https://apirecipe.hml.qbitos.com/
QBI2_BEARER_TOKEN=
QBI2_CLIENT_APP_ID=563
QBI2_TIMEOUT_SECONDS=15
QBI2_AUTH_MODE=auto
QBI2_VADEMECUM_PATH=/apirecipe/GetMedicamento/{search}
QBI2_VADEMECUM_PAGE_PARAM=numeroPagina
QBI2_CLIENT_APP_ID_PARAM=clienteAppId
QBI2_INCLUDE_CLIENT_APP_ID_IN_VADEMECUM=1
QBI2_VADEMECUM_MIN_QUERY_LENGTH=2
```

`QBI2_AUTH_MODE=auto` envia `Authorization: Bearer ...` solo si `QBI2_BEARER_TOKEN` esta configurado. Esto permite probar si algun endpoint de catalogo es publico sin cambiar codigo. Usar `required` cuando soporte confirme que el vademecum exige token.

El Swagger de homologacion confirma que `GetMedicamento` recibe el texto de busqueda en el path y exige `numeroPagina` + `clienteAppId`.

Nota operativa 2026-05-23:

- El vademecum de Innovamed/Qbi2 responde `401` con `WWW-Authenticate: Bearer` cuando no recibe token.
- Si el wrapper devuelve `provider_status=401`, el endpoint probablemente esta vivo: revisar primero que `QBI2_BEARER_TOKEN` este llegando al proceso Django.
- En desarrollo local, `settings.py` carga `/home/eze/omar/.env.qbi2` automaticamente.
- En Docker, el archivo `.env.qbi2` debe entrar como `env_file`; si no, el contenedor no ve el Bearer aunque el archivo exista en el host.
- Para trabajar localmente sobre la aplicacion, dejar Docker solo para la base `nuevo_cardioprieto` y levantar Django con `runserver`; reconstruir imagenes de app/nginx recien al preparar QA.

## PoC de receta HML

Comando seguro por defecto, solo imprime payload:

```bash
python manage.py qbi2_receta_poc
```

Emitir receta real en Qbi2 HML:

```bash
QBI2_TIMEOUT_SECONDS=90 python manage.py qbi2_receta_poc --send
```

Imprimir respuesta completa del proveedor:

```bash
QBI2_TIMEOUT_SECONDS=90 python manage.py qbi2_receta_poc --send --raw
```

La PoC usa datos ficticios y `regNo=34959` por defecto:

```text
LOTRIAL - enalapril - 10 mg comp.x 30
```

El diagnostico puede ser texto libre o codigo CIE-10 segun Swagger (`RecetaRequestDto.diagnostico`). La prueba HML exitosa devolvio:

```text
status=OK
idReceta
s3Link
verificador
idTransaccion
fechavencimiento
errores=[]
```

Qbi2 completo automaticamente cobertura "No posee" para el paciente ficticio cuando no se envio cobertura.
