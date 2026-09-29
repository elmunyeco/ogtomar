# API de busqueda por trigramas para clientes externos

Fecha de referencia: 2026-06-07.

## Objetivo

Exponer la busqueda identificatoria por trigramas de `~/omar` para que otra aplicacion, por ejemplo `~/omar-solo`, pueda buscar pacientes e historias con el mismo criterio, sin conectarse directo a la base MySQL y sin duplicar el algoritmo.

La fuente canonica sigue siendo `~/omar`:

```text
Cliente externo
  -> backend propio del cliente
  -> API de busqueda Django en omar
  -> main.global_search
  -> MySQL / indice materializado de trigramas
```

No se recomienda:

```text
Cliente externo -> MySQL directo
```

porque acopla el cliente al esquema clinico, distribuye credenciales de base, duplica ranking y dificulta auditoria.

## Endpoint propuesto

```text
GET /api/v1/search/pacientes/?q=berg&page=1&limit=10
```

Parametros:

- `q`: texto buscado. Minimo real: 3 caracteres utiles, igual que la busqueda global actual.
- `page`: pagina solicitada. Default: `1`.
- `limit`: cantidad por pagina. Default: `10`; maximo configurable con `SEARCH_API_MAX_LIMIT`.

Respuesta esperada:

```json
{
  "query": "berg",
  "page": 1,
  "limit": 10,
  "has_next": false,
  "has_previous": false,
  "results": [
    {
      "paciente_id": 123,
      "historia_id": 456,
      "title": "Bergonzi, Ezequiel",
      "subtitle": "Doc 23101065 - Paciente #123 - Historia #456",
      "score": 9420
    }
  ]
}
```

La respuesta debe ser deliberadamente minima. No devolver telefono, mail, direccion, obra social, comentarios, indicaciones ni texto clinico salvo que se defina una necesidad explicita y permisos especificos.

## Implementacion en Django

No hace falta Django REST Framework para esta primera version. La aplicacion ya tiene Django puro y el servicio de busqueda vive en `main/global_search.py`.

Archivos propuestos:

- `hhcc/main/api_auth.py`
- `hhcc/main/views.py`
- `hhcc/main/urls.py`
- `hhcc/hhcc/settings.py`

### `hhcc/main/api_auth.py`

Crear un decorador `require_search_api_token`.

Responsabilidades:

- Leer `Authorization: Bearer <token>`.
- Comparar contra `settings.SEARCH_API_TOKEN`.
- Usar `secrets.compare_digest` para evitar comparaciones inseguras.
- Rechazar con `401` si falta o no coincide.

Librerias:

```python
import secrets
from functools import wraps

from django.conf import settings
from django.http import JsonResponse
```

### `hhcc/main/views.py`

Agregar `global_search_api(request)`.

Responsabilidades:

- Aceptar solo `GET`.
- Leer `q`, `page`, `limit`.
- Limitar `limit` contra `settings.SEARCH_API_MAX_LIMIT`.
- Llamar a `global_search(q, page=page, per_page=limit)`.
- Serializar un JSON minimo.
- Registrar auditoria o log operativo.

Librerias:

```python
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .api_auth import require_search_api_token
from .global_search import global_search
```

### `hhcc/main/urls.py`

Agregar:

```python
path("api/v1/search/pacientes/", views.global_search_api, name="api_global_search")
```

### `hhcc/hhcc/settings.py`

Agregar variables por entorno:

```python
SEARCH_API_TOKEN = os.getenv("SEARCH_API_TOKEN", "")
SEARCH_API_MAX_LIMIT = int(os.getenv("SEARCH_API_MAX_LIMIT", "10"))
```

El token debe ser largo, aleatorio y distinto del `SECRET_KEY` de Django.

## Seguridad

La llamada debe ser backend a backend:

```text
navegador -> omar-solo Node -> omar Django
```

No exponer el token al navegador.

### Con HTTPS

Es el modo correcto para produccion si el trafico cruza redes no controladas.

Capas recomendadas:

- HTTPS.
- `Authorization: Bearer <SEARCH_API_TOKEN>`.
- Rate limit.
- Auditoria.
- Respuesta minima.
- CORS cerrado o irrelevante, porque no lo consume el navegador.

### Sin HTTPS

Se acepta solo como modo controlado de QA o red privada.

Condiciones minimas:

- El endpoint no debe quedar abierto a Internet.
- Usar red Docker privada, VPN, firewall o allowlist de IP.
- Token largo en `SEARCH_API_TOKEN`.
- Rate limit en nginx o aplicacion.
- Auditoria de cada consulta.
- Timeout corto desde el cliente.

Si el endpoint va a estar accesible desde Internet, no usar HTTP plano.

## Auditoria

Primera version aceptable: log estructurado.

Campos minimos:

- timestamp;
- cliente (`X-Client`, por ejemplo `omar-solo`);
- usuario remoto (`X-User`, si el cliente lo informa);
- query;
- pagina;
- limite;
- cantidad de resultados;
- IP remota.

Version posterior: modelo `SearchApiAudit`.

Campos propuestos:

```python
class SearchApiAudit(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    client = models.CharField(max_length=80)
    user_ref = models.CharField(max_length=120, blank=True)
    query = models.CharField(max_length=255)
    page = models.IntegerField(default=1)
    limit = models.IntegerField(default=10)
    result_count = models.IntegerField(default=0)
    remote_addr = models.GenericIPAddressField(null=True, blank=True)
```

## Contrato para clientes

Headers requeridos:

```text
Authorization: Bearer <SEARCH_API_TOKEN>
X-Client: omar-solo
X-User: <usuario autenticado en el cliente>
```

`X-User` no autentica por si mismo. Solo sirve para auditoria. La autenticacion real es el token servidor-a-servidor.

## Integracion prevista con omar-solo

`omar-solo` no debe llamar a `omar` desde el navegador. Debe agregar una ruta propia protegida por su JWT local:

```text
GET /api/search/patients?q=berg&page=1&limit=10
```

Esa ruta llama desde Node al API de `omar` usando `fetch` nativo de Node 18.

Variables esperadas en `omar-solo`:

```text
OMAR_SEARCH_BASE_URL=http://hhcc_app:8000
OMAR_SEARCH_TOKEN=<mismo valor que SEARCH_API_TOKEN>
OMAR_SEARCH_TIMEOUT_MS=5000
```

En QA con nginx compartido, puede apuntar a una URL interna del stack si ambos contenedores comparten red. Si corre en otra maquina, debe apuntar a una direccion privada, VPN o endpoint protegido por firewall.

## Pendientes antes de implementar

- Definir si la primera version devuelve `score` o lo omite.
- Definir si se devuelven URLs internas de `omar`; por defecto no.
- Definir politica de acceso HTTP sin TLS en QA.
- Crear token y guardarlo solo en variables de entorno.
- Agregar pruebas de autenticacion, query corta, respuesta minima y limite maximo.
