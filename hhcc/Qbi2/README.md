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
