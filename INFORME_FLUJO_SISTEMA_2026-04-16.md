# Informe de Revision de Flujo del Sistema

Fecha: 2026-04-16

Repositorio revisado: `/home/eze/omar`

Objetivo: evaluar el sistema completo desde la perspectiva de un usuario especializado, con foco en flujo operativo, coherencia de navegacion y retorno despues de cada accion.

## Alcance

La revision cubrio los flujos principales de:

- autenticacion y navegacion global
- busqueda de pacientes
- busqueda de historias clinicas
- historia clinica
- medicacion / indicaciones
- ordenes medicas
- listado de estudios
- formularios de estudios de ecocardiograma, carotidas, MMII y ecostress
- impresion de historia clinica

No se hicieron cambios de codigo durante esta revision. El objetivo fue detectar problemas de flujo, priorizarlos y proponer soluciones concretas.

## Resumen Ejecutivo

El sistema ya es usable y resuelve la operatoria principal, pero hoy conviven capas viejas y nuevas de navegacion. Eso genera una sensacion de sistema mezclado y, mas importante, introduce comportamientos inconsistentes en puntos criticos: que pantalla se abre para editar un estudio, adonde vuelve el usuario despues de guardar, y cual es el eje de navegacion principal.

La conclusion principal es esta: la historia clinica del paciente deberia ser el centro de navegacion del sistema, y varios flujos actuales todavia desvían al usuario a listados globales o a rutas ambiguas.

## Hallazgos y Soluciones

### 1. Alta

#### 1.1 Redirects a una vista que ya no existe

Problema:

Hay acciones que todavia redirigen a `detalle_historia`, aunque la ruta vigente es `detalle_historia_con_historial`.

Referencias:

- `hhcc/main/views.py:1006`
- `hhcc/main/views.py:1022`
- `hhcc/main/urls.py:76`

Impacto:

- Si esos endpoints siguen activos, el usuario puede caer en una ruta rota.
- Aunque hoy se usen menos, dejan una zona fragil y dificil de mantener.

Solucion propuesta:

- Reemplazar todos los `redirect("detalle_historia", ...)` por `redirect("detalle_historia_con_historial", ...)`.
- Hacer una pasada global sobre `views.py` buscando nombres de rutas legacy.
- Agregar una prueba simple de integracion para estos POST.

#### 1.2 Doble implementacion del listado de estudios

Problema:

Existen dos vistas distintas para el listado de estudios, con contratos de datos diferentes y templates distintos. La URL activa publica una, pero el codigo mantiene otra en paralelo.

Referencias:

- `hhcc/main/views.py:196`
- `hhcc/main/views.py:1578`
- `hhcc/main/urls.py:22`

Impacto:

- Alto riesgo de tocar la implementacion equivocada.
- Posibles regresiones silenciosas cuando se modifica solo una de las dos.
- Sensacion de flujo inconsistente si partes del sistema usan una variante y otras otra.

Solucion propuesta:

- Elegir una sola vista de listado de estudios como canonica.
- Eliminar o archivar la otra.
- Unificar tambien el template y el contrato de datos asociado.

#### 1.3 Edicion de estudios montada sobre rutas de "nuevo"

Problema:

Para abrir un estudio existente, el sistema deriva al formulario de "nuevo estudio" y recupera el contenido via query string (`action=recuperar&estudio=...`).

Referencias:

- `hhcc/main/views.py:1599`
- `hhcc/main/views.py:1619`
- `hhcc/main/views.py:1642`
- `hhcc/main/views.py:1665`

Impacto:

- El flujo es semantica y tecnicamente ambiguo.
- Complica validaciones, breadcrumbs, botones y mensajes.
- Hace dificil saber si el usuario esta creando, editando o solo consultando.

Solucion propuesta:

- Definir una ruta explicita por estudio existente, por ejemplo:
  - `/ecocardiograma/estudio/<id>/`
  - `/carotidas/estudio/<id>/`
  - `/mmii/estudio/<id>/`
  - `/ecostress/estudio/<id>/`
- Reservar las rutas `/nuevo/` solo para altas.
- Hacer que los listados apunten a esa ruta explicita de edicion/detalle.

#### 1.4 Criterio inconsistente despues de guardar un estudio

Problema:

Cada modulo responde distinto despues de guardar:

- MMII vuelve a la vista de nuevo estudio.
- Ecostress vuelve a la vista de nuevo estudio.
- Carotidas salta a una pantalla distinta.

Referencias:

- `hhcc/mmii/views.py:68`
- `hhcc/ecostress/views.py:76`
- `hhcc/carotidas/views.py:41`

Impacto:

- El usuario no puede anticipar que va a pasar al guardar.
- Se pierde continuidad de trabajo por paciente.
- El sistema requiere reaprendizaje por modulo.

Solucion propuesta:

- Definir una regla unica para todos los estudios.
- Recomendacion:
  - guardar y quedarse en el estudio recien guardado si se va a seguir editando
  - o guardar y volver al listado de estudios de esa historia si el flujo es mas transaccional
- Aplicar la misma regla en los cuatro modulos.

### 2. Media-Alta

#### 2.1 Los botones "Volver" de estudios rompen el contexto del paciente

Problema:

Los formularios de estudios vuelven al listado general de historias en lugar de volver a la historia o al listado de estudios del paciente actual.

Referencias:

- `hhcc/ecocardiograma/templates/ecocardiograma/eco_form.html:1402`
- `hhcc/carotidas/templates/carotidas/nuevo_estudio.html:337`
- `hhcc/mmii/templates/mmii/nuevo_estudio.html:190`
- `hhcc/ecostress/templates/ecostress/nuevo_estudio.html:234`

Impacto:

- El medico pierde el hilo del paciente que estaba atendiendo.
- Se agregan clics innecesarios para retomar el contexto.

Solucion propuesta:

- Cambiar todos los "Volver" para que regresen a:
  - `historias/<historia_id>/estudios/`
- En un segundo nivel, ofrecer desde ahi acceso a la historia clinica completa.

#### 2.2 Navegacion global insuficiente y logo mal aprovechado

Problema:

El logo lleva a editar perfil en lugar de llevar al inicio, y el menu principal expone muy pocas entradas para el uso real del sistema.

Referencias:

- `hhcc/main/templates/components/header.html:10`
- `hhcc/main/templates/components/header.html:26`

Impacto:

- El sistema no ofrece una orientacion global clara.
- Muchas funciones quedan descubiertas solo por conocimiento previo.
- El logo, que deberia ser un ancla de navegacion, hoy no cumple ese rol.

Solucion propuesta:

- Hacer que el logo lleve al inicio real del sistema.
- Mantener perfil/cambio de nombre como accion de usuario, no como home implicita.
- Mantener por ahora la arquitectura de dos objetos principales del sistema:
  - Pacientes
  - Historias
- Por ahora no introducir un item global `Buscador`, porque hoy los buscadores vigentes son el de pacientes y el de historias.
- No introducir un item global `Estudios`, porque estudios no tiene entrada directa autonoma; se accede desde paciente/historia.

Definicion funcional confirmada:

- `Pacientes` y `Historias` deben conservar el mismo nivel de importancia en la navegacion.
- El sistema no debe sugerir que `Historias` está por encima de `Pacientes`.
- Por ahora el header debe respetar el esquema de dos objetos principales.
- Esto no descarta que exista mas adelante un buscador global como tercer entrada, pero todavia no corresponde diseñar el header como si ya estuviera resuelto.

#### 2.3 Dos modelos de acceso a estudios compiten entre si

Problema:

Desde el listado de historias se puede entrar al listado unificado de estudios o a listados especificos por modulo. No queda claro cual es la entrada principal recomendada.

Referencias:

- `hhcc/main/templates/listar_buscar_historias_2.html:87`
- `hhcc/main/templates/listar_buscar_historias_2.html:115`

Impacto:

- Duplica caminos para una misma tarea.
- Aumenta la dispersión del flujo.

Solucion propuesta:

- Elegir un camino principal.
- Recomendacion:
  - desde historias, entrar primero a la historia clinica
  - desde la historia, ir a `Estudios`
  - dejar los contadores por modulo como informacion o acceso secundario, no como flujo principal

### 3. Media

#### 3.1 La lista de pacientes no ofrece acceso directo a la historia clinica

Problema:

Desde el listado de pacientes hoy solo se puede editar el paciente. No hay un acceso claro y directo a su historia clinica.

Referencia:

- `hhcc/main/templates/listar_buscar_pacientes.html:83`

Impacto:

- Para la operatoria diaria, editar la ficha suele ser menos frecuente que abrir la historia.
- Obliga a hacer mas navegacion de la necesaria.

Solucion propuesta:

- Agregar una segunda accion por fila:
  - `Abrir historia`
- Mantener `Editar paciente` como accion administrativa separada.

#### 3.2 La historia muestra "Ultima visita" con una fecha que no representa la ultima visita real

Problema:

Se muestra `historia.fechaAlta` como "Ultima visita", pero eso parece ser la fecha de alta de la historia, no la ultima evolucion registrada.

Referencia:

- `hhcc/main/templates/detalle_historia_con_historial_2.html:172`

Impacto:

- El medico puede interpretar mal la recencia clinica del seguimiento.

Solucion propuesta:

- Mostrar la fecha del ultimo comentario/visita real.
- Si no hay visitas, mostrar "Sin visitas registradas" o la fecha de apertura de historia con rotulo correcto.

#### 3.3 Cancelar en alta/edicion de paciente no debe relanzar la misma operacion

Problema:

El comportamiento de `Cancelar` no es consistente entre alta y edicion de paciente.

Referencias:

- `hhcc/main/templates/crear_paciente.html:186`
- `hhcc/main/templates/editar_paciente.html:361`

Estado actual observado:

- En `crear_paciente`, `Cancelar` ya abandona el alta y vuelve al listado de pacientes.
- En `editar_paciente`, `Cancelar` vuelve a la misma pantalla de edicion, generando un bucle sin salida real.

Impacto:

- En edicion, `Cancelar` no cancela nada.
- El usuario queda forzado a salir por otro camino que no es el control esperado.
- La interfaz contradice la semantica del boton.

Solucion propuesta:

- Mantener el criterio de que `Cancelar` debe abandonar la operacion actual.
- En `editar_paciente`, hacer que `Cancelar` vuelva a una pantalla neutra o de contexto.

Recomendacion:

- opcion minima y consistente: volver a `listar_buscar_pacientes`
- opcion contextual mas rica: volver a la historia clinica del paciente si existe

Conclusion funcional:

- La idea correcta no es necesariamente "volver a una pantalla blanca" literal.
- La idea correcta es salir de la operacion en curso y no reingresar a la misma vista.

### 4. Baja

#### 4.1 Terminologia inconsistente en la historia clinica

Problema:

Dentro del panel de la historia se sigue usando el rotulo `Visitas` donde el contenido corresponde a comentarios o evolucion.

Referencias:

- `hhcc/main/templates/detalle_historia_con_historial_2.html:346`
- `hhcc/main/templates/historial_medico/historial_medico.html:217`

Impacto:

- No rompe flujo, pero ensucia el lenguaje funcional.
- Hace mas dificil cerrar una interfaz consistente.

Solucion propuesta:

- Renombrar el bloque como `Comentarios` o `Evolucion`.
- Unificar ese lenguaje en historia, impresion y API.

#### 4.2 Rutas de ejemplo visibles en el arbol principal

Problema:

Siguen definidas rutas de ejemplo (`h1`, `h2`, `h3`) en el archivo principal de URLs.

Referencia:

- `hhcc/main/urls.py:89`

Impacto:

- Aumenta ruido tecnico.
- Daña la claridad del arbol de navegacion.

Solucion propuesta:

- Eliminar esas rutas si ya no cumplen funcion.
- Si sirven para diseño o referencia, moverlas a un entorno de desarrollo o carpeta de archivo.

## Propuesta de Flujo Objetivo

### Eje principal

El eje principal del sistema deberia ser:

1. Buscar paciente o buscar historia.
2. Entrar a la historia clinica.
3. Desde la historia:
   - cargar evolucion
   - cargar signos vitales
   - ajustar diagnosticos
   - ir a indicaciones
   - ir a estudios
   - ir a ordenes
   - imprimir

### Regla de contexto

Toda pantalla secundaria deberia conservar el contexto de la historia activa.

Eso implica:

- breadcrumbs consistentes
- botones `Volver` hacia la historia o hacia el listado de estudios de esa historia
- mensajes de exito que no expulsen al usuario a listados globales

### Regla unica para estudios

Cada modulo de estudio deberia tener tres estados claros:

- nuevo
- edicion de estudio existente
- impresion

Y los tres deberian compartir el mismo criterio de retorno.

## Priorizacion Recomendada

### Fase 1: estabilizacion de flujo

- corregir redirects a rutas inexistentes
- unificar retornos despues de guardar estudios
- cambiar botones `Volver` de estudios para preservar contexto

### Fase 2: simplificacion de arquitectura

- consolidar una sola vista de listado de estudios
- eliminar rutas y templates duplicados o legacy
- definir rutas explicitas para editar estudios existentes

### Fase 3: afinado de UX

- agregar acceso directo a historia desde listado de pacientes
- corregir significado de "Ultima visita"
- depurar terminologia (`Visitas` vs `Comentarios`)
- mejorar header y home de navegacion

## Conclusion

El sistema no necesita un rediseño total. Necesita ordenar su columna vertebral de navegacion.

Hoy el mayor costo para el usuario no esta en la complejidad clinica sino en la inconsistencia entre modulos y en la convivencia de flujos viejos y nuevos. Si se toma la historia clinica como centro, se unifican los retornos y se limpian las rutas duplicadas, el sistema puede ganar mucha claridad sin una reescritura grande.

## Anexo: Archivos principales revisados

- `hhcc/main/urls.py`
- `hhcc/main/views.py`
- `hhcc/main/templates/components/header.html`
- `hhcc/main/templates/listar_buscar_pacientes.html`
- `hhcc/main/templates/listar_buscar_historias_2.html`
- `hhcc/main/templates/detalle_historia_con_historial_2.html`
- `hhcc/main/templates/historial_medico/historial_medico.html`
- `hhcc/main/templates/listar_estudios_historia.html`
- `hhcc/ecocardiograma/templates/ecocardiograma/eco_form.html`
- `hhcc/carotidas/templates/carotidas/nuevo_estudio.html`
- `hhcc/mmii/templates/mmii/nuevo_estudio.html`
- `hhcc/ecostress/templates/ecostress/nuevo_estudio.html`
- `hhcc/carotidas/views.py`
- `hhcc/mmii/views.py`
- `hhcc/ecostress/views.py`
