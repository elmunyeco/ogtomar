# MAPA TECNICO

## Proposito
- Este archivo describe el sistema real que hoy se debe mantener, discutir y programar.
- La referencia operativa principal es `~/omar`.
- `~/omar-codex` queda como repositorio de contexto, reportes, evidencia y memoria de integracion, pero no como centro de ejecucion.
- Leer este archivo al inicio de cada sesion antes de tocar arquitectura o codigo.

## Regla de trabajo
- El sistema productivo/local operativo vive en `~/omar`.
- Las decisiones de arquitectura y los cambios de codigo deben partir de la implementacion real de `~/omar/hhcc`.
- Si hace falta contexto historico, validacion de criterios o evidencia visual/funcional, consultar `~/omar-codex`.
- No reabrir decisiones ya consolidadas sin una razon tecnica o funcional concreta.

## Resumen del sistema
- Es una aplicacion Django monolitica orientada a consultorio cardiologico.
- El dominio principal es la historia clinica del paciente.
- El sistema maneja:
  - pacientes
  - historias clinicas
  - evolucion clinica diaria
  - signos vitales
  - condiciones medicas
  - indicaciones/medicacion
  - solicitudes
  - estudios cardiologicos
  - impresion PDF
- La aplicacion usa MySQL como base principal y Docker para deploy/restore reproducible.

## Repositorio canonico
- Repo operativo: `~/omar`
- Proyecto Django: `~/omar/hhcc`
- Settings principales: [hhcc/settings.py](/home/eze/omar/hhcc/hhcc/settings.py:1)
- URLs globales: [hhcc/urls.py](/home/eze/omar/hhcc/hhcc/urls.py:1)

## Estructura de apps

### 1. `main`
- Es el nucleo del sistema.
- Modela pacientes, historias clinicas, signos vitales, comentarios/evolucion, indicaciones y condiciones medicas.
- Tambien contiene:
  - autenticacion minima
  - busquedas y listados
  - historia clinica principal
  - solicitudes
  - impresion de historia clinica e indicaciones
  - listado unificado de estudios por historia

Archivos clave:
- [main/models.py](/home/eze/omar/hhcc/main/models.py:1)
- [main/views.py](/home/eze/omar/hhcc/main/views.py:1)
- [main/urls.py](/home/eze/omar/hhcc/main/urls.py:1)
- [main/templates/detalle_historia_con_historial_2.html](/home/eze/omar/hhcc/main/templates/detalle_historia_con_historial_2.html:1)
- [main/templates/listar_estudios_historia.html](/home/eze/omar/hhcc/main/templates/listar_estudios_historia.html:1)
- [main/templates/historias_estudios_nuevo.html](/home/eze/omar/hhcc/main/templates/historias_estudios_nuevo.html:1)
- [main/templates/ordenes_medicas.html](/home/eze/omar/hhcc/main/templates/ordenes_medicas.html:1)

### 2. `ecocardiograma`
- Modulo de estudio mas complejo.
- Tiene modelo principal del estudio, segmentos y conclusion.
- Conserva una doble capa:
  - flujo nuevo explicito por historia y estudio
  - endpoints legacy de guardado parcial por compatibilidad

Archivos clave:
- [ecocardiograma/models.py](/home/eze/omar/hhcc/ecocardiograma/models.py:1)
- [ecocardiograma/views.py](/home/eze/omar/hhcc/ecocardiograma/views.py:1)
- [ecocardiograma/urls.py](/home/eze/omar/hhcc/ecocardiograma/urls.py:1)
- [ecocardiograma/templates/ecocardiograma/eco_form.html](/home/eze/omar/hhcc/ecocardiograma/templates/ecocardiograma/eco_form.html:1)

### 3. `carotidas`
- Estudio de doppler de vasos del cuello / QIMT.
- Modelo con codificaciones legacy y funciones que las traducen a texto clinico legible.

Archivos clave:
- [carotidas/models.py](/home/eze/omar/hhcc/carotidas/models.py:1)
- [carotidas/views.py](/home/eze/omar/hhcc/carotidas/views.py:1)
- [carotidas/forms.py](/home/eze/omar/hhcc/carotidas/forms.py:1)

### 4. `ecostress`
- Estudio de ecostress cardiaco.
- Mantiene defaults clinicos para ayudar a la carga del estudio.

Archivos clave:
- [ecostress/models.py](/home/eze/omar/hhcc/ecostress/models.py:1)
- [ecostress/views.py](/home/eze/omar/hhcc/ecostress/views.py:1)
- [ecostress/forms.py](/home/eze/omar/hhcc/ecostress/forms.py:1)

### 5. `mmii`
- Doppler arterial de miembros inferiores.
- Surge del reemplazo/renombre del legado `doppler`.

Archivos clave:
- [mmii/models.py](/home/eze/omar/hhcc/mmii/models.py:1)
- [mmii/views.py](/home/eze/omar/hhcc/mmii/views.py:1)
- [mmii/forms.py](/home/eze/omar/hhcc/mmii/forms.py:1)

### 6. `earthbox`
- No pertenece al flujo clinico real.
- Es residual / experimental.
- Hoy no esta montada en las URLs globales y no debe condicionar decisiones de arquitectura.

Archivos:
- [earthbox/views.py](/home/eze/omar/hhcc/earthbox/views.py:1)
- [earthbox/urls.py](/home/eze/omar/hhcc/earthbox/urls.py:1)

## Modelo conceptual del negocio

### Paciente
- Entidad administrativa y de identificacion.
- Vive en `main.Paciente`.
- Tiene documento, nombre, fecha de nacimiento, sexo, contacto, obra social y otros datos de ficha.
- Al crear un paciente, se crea automaticamente una historia clinica por signal.

Referencias:
- [main/models.py](/home/eze/omar/hhcc/main/models.py:19)
- [main/signals.py](/home/eze/omar/hhcc/main/signals.py:1)

### Historia Clinica
- Es el eje real del sistema.
- Todo lo clinico se cuelga de una `HistoriaClinica`.
- El usuario puede llegar desde pacientes, pero el trabajo medico ocurre desde la historia.

Referencias:
- [main/models.py](/home/eze/omar/hhcc/main/models.py:91)
- [main/views.py](/home/eze/omar/hhcc/main/views.py:1381)

### Visita clinica diaria
- No existe una tabla `visita` formal.
- La visita diaria se reconstruye por fecha a partir de:
  - `ComentariosVisitas`
  - `SignosVitales`
  - `IndicacionesVisitas`
- El sistema trata la fecha como unidad funcional de evolucion.

### Regla funcional fuerte
- Una visita por dia.
- Si ya existe una evolucion del dia, se actualiza.
- Si ya existe un registro de signos vitales del dia, se actualiza el primero visible.
- La precision clinica aceptada para comentarios es a nivel dia, no hora.

Esto esta implementado especialmente en:
- [main/views.py](/home/eze/omar/hhcc/main/views.py:959)

## Flujo principal del usuario

### 1. Acceso
- Login clasico Django.
- Logout.
- Cambio de nombre del usuario autenticado.

Referencias:
- [main/urls.py](/home/eze/omar/hhcc/main/urls.py:6)
- [main/views.py](/home/eze/omar/hhcc/main/views.py:20)
- [main/views.py](/home/eze/omar/hhcc/main/views.py:1020)

### 2. Pacientes
- Listado con busqueda por documento, nombre o apellido.
- Alta de paciente.
- Edicion de paciente.
- Eliminacion bloqueada si tiene historias asociadas.
- Desde el listado se puede abrir la historia principal del paciente.

Referencias:
- [main/views.py](/home/eze/omar/hhcc/main/views.py:46)
- [main/views.py](/home/eze/omar/hhcc/main/views.py:317)
- [main/views.py](/home/eze/omar/hhcc/main/views.py:337)
- [main/views.py](/home/eze/omar/hhcc/main/views.py:370)
- [main/templates/listar_buscar_pacientes.html](/home/eze/omar/hhcc/main/templates/listar_buscar_pacientes.html:1)

### 3. Historias clinicas
- Listado con busqueda por id, documento, nombre o apellido.
- Desde ahi se abre:
  - la historia clinica
  - el listado unificado de estudios
- El listado ya anota conteos por tipo de estudio.

Referencias:
- [main/views.py](/home/eze/omar/hhcc/main/views.py:106)
- [main/templates/listar_buscar_historias_2.html](/home/eze/omar/hhcc/main/templates/listar_buscar_historias_2.html:1)

### 4. Historia clinica
- Pantalla central del sistema.
- Permite:
  - editar signos vitales del dia
  - editar condiciones medicas activas
  - editar evolucion/comentarios del dia
  - navegar a medicacion
  - navegar a solicitudes
  - navegar al listado de estudios
  - iniciar un nuevo estudio
  - imprimir historia clinica
- Debajo, presenta el historial de evolucion reconstruido por fecha.

Referencias:
- [main/views.py](/home/eze/omar/hhcc/main/views.py:1381)
- [main/templates/detalle_historia_con_historial_2.html](/home/eze/omar/hhcc/main/templates/detalle_historia_con_historial_2.html:1)

### 5. Indicaciones / medicacion
- Modulo separado de la historia, pero dependiente de una historia clinica.
- Tiene:
  - listado
  - alta
  - edicion
  - borrado logico
  - comentario de indicaciones
  - impresion PDF
- En datos, las indicaciones usan `IndicacionesVisitas`.
- El comentario de indicaciones vive en `ComentariosVisitas` con tipo `INDIC`.

Referencias:
- [main/views.py](/home/eze/omar/hhcc/main/views.py:1036)
- [main/views.py](/home/eze/omar/hhcc/main/views.py:1120)
- [main/views.py](/home/eze/omar/hhcc/main/views.py:1146)
- [main/views.py](/home/eze/omar/hhcc/main/views.py:1174)
- [main/views.py](/home/eze/omar/hhcc/main/views.py:1190)
- [main/views.py](/home/eze/omar/hhcc/main/views.py:1215)

### 6. Solicitudes
- El nombre funcional visible es `Solicitudes`.
- La ruta viva es `ordenes_medicas`.
- El template operativo actual es [ordenes_medicas.html](/home/eze/omar/hhcc/main/templates/ordenes_medicas.html:1).
- La generacion PDF buena hoy se hace con `generar_pdf_orden`.
- `descargarPDFSolicitudes` sigue existiendo en codigo pero es parte de la capa vieja.

Referencias:
- [main/views.py](/home/eze/omar/hhcc/main/views.py:390)
- [main/views.py](/home/eze/omar/hhcc/main/views.py:533)
- [main/views.py](/home/eze/omar/hhcc/main/views.py:728)

### 7. Estudios
- Cada estudio cuelga de una historia clinica.
- El sistema ya tiene un listado unificado por historia.
- Desde ahi se puede:
  - ver/editar estudio
  - imprimir PDF
  - iniciar nuevo estudio
- Hay cuatro tipos activos:
  - ecocardiograma
  - ecostress
  - carotidas
  - mmii

Referencias:
- [main/views.py](/home/eze/omar/hhcc/main/views.py:200)
- [main/views.py](/home/eze/omar/hhcc/main/views.py:1570)
- [main/templates/listar_estudios_historia.html](/home/eze/omar/hhcc/main/templates/listar_estudios_historia.html:1)
- [main/templates/historias_estudios_nuevo.html](/home/eze/omar/hhcc/main/templates/historias_estudios_nuevo.html:1)

## Contrato de datos principal

### `Paciente`
- Tabla: `pacientes`
- Clave funcional: documento + tipo de documento
- Tiene `fechaAlta`
- Tiene sexo `H/M`, no `M/F`

### `HistoriaClinica`
- Tabla: `historias_clinicas`
- FK a `Paciente`
- Tiene `fechaAlta`

### `CondicionMedica` / `CondicionMedicaHistoria`
- Tablas:
  - `condiciones_medicas`
  - `condiciones_medicas_historias`
- Las condiciones activas se reemplazan en bloque al guardar la historia.

### `SignosVitales`
- Tabla: `signos_vitales`
- No hay unique fuerte por `historia + fecha`
- La UI toma el primer registro visible por fecha
- Esto explica el riesgo de duplicados silenciosos si no se cuida la logica de guardado

### `ComentariosVisitas`
- Tabla: `comentarios_visitas`
- Tipos relevantes:
  - `EVOL`
  - `INDIC`
- Se usa `DateTimeField`, pero funcionalmente el sistema agrupa por dia

### `IndicacionesVisitas`
- Tabla: `indicaciones_visitas`
- Maneja esquema de horarios:
  - `ochoHoras`
  - `doceHoras`
  - `dieciochoHoras`
  - `veintiunaHoras`
- Borrado logico por `eliminado`

## Arquitectura de navegacion

### Centro de navegacion
- La pantalla centro es `detalle_historia_con_historial`.
- Pacientes y listados son puertas de entrada.
- El trabajo medico real se hace sobre una historia concreta.

### Principio operativo
- El usuario busca paciente o historia.
- Abre historia clinica.
- Desde esa historia:
  - registra evolucion del dia
  - toca signos y condiciones
  - entra a medicacion
  - entra a solicitudes
  - consulta o crea estudios
- Toda accion razonable deberia volver a ese contexto o a su listado de estudios asociado.

### Estado actual de esa navegacion
- La historia ya funciona como hub.
- El listado de estudios por historia ya esta consolidado.
- Los estudios ya exponen rutas explicitas `estudio/<id>/`.
- Todavia quedan algunas huellas de compatibilidad legacy, pero el flujo central ya esta bastante definido.

## Capa de estudios

### Patron comun
- Entrada por historia:
  - `/<modulo>/<historia_id>/`
  - `/<modulo>/<historia_id>/nuevo/`
- Edicion explicita:
  - `/<modulo>/estudio/<estudio_id>/`
- Impresion:
  - endpoint propio PDF por modulo
- Compatibilidad hacia atras:
  - si llega `action=recuperar&estudio=...`, se redirige a la ruta explicita de edicion

Esto ya existe en:
- [ecocardiograma/views.py](/home/eze/omar/hhcc/ecocardiograma/views.py:176)
- [carotidas/views.py](/home/eze/omar/hhcc/carotidas/views.py:17)
- [ecostress/views.py](/home/eze/omar/hhcc/ecostress/views.py:37)
- [mmii/views.py](/home/eze/omar/hhcc/mmii/views.py:26)

### Situacion especifica de ecocardiograma
- Es el modulo mas complejo y mas hibrido.
- Tiene:
  - guardado completo nuevo por AJAX
  - endpoints legacy parciales
  - logica de render y calculos en frontend
  - segmentos cardiacos
  - conclusion estructurada + texto libre
- Cualquier refactor de este modulo requiere mas cuidado que los otros tres.

## UI real

### Base
- [base.html](/home/eze/omar/hhcc/main/templates/base.html:1)
- Usa `style.css` propio y además Alpine/Tailwind por CDN.
- El header se renderiza solo si el usuario esta autenticado.

### Header
- [components/header.html](/home/eze/omar/hhcc/main/templates/components/header.html:1)
- Menu principal real:
  - Pacientes
  - Historias
- No expone estudios como menu global.
- No expone `earthbox`.

### Historia clinica
- Visualmente es la pantalla mas importante.
- Tiene acciones directas arriba:
  - Estudios
  - Nuevo estudio
  - Medicacion
  - Solicitudes
  - Imprimir
- Tiene barra inferior fija para cancelar / guardar cambios.

### Solicitudes
- Visualmente es una pantalla de seleccion de practicas agrupadas.
- Genera uno o varios PDFs segun grupo y tambien contempla `otros estudios`.

## Impresion y PDFs
- El sistema imprime:
  - historia clinica
  - indicaciones
  - solicitudes
  - cada estudio
- La mayor parte de los PDFs nuevos usa WeasyPrint.
- `descargarPDFSolicitudes` usa ReportLab y pertenece a una etapa mas vieja.
- Los estudios y la historia usan `print_base.html` y `print.css` como infraestructura visual compartida.

Archivos clave:
- [main/templates/print_base.html](/home/eze/omar/hhcc/main/templates/print_base.html:1)
- [main/static/main/css/print.css](/home/eze/omar/hhcc/main/static/main/css/print.css:1)

## Infraestructura y despliegue

### Runtime local / deploy
- Base MariaDB: contenedor `nuevo_cardioprieto`
- App Django: contenedor `hhcc_app`
- Proxy: nginx

Archivos:
- [docker-compose.yml](/home/eze/omar/docker-compose.yml:1)
- [Dockerfile](/home/eze/omar/Dockerfile:1)
- [docker-entrypoint.sh](/home/eze/omar/docker-entrypoint.sh:1)

### Restore reproducible
- El mecanismo canónico es `deploy/start_fresh.sh`
- Si existe `deploy/cardioprieto_dump.sql`, el script:
  - levanta DB
  - restaura dump
  - arranca app sin migraciones de startup

Referencia:
- [deploy/start_fresh.sh](/home/eze/omar/deploy/start_fresh.sh:1)

## Base de datos y migracion

### Base activa
- MySQL / MariaDB
- Host habitual local: `127.0.0.1`
- Puerto: `3307`
- DB: `cardioprieto`

### Fuente legacy
- Existio/puede existir una instancia vieja en `3308`
- La migracion al esquema nuevo se hace en `~/omar/migracion_db`

Archivos clave:
- [migracion_db/MIGRACION_DB.md](/home/eze/omar/migracion_db/MIGRACION_DB.md:1)
- [migracion_db/02_migrar.sql](/home/eze/omar/migracion_db/02_migrar.sql:1)
- [migracion_db/03_migrar_pendientes.sql](/home/eze/omar/migracion_db/03_migrar_pendientes.sql:1)
- [scripts_migraciones/migrate_estudios_3308_to_3307.py](/home/eze/omar/scripts_migraciones/migrate_estudios_3308_to_3307.py:1)

### Regla clave de migracion
- El legado no manda sobre usuarios del sistema nuevo.
- `auth_*` y `django_*` no se deben reimportar desde legacy.
- La migracion de negocio reconstruye:
  - pacientes
  - historias
  - condiciones
  - indicaciones
  - signos
  - comentarios
  - estudios

## Estado tecnico actual

### Lo que ya esta consolidado
- `~/omar` es el sistema correcto para programar.
- Historia clinica como centro del flujo.
- Listado unificado de estudios por historia.
- Rutas explicitas de edicion de estudios.
- Modulos de estudios ya integrados al monolito.
- Docker/deploy/reload reproducible.
- Regla funcional de visita diaria ya absorbida en el nucleo.

### Lo que sigue mezclado
- `main/views.py` concentra demasiado codigo y mezcla dominios.
- Ecocardiograma conserva compatibilidad legacy interna.
- Sigue existiendo `descargarPDFSolicitudes`.
- Quedan restos archivados y referencias historicas a templates viejos.
- El proyecto mezcla componentes modernos con residuos heredados del proceso de integracion.

### Lo que hoy es residual
- `earthbox`
- `_archive_templates`
- `_archive_pre_integracion_20260403`
- referencias viejas a `ordenes_pedicas`
- endpoints o templates viejos asociados a `descargarPDFSolicitudes`

## Deuda tecnica real

### 1. `main/views.py` demasiado grande
- Contiene autenticacion, CRUD, historia, indicaciones, solicitudes, impresion y logica JSON en un solo archivo.
- Es el principal cuello de mantenimiento.

### 2. Compatibilidad legacy no aislada
- En especial en ecocardiograma.
- El costo no es solo estético: complica razonamiento, pruebas y cambios de contrato.

### 3. Modelo de visita implicito
- La visita clinica existe por composicion de fecha, no como entidad propia.
- Esto es funcionalmente valido hoy, pero explica varias rarezas del codigo.

### 4. Restos de integracion y archivo
- Hay bastante material viejo bien archivado, pero sigue generando ruido conceptual.

### 5. Inconsistencias menores de infraestructura
- En runtime activo se usa CDN para Alpine/Tailwind en `base.html`, aunque existen decisiones/documentos previos con assets locales.
- No es un blocker funcional, pero es una divergencia tecnica a tener presente.

## Criterios que no conviene olvidar
- La unidad de trabajo clinica es la historia, no el paciente suelto.
- La unidad de evolucion funcional es el dia.
- El sistema real a tocar es `~/omar`.
- `~/omar-codex` se consulta para:
  - evidencia
  - reportes
  - decisiones historicas
  - contexto de integracion
- No tomar decisiones guiadas por codigo archivado salvo que se reintroduzca conscientemente.

## Orden recomendado para futuras discusiones de arquitectura
1. Mantener fijo el modelo de navegacion: historia clinica como hub.
2. Separar tecnicamente el nucleo `main` por dominios sin romper rutas.
3. Aislar compatibilidad legacy de eco.
4. Eliminar o encapsular piezas residuales muertas.
5. Recién después discutir refactors más profundos de modelo o frontend.

## Lectura minima al inicio de cada sesion
- [MAPA_TECNICO.md](/home/eze/omar/MAPA_TECNICO.md:1)
- [INTEGRACION_NOTAS.md](/home/eze/omar/INTEGRACION_NOTAS.md:1)
- Si la tarea toca flujo o decisiones previas:
  - [PENDIENTES_FLUJO_SISTEMA_2026-04-16.md](/home/eze/omar/PENDIENTES_FLUJO_SISTEMA_2026-04-16.md:1)
  - [INFORME_FLUJO_SISTEMA_2026-04-16.md](/home/eze/omar/INFORME_FLUJO_SISTEMA_2026-04-16.md:1)
- Si la tarea toca integración o historia técnica:
  - [CONTEXTO.md](/home/eze/omar-codex/CONTEXTO.md:1)
  - [DOCUMENTACION_INTEGRACION.md](/home/eze/omar-codex/DOCUMENTACION_INTEGRACION.md:1)
  - [SESSION_NOTES.md](/home/eze/omar-codex/Scrap_cardioprietohc/SESSION_NOTES.md:1)

## Conclusión operativa
- El sistema no es `omar-codex`.
- El sistema es `~/omar`.
- `omar-codex` es memoria técnica y evidencia.
- Las discusiones de arquitectura futuras deben partir de la implementación real de `~/omar`, especialmente de `main`, de la historia clínica como pantalla central y de los estudios como módulos ya integrados sobre esa base.
