# Pendientes de Flujo del Sistema

Fecha: 2026-04-16

Repositorio: `/home/eze/omar`

Relacion con otros documentos:

- Diagnostico completo: `INFORME_FLUJO_SISTEMA_2026-04-16.md`
- Este archivo: backlog operativo y orden de ejecucion recomendado

## Objetivo

Transformar el informe de revision en una secuencia concreta de trabajo, con prioridades, criterios de aceptacion y notas de implementacion.

## Regla de trabajo

Tomar a la historia clinica como centro de navegacion del sistema.

Principio operativo:

- el usuario entra por paciente o historia
- el contexto principal pasa a ser la historia clinica
- desde ahi navega a estudios, indicaciones, ordenes e impresion
- toda accion secundaria debe volver al mismo contexto

## Backlog Priorizado

### Bloque 1. Estabilizacion inmediata

#### 1. Corregir redirects legacy a `detalle_historia`

Estado: resuelto en `refactor/flujo-clinico-integral`

Archivos a revisar:

- `hhcc/main/views.py`

Trabajo esperado:

- reemplazar redirects a rutas que ya no existen
- verificar si queda algun nombre de URL legacy en `views.py`
- asegurar que toda accion relacionada con historia vuelva a `detalle_historia_con_historial`

Criterio de aceptacion:

- no quedan referencias activas a `detalle_historia`
- actualizar condiciones y guardar signos vitales vuelven correctamente a la historia clinica

#### 2. Unificar comportamiento de "guardar estudio"

Estado: resuelto en `refactor/flujo-clinico-integral`

Archivos a revisar:

- `hhcc/mmii/views.py`
- `hhcc/ecostress/views.py`
- `hhcc/carotidas/views.py`
- `hhcc/ecocardiograma/views.py`

Trabajo esperado:

- definir una regla unica despues de guardar
- aplicar esa regla a todos los modulos de estudios

Recomendacion:

- guardar y volver al estudio actual o al listado de estudios de la historia
- no expulsar al listado general de historias

Criterio de aceptacion:

- MMII, Ecostress, Carotidas y Ecocardiograma reaccionan igual despues de guardar

#### 3. Corregir todos los botones "Volver" en estudios

Estado: resuelto en `refactor/flujo-clinico-integral`

Archivos a revisar:

- `hhcc/ecocardiograma/templates/ecocardiograma/eco_form.html`
- `hhcc/carotidas/templates/carotidas/nuevo_estudio.html`
- `hhcc/mmii/templates/mmii/nuevo_estudio.html`
- `hhcc/ecostress/templates/ecostress/nuevo_estudio.html`

Trabajo esperado:

- reemplazar enlaces de vuelta al listado general de historias
- volver al listado de estudios de la historia activa

Criterio de aceptacion:

- desde cualquier estudio, `Volver` conserva el contexto del paciente actual

### Bloque 2. Consolidacion de arquitectura

#### 4. Elegir una sola implementacion del listado de estudios

Estado: pendiente

Archivos a revisar:

- `hhcc/main/views.py`
- `hhcc/main/urls.py`
- `hhcc/main/templates/listar_estudios_historia.html`
- `hhcc/main/templates/ver_estudios.html`

Trabajo esperado:

- decidir cual vista queda como oficial
- eliminar o archivar la implementacion paralela
- dejar un solo template y un solo contrato de datos

Criterio de aceptacion:

- una sola URL y una sola vista resuelven el listado de estudios por historia
- no quedan caminos duplicados en `main/views.py`

#### 5. Separar claramente "nuevo estudio" de "estudio existente"

Estado: pendiente

Archivos a revisar:

- `hhcc/main/views.py`
- `hhcc/ecocardiograma/urls.py`
- `hhcc/carotidas/urls.py`
- `hhcc/mmii/urls.py`
- `hhcc/ecostress/urls.py`

Trabajo esperado:

- crear rutas explicitas de detalle/edicion para estudios existentes
- dejar `/nuevo/` solo para altas
- dejar de usar `action=recuperar&estudio=...` como base del flujo

Criterio de aceptacion:

- desde el listado de estudios se entra a una ruta explicita de estudio existente
- el usuario puede distinguir semantica y tecnicamente entre alta y edicion

#### 6. Revisar si conviene mantener listados por modulo

Estado: pendiente

Archivos a revisar:

- `hhcc/main/templates/listar_buscar_historias_2.html`
- apps de estudios

Trabajo esperado:

- decidir si los links por modulo siguen siendo acceso principal o acceso secundario

Recomendacion:

- dejar el listado unificado como flujo principal
- mantener listados por modulo solo si aportan valor real

Criterio de aceptacion:

- el sistema tiene un criterio unico y entendible para entrar a estudios

### Bloque 3. Mejora de experiencia de uso

#### 7. Dar acceso directo a historia desde listado de pacientes

Estado: pendiente

Archivos a revisar:

- `hhcc/main/templates/listar_buscar_pacientes.html`
- `hhcc/main/views.py`

Trabajo esperado:

- agregar accion `Abrir historia`
- mantener `Editar paciente` como accion separada

Criterio de aceptacion:

- desde el listado de pacientes se puede ir directo a la historia clinica

#### 8. Corregir el significado de "Ultima visita"

Estado: pendiente

Archivos a revisar:

- `hhcc/main/templates/detalle_historia_con_historial_2.html`
- `hhcc/main/views.py`

Trabajo esperado:

- calcular la ultima visita real segun comentarios/evoluciones
- dejar el label correcto si no hay visitas

Criterio de aceptacion:

- la fecha mostrada representa actividad clinica real

#### 9. Limpiar terminologia en historia clinica

Estado: pendiente

Archivos a revisar:

- `hhcc/main/templates/detalle_historia_con_historial_2.html`
- `hhcc/main/templates/historial_medico/historial_medico.html`
- vistas o serializadores asociados

Trabajo esperado:

- reemplazar `Visitas` por `Comentarios` o `Evolucion` donde corresponda
- unificar nomenclatura en UI e impresion

Criterio de aceptacion:

- la interfaz usa un lenguaje consistente

#### 10. Mejorar header y navegacion global

Estado: pendiente

Archivos a revisar:

- `hhcc/main/templates/components/header.html`

Trabajo esperado:

- hacer que el logo lleve al inicio
- evaluar accesos principales adicionales

Criterio de aceptacion:

- el header sirve como ancla real de navegacion

### Bloque 4. Limpieza tecnica

#### 11. Eliminar rutas y vistas de ejemplo o legacy que ya no aportan

Estado: pendiente

Archivos a revisar:

- `hhcc/main/urls.py`
- `hhcc/main/views.py`
- templates no usados

Trabajo esperado:

- depurar rutas `h1`, `h2`, `h3` si ya no sirven
- revisar templates y vistas duplicadas

Criterio de aceptacion:

- el arbol de rutas y vistas refleja solo flujo vigente o legado archivado de forma clara

## Orden recomendado de implementacion

1. corregir redirects legacy
2. unificar `guardar` y `volver` en estudios
3. consolidar el listado de estudios
4. separar `nuevo` de `editar`
5. recien despues mejorar header, listados y terminologia

## Estrategia de ramas sugerida

Rama actual de trabajo general:

- `refactor/flujo-clinico-integral`

Opcionalmente, si el trabajo crece mucho, dividir en subbloques:

- `fix/redirects-historia`
- `fix/retorno-estudios`
- `refactor/listado-estudios-unificado`
- `refactor/rutas-estudios-explicitas`
- `feat/acceso-historia-desde-pacientes`

## Regresiones a vigilar

- romper links existentes desde templates legacy
- dejar botones `Volver` apuntando a una URL vieja
- cambiar semantica de rutas sin actualizar impresiones o breadcrumbs
- introducir divergencia entre modulos de estudios

## Cierre

Este archivo deberia mantenerse actualizado mientras se ejecuta el saneamiento de flujo.

La idea es simple:

- el informe diagnostica
- este backlog ordena
- la rama `refactor/flujo-clinico-integral` implementa
