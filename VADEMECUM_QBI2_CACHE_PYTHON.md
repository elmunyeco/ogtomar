# Cache Python persistente para vademecum QBI2 / Innovamed

Documento de diseno para la cache persistente del vademecum QBI2 / Innovamed.
La implementacion toma ideas de la cache conceptual en Go de `~/omar/cache`
(TTL, get/set/delete, stats y copias defensivas), pero la cache real vive en
MySQL.

## Regla central

```text
La cache sirve para encontrar candidatos.
QBI2 vivo sirve para confirmar antes de emitir.
```

No se cachea la emision de recetas. Tampoco se acepta cache como validacion
final de un medicamento seleccionado para recetar.

## Ubicacion

La cache es una app Django independiente:

```text
hhcc/Qbi2/
  cache.py
  vademecum_cache.py
  models.py
  migrations/
```

Flujo de busqueda:

```text
UI paciente / UI medico
  -> endpoint Django de busqueda/autocomplete
    -> CachedVademecumService
      -> MySQLCache
      -> tabla qbi2_cache_entries
      -> VademecumService
        -> Qbi2Client
          -> QBI2 / Innovamed
```

Flujo de receta:

```text
PrescriptionService
  -> valida medicamento seleccionado contra QBI2 vivo
  -> emite receta solo si valida
```

## Por que MySQL

Se usa MySQL como unico backend para desarrollo, testing y produccion.

Motivos:

- ya forma parte de la infraestructura
- sobrevive reinicios del proceso Python
- comparte cache entre workers Django
- evita agregar SQLite, Redis u otro punto de falla
- permite inspeccion manual de claves, fechas, errores y locks
- permite leases con transacciones y `SELECT ... FOR UPDATE`

## Tabla

Modelo principal:

```text
Qbi2CacheEntry -> qbi2_cache_entries
```

Campos principales:

- `key_hash`: SHA-256 de la clave canonica; primary key
- `cache_key`: clave canonica completa
- `namespace`: por ahora `vademecum`
- `provider`: por ahora `qbi2`
- `endpoint`
- `cliente_app_id`
- `normalized_query`
- `page`
- `params_hash`
- `schema_version`
- `status`: `ok`, `empty`, etc.
- `value`: respuesta JSON cacheada
- `metadata`: metadata de diagnostico
- `fetched_at`
- `fresh_until`
- `stale_until`
- `refresh_locked_until`
- `refresh_token`
- `refresh_started_at`
- `last_refresh_error`

## API del backend

Modulo:

```text
hhcc/Qbi2/cache.py
```

Clase:

```python
class MySQLCache:
    def get(self, key: str, *, allow_stale: bool = False) -> CacheResult: ...
    def set(self, key: str, value: Any, fresh_ttl: timedelta, *, stale_ttl: timedelta, metadata: dict | None = None) -> None: ...
    def delete(self, key: str) -> bool: ...
    def clear(self, *, namespace: str | None = None) -> int: ...
    def stats(self, *, namespace: str | None = None) -> CacheStats: ...
    def try_acquire_refresh_lease(self, key: str, *, lease_ttl: timedelta) -> RefreshLease: ...
    def release_refresh_lease(self, key: str, token: str | None, *, error: str | None = None) -> None: ...
```

`get()` devuelve copias defensivas para que el caller no pueda mutar el objeto
cacheado.

## Claves canonicas

La clave depende de:

- proveedor
- namespace
- version de schema
- `clienteAppId`
- base URL hasheada
- endpoint
- query normalizada
- pagina
- parametros extra ordenados y hasheados

Formato conceptual:

```text
qbi2:vademecum:v1:clienteAppId=563:base=...:path=/apirecipe/GetMedicamento:q=atorva:page=1:params=...
```

Normalizacion de query:

- trim
- lowercase
- espacios repetidos colapsados
- acentos removidos

## TTL

Politica actual:

- `fresh_ttl = 15 dias`
- `stale_ttl = 75 dias`
- vida total desde `fetched_at`: 90 dias
- no se cachean errores transitorios como nuevo valor bueno
- si QBI2 falla y existe stale, stale puede devolverse solo para busqueda
- validacion pre-receta siempre usa QBI2 vivo

Razonamiento:

- un medicamento usualmente no cambia de un dia al otro
- la busqueda/autocomplete tolera datos viejos si estan marcados como stale
- la emision de receta no tolera stale como verdad final

## Refresh lazy, no masivo

El TTL no dispara renovaciones globales.

Comportamiento:

```text
fresh hit:
  devolver cache

miss:
  consultar QBI2 y guardar en MySQL

stale hit:
  intentar tomar lease MySQL para esa clave

stale hit + lease obtenido:
  refrescar solo esa clave

stale hit + lease no obtenido:
  otro worker ya esta refrescando esa clave
  devolver stale

stale hit + QBI2 caido:
  liberar lease
  registrar last_refresh_error
  devolver stale solo para busqueda/autocomplete
```

Si vencen 50.000 claves, no se refrescan 50.000 claves. Se refresca solamente
la clave que alguien pidio.

## Autocomplete

Caso importante: una caja de texto sugiere medicamentos mientras se escribe.

Politica:

- minimo 2 caracteres
- debounce frontend recomendado: 150 a 250 ms
- cancelar requests anteriores si el usuario sigue tipeando
- cachear cada query normalizada por pagina
- `at`, `ato`, `ator` y `atorv` son claves distintas
- limitar autocomplete a pagina inicial salvo necesidad explicita

Esto reduce llamadas repetidas a QBI2 para prefijos frecuentes sin generar
renovaciones masivas.

## Revalidacion antes de emitir

Cuando paciente o medico selecciona un medicamento, guardar snapshot:

- `regNo`
- nombre comercial
- droga
- presentacion
- potencia
- forma farmaceutica
- via
- flags regulatorios/comerciales
- timestamp de seleccion
- fuente
- query que llevo a la seleccion

Ese snapshot sirve para auditoria y UX, no para saltear revalidacion.

Antes de emitir:

```text
snapshot seleccionado
  -> consultar QBI2 vivo por regNo si existe endpoint
  -> si no existe endpoint por regNo, buscar candidato compatible
  -> comparar campos criticos
  -> emitir solo si sigue vigente y compatible
```

Campos criticos:

- `regNo`
- presentacion
- potencia
- forma farmaceutica
- via
- psicofarmaco
- estupefaciente
- venta controlada
- requiere duplicado
- requiere aprobacion
- cobertura

Estados de validacion:

```text
valid
not_found
changed
ambiguous
provider_error
invalid_snapshot
```

`provider_error` nunca se convierte en exito por tener cache.

## Tests

La app `Qbi2` tiene tests Django que usan la base MySQL de test:

```bash
python manage.py test Qbi2
```

Casos cubiertos:

- persistencia set/get en MySQL
- copias defensivas al devolver valores
- stale por TTL
- leases por clave
- autocomplete desde 2 letras
- cache por prefijo normalizado
- refresh lazy de una sola clave
- validacion contra servicio vivo, no contra cache

## Resumen

La solucion queda asi:

- MySQL como unico backend
- TTL fresco de 15 dias
- stale adicional de 75 dias
- refresh lazy por clave
- lease por clave para evitar refresh duplicado
- cache solo para busqueda/autocomplete
- receta solo despues de revalidacion viva contra QBI2

## Nota operativa de despliegue

Las migraciones no deben correr como efecto colateral de levantar el proceso web.

Politica actual:

- `RUN_MIGRATIONS_ON_STARTUP=0` por defecto
- el contenedor web arranca sin ejecutar `manage.py migrate`
- las migraciones se ejecutan como paso explicito de release

Flujo recomendado antes de levantar una imagen nueva que trae migraciones:

```bash
cd /home/eze/omar/deploy
docker compose run --rm app python3 manage.py migrate
docker compose up -d app
```

Para esta app puntual, si se quiere limitar a QBI2:

```bash
cd /home/eze/omar/deploy
docker compose run --rm app python3 manage.py migrate Qbi2
docker compose up -d app
```

Arranque normal sin migrar:

```bash
cd /home/eze/omar/deploy
docker compose up -d app
```

Solo usar `RUN_MIGRATIONS_ON_STARTUP=1` como opt-in explicito y temporal.
