# Plan de integracion QBI2 Recipe con historias clinicas

Fecha de trabajo: 2026-06-19.

Documento base leido: `API_ENTITIES.md` (`DQBI2-IT-014`, modelo de entidades de la interfaz QBI2 Recipe).

Objetivo: definir un plan de inclusion total de QBI2 Recipe dentro del sistema de historias clinicas de `~/omar`, dejando atras la POC como camino principal. La POC sirve como evidencia tecnica de payloads, cliente HTTP, busqueda de medicamentos y emision HML, pero la integracion final debe modelar el dominio completo: recetas, practicas, otras prescripciones, documentos emitidos, estados, anulacion, consulta, auditoria y vinculacion clinica.

Decision explicita: no usar cache para catalogos QBI2. Las busquedas de medicamentos, diagnosticos, financiadores y practicas deben consultar QBI2 en vivo. El sistema puede guardar auditoria y snapshots de lo efectivamente elegido o emitido, pero no debe persistir catalogos como cache operativo.

---

## 1. Lectura sintetica del contrato QBI2

QBI2 Recipe no debe entenderse como "un endpoint para imprimir una receta". Es un microservicio documental con dos familias de operaciones:

- Catalogos maestros por GET: diagnosticos, medicamentos, practicas, financiadores y planes.
- Generadores por POST: `GenerarReceta`, `GenerarPractica`, `GenerarOtrasPrescripciones`.

El flujo correcto es:

1. Buscar en catalogos QBI2.
2. Tomar identificadores canonicos del catalogo.
3. Armar un payload con actores, cobertura, diagnostico e items prescriptos.
4. Emitir documento.
5. Guardar respuesta completa y resumen normalizado.
6. Exponer PDF/verificador dentro de la historia clinica.
7. Consultar estado o anular usando el identificador correcto.

La distincion mas importante del contrato es la doble identidad del documento:

- `id`: hash documental. Sirve para anular.
- `idReceta` o `numeroPrescripcion`: numero documental. Sirve para consultar.

No son intercambiables. Un modelo que guarde solo `qbi2_id_receta` queda corto y es riesgoso.

Tambien hay que asumir que HTTP 200 no significa exito total. QBI2 puede responder 200 con `errores[]`, `response[]`, `idTransaccion` o exito parcial. Por lo tanto, la capa de integracion debe parsear cuerpo completo, no solo status HTTP.

---

## 2. Estado actual del sistema local

El sistema real vive en `~/omar/hhcc` y es un monolito Django. El eje funcional es `main.HistoriaClinica`, asociada a `main.Paciente`.

Modelos actuales relevantes:

- `Paciente`: documento, nombre, apellido, fecha de nacimiento, sexo, contacto, obra social, plan, afiliado.
- `HistoriaClinica`: entidad eje.
- `ComentariosVisitas`: evolucion e indicaciones como texto por fecha.
- `IndicacionesVisitas`: medicacion/indicaciones internas por historia y fecha.

Pantallas actuales relevantes:

- Historia clinica: centro de trabajo medico.
- Indicaciones: listado, alta, edicion, baja logica e impresion PDF local.
- Solicitudes: ordenes medicas locales con impresion PDF.
- QBI2 POC: busqueda de vademecum, portal paciente, solicitudes de receta y emision HML.

La POC actual contiene piezas utiles:

- `Qbi2Client`: cliente HTTP configurable.
- `VademecumService`: busqueda directa de medicamentos.
- `recipes.py`: construccion de payload y emision de receta.
- `SolicitudReceta`: solicitud paciente/medico con auditoria basica.
- `portal.py`: validacion simple de paciente por apellido/documento.

Pero tambien tiene limites que no deben arrastrarse a produccion:

- Incluye cache (`Qbi2CacheEntry`, `CachedVademecumService`, `MySQLCache`), que queda fuera.
- Guarda una receta emitida dentro de una solicitud, con pocos campos normalizados.
- No modela documentos emitidos como entidad propia.
- No distingue suficientemente hash de anulacion, numero documental, transaccion y estado.
- Tiene defaults ficticios de HML que deben reemplazarse por validacion real.
- Solo cubre receta de medicamentos, no practicas ni otras prescripciones.

---

## 3. Principio de arquitectura

La integracion final debe ser un modulo documental asociado a la historia clinica.

Regla central:

> QBI2 no reemplaza la historia clinica, ni las indicaciones internas, ni las solicitudes locales. QBI2 emite documentos electronicos verificables que nacen desde esos flujos y luego quedan adjuntos a la historia como eventos clinico-administrativos.

Consecuencias:

- `HistoriaClinica` sigue siendo el eje de navegacion.
- `Paciente` sigue siendo la fuente local de identidad, pero necesita mejorar datos para QBI2.
- Las indicaciones internas pueden originar recetas QBI2, pero no toda indicacion es una receta electronica.
- Las solicitudes locales pueden originar practicas QBI2, pero no toda solicitud local necesita QBI2.
- Los documentos QBI2 deben aparecer en el timeline/historial de la historia.
- La respuesta completa de QBI2 debe conservarse para auditoria y soporte.
- Los catalogos se consultan en vivo, sin cache.

---

## 4. Modelo objetivo propuesto

### 4.1 `Qbi2Documento`

Entidad principal de documento electronico emitido o intentado.

Representa recetas, practicas y otras prescripciones. Debe vincularse siempre que sea posible a historia y paciente.

Campos sugeridos:

- `historia_clinica`: FK a `main.HistoriaClinica`.
- `paciente`: FK a `main.Paciente`.
- `tipo`: `receta`, `practica`, `otra_prescripcion`.
- `origen`: `historia`, `indicacion`, `solicitud`, `portal_paciente`, `manual`, `reintento`.
- `estado_local`: `borrador`, `listo_para_emitir`, `emitiendo`, `emitido`, `emitido_parcial`, `error_emision`, `anulacion_pendiente`, `anulado`, `error_anulacion`, `vencido`, `estado_desconocido`.
- `estado_qbi2`: valor textual devuelto por QBI2 (`pendiente`, `autorizado`, `dispensado`, `vencido`, `anulado`, etc.).
- `cliente_app_id`: snapshot del cliente usado.
- `qbi2_id_hash`: campo `id`, hash usado para anular.
- `qbi2_id_receta`: numero documental de receta, usado para consultar recetas.
- `qbi2_numero_prescripcion`: numero documental para practica u otras prescripciones.
- `qbi2_id_transaccion`: agrupador cuando QBI2 divide la operacion.
- `fecha_emision`: fecha/hora local de emision.
- `fecha_documento_qbi2`: fecha devuelta por QBI2.
- `fecha_vencimiento_qbi2`: si QBI2 la informa.
- `pdf_url`: `s3Link`.
- `verificador_url`: enlace verificador.
- `payload_enviado`: JSON completo.
- `respuesta_qbi2`: JSON completo.
- `errores_qbi2`: JSON/lista normalizada.
- `ultimo_error`: texto corto para UI.
- `solicitado_por`, `emitido_por`, `anulado_por`: FK a usuario.
- `created_at`, `updated_at`.

Indices:

- `(historia_clinica, -created_at)`.
- `(paciente, -created_at)`.
- `(tipo, estado_local)`.
- `qbi2_id_hash`.
- `qbi2_id_receta`.
- `qbi2_numero_prescripcion`.
- `qbi2_id_transaccion`.

Razon: esta tabla permite ver todos los documentos QBI2 de una historia y operar consulta/anulacion sin depender de una solicitud original.

### 4.2 `Qbi2ItemPrescripto`

Entidad hija de `Qbi2Documento`.

Campos sugeridos:

- `documento`: FK a `Qbi2Documento`.
- `tipo_item`: `medicamento`, `practica`, `texto_libre`.
- `reg_no`: identificador Alfabeta para medicamento.
- `medicamento_nombre_producto`.
- `medicamento_nombre_droga`.
- `medicamento_presentacion`.
- `practica_id`: identificador de practica QBI2.
- `practica_nombre`.
- `practica_categoria`.
- `practica_tipo`.
- `texto_libre`: para otras prescripciones.
- `cantidad`.
- `tratamiento`.
- `posologia`.
- `diagnostico_texto`.
- `diagnostico_codigo`: CIE-10 si se uso catalogo.
- `permite_sustitucion`.
- `imprimir_diagnostico`.
- `forzar_duplicado`.
- `metadata_qbi2`: snapshot de campos adicionales elegidos.

Razon: una receta puede tener varios medicamentos; una emision puede dividirse; las practicas y textos libres necesitan un contenedor comun pero no identico.

### 4.3 `Qbi2Solicitud`

Entidad opcional pero recomendable para flujos que requieren aprobacion antes de emitir.

No debe confundirse con documento emitido. Una solicitud es intencion o pedido; un documento es resultado QBI2.

Campos sugeridos:

- `historia_clinica`, `paciente`.
- `tipo`: `receta`, `practica`, `otra_prescripcion`.
- `origen`: `portal_paciente`, `medico`, `administrativo`, `indicacion`.
- `estado`: `pendiente`, `aprobada`, `rechazada`, `cancelada`, `convertida_en_documento`.
- `payload_borrador`: JSON con seleccion del paciente/medico antes de emitir.
- `observacion_paciente`.
- `observacion_medico`.
- `creada_por`, `decidida_por`.
- `documento_resultante`: FK opcional a `Qbi2Documento`.
- `created_at`, `updated_at`, `fecha_decision`.

La actual `SolicitudReceta` puede migrar hacia esta entidad general o mantenerse como puente temporal, pero no conviene expandirla indefinidamente.

### 4.4 `Qbi2Evento`

Log inmutable de eventos de integracion.

Campos sugeridos:

- `documento`: FK opcional a `Qbi2Documento`.
- `solicitud`: FK opcional a `Qbi2Solicitud`.
- `tipo_evento`: `catalogo_busqueda`, `payload_generado`, `emision_intento`, `emision_ok`, `emision_parcial`, `emision_error`, `consulta_estado`, `anulacion_intento`, `anulacion_ok`, `anulacion_error`, `validacion_local_error`.
- `endpoint`.
- `request_resumen`: JSON sin secretos.
- `response_resumen`: JSON sin datos excesivos si no hace falta.
- `http_status`.
- `error`.
- `usuario`.
- `ip`.
- `created_at`.

Como no se usara cache, este evento no sirve para responder busquedas futuras. Sirve para auditoria, soporte y trazabilidad.

### 4.5 Snapshots embebidos

Para evitar sobre-modelar desde el inicio, los datos de actores pueden guardarse como JSON dentro de `Qbi2Documento`:

- `paciente_snapshot`.
- `medico_snapshot`.
- `cobertura_snapshot`.
- `lugar_atencion_snapshot`.
- `sub_emisor_snapshot`.

Esto es preferible a depender solo de `Paciente`, porque una receta debe conservar lo que se envio aunque luego cambie el domicilio, obra social o telefono del paciente.

---

## 5. Datos locales que faltan o deben normalizarse

Para integracion total no conviene seguir usando defaults ficticios. Hay que decidir como completar o exigir datos.

### Paciente

Campos actuales utiles:

- Tipo y numero de documento.
- Nombre/apellido.
- Fecha de nacimiento.
- Sexo.
- Email, telefono, celular.
- Direccion libre, localidad.
- Obra social, plan, afiliado.

Brechas:

- CUIL/CUIT del paciente si QBI2 lo exige para ciertas operaciones.
- Provincia estructurada.
- Codigo postal.
- Domicilio partido en calle/numero/piso/depto.
- Mapeo real de obra social local contra `idFinanciador`, `nroFinanciador`, `planId`.
- Validacion de email real, no fallback.
- Sexo local `H/M` debe mapearse cuidadosamente a QBI2. Hoy la POC mapea `H -> M` y `M -> F`, pero esto merece validacion explicita porque `M` puede ser ambiguo si se lee como masculino en otros contratos.

Decision recomendada: agregar una pantalla de "Datos requeridos para receta electronica" cuando falten campos. No emitir con datos inventados.

### Medico

El sistema actual no tiene un modelo medico completo equivalente a QBI2.

Hace falta definir configuracion local:

- Nombre/apellido profesional.
- Tipo y numero de documento.
- CUIL/CUIT o `idTributario`.
- Profesion.
- Especialidad.
- Matricula tipo y numero.
- Sello: linea1, linea2, linea3.
- Email/telefono profesional.

Puede vivir inicialmente en settings/env si hay un solo medico, pero para integracion total conviene un modelo `MedicoEmisor` o `Qbi2PerfilEmisor`, incluso si empieza con una unica fila.

### Lugar de atencion

Debe existir configuracion estructurada:

- Nombre del consultorio.
- Domicilio.
- Codigo postal.
- Localidad.
- Provincia.
- Email.
- Telefono/contacto.
- Logo si QBI2 lo usa.

### Cobertura

No alcanza con `obraSocial`, `plan`, `afiliado` como texto libre si se quiere validar contra financiadores.

Sin cache, el flujo seria:

1. En la ficha del paciente, el usuario busca financiador/plan en vivo contra QBI2.
2. El sistema guarda en el paciente los identificadores elegidos, no como cache de catalogo sino como dato administrativo del paciente:
   - `qbi2_id_financiador`.
   - `qbi2_nro_financiador`.
   - `qbi2_plan_id`.
   - `qbi2_plan_nombre_snapshot`.
   - `afiliado_credencial`.
3. Al emitir, se envia el snapshot actual del paciente.

Esto no contradice "sin cache": no se esta cacheando el catalogo completo, se esta guardando la cobertura seleccionada para ese paciente.

---

## 6. Servicios de integracion

Separar la capa QBI2 en servicios pequenos, testeables y sin dependencia de templates.

### 6.1 Cliente HTTP

Reutilizar y endurecer `Qbi2Client`:

- Base URL por entorno: HML/produccion.
- Token bearer opcional/obligatorio segun env.
- Timeout corto.
- Logging sin secretos.
- Parseo JSON robusto.
- Errores propios: configuracion, HTTP, red, timeout, respuesta invalida.

Mejora recomendada: migrar de `urllib` a `requests` solo si el proyecto ya lo acepta como dependencia. Si no, `urllib` actual alcanza.

### 6.2 Catalogos directos sin cache

Servicios:

- `Qbi2DiagnosticoService.buscar(texto)`.
- `Qbi2MedicamentoService.buscar(texto, page=1, cobertura=None)`.
- `Qbi2FinanciadorService.buscar()`.
- `Qbi2PracticaService.buscar(texto, cliente_app_id)`.

Reglas:

- No guardar resultados para reuso.
- Normalizar nombres de campos inconsistentes al salir del servicio.
- Registrar evento de busqueda solo si hace falta auditoria.
- Devolver items minimos para UI: id canonico, display, metadata necesaria.

### 6.3 Builders de payload

Un builder por generador:

- `build_generar_receta_payload(documento_o_borrador)`.
- `build_generar_practica_payload(documento_o_borrador)`.
- `build_generar_otras_prescripciones_payload(documento_o_borrador)`.

Responsabilidades:

- Validar datos locales antes de invocar QBI2.
- Mapear `Paciente`, medico, cobertura y lugar de atencion.
- Usar identificadores canonicos de catalogos.
- Resolver inconsistencias de nombres (`clienteAppId/clientAppId`, `depto/dpto`, etc.) en un solo lugar.
- No inventar datos clinicos o administrativos.
- Generar payload completo y guardarlo antes o junto con el intento de emision.

### 6.4 Parser de respuesta

Un parser comun de documentos emitidos:

- Extraer `id` hash.
- Extraer `idReceta` o `numeroPrescripcion`.
- Extraer `idTransaccion`.
- Extraer `s3Link`.
- Extraer `verificador`.
- Extraer `fecha`, `fechavencimiento`, `status/estado`.
- Extraer `errores[]`.
- Detectar exito total, exito parcial o error semantico con HTTP 200.

Regla de oro: la UI y los modelos no deben leer directamente la respuesta cruda. Deben usar un resumen normalizado.

### 6.5 Consulta y anulacion

Servicios:

- `consultar_documento(documento)`.
- `anular_documento(documento, motivo, usuario)`.

Reglas:

- Para anular usar `qbi2_id_hash`.
- Para consultar usar `qbi2_id_receta` o `qbi2_numero_prescripcion` segun tipo.
- Si hay `idTransaccion`, permitir consulta por transaccion cuando aplique.
- Guardar cada intento como evento.
- Actualizar `estado_local` solo despues de parsear respuesta.

---

## 7. Integracion en pantallas

### 7.1 Historia clinica

Agregar una seccion "Documentos electronicos" o "Recetas y prescripciones" en la historia.

Debe mostrar:

- Fecha.
- Tipo.
- Diagnostico.
- Items.
- Estado local/QBI2.
- PDF.
- Verificador.
- Acciones: consultar estado, anular, reintentar si error.

Debe permitir:

- Nueva receta.
- Nueva practica.
- Nueva prescripcion libre.
- Crear receta desde una indicacion existente.

### 7.2 Indicaciones

Las indicaciones actuales son medicacion interna, con horarios y fecha. No deben convertirse automaticamente en receta.

Agregar acciones por indicacion:

- "Recetar en QBI2".
- "Agregar a receta QBI2".
- "Ver recetas emitidas relacionadas".

Casos:

- Una indicacion puede no tener `regNo`, porque hoy es texto libre. En ese caso, antes de emitir se debe buscar medicamento QBI2 en vivo y seleccionar.
- Varias indicaciones pueden agruparse en una receta si QBI2 y la regla medica lo permiten.
- Si QBI2 limita cantidad o divide recetas, el sistema debe crear N `Qbi2Documento` hijos o un documento transaccional con items asociados a cada respuesta. Recomendacion: crear un `Qbi2Documento` por documento final y compartir `qbi2_id_transaccion`.

### 7.3 Solicitudes locales

La pantalla de solicitudes actual puede originar dos caminos:

- PDF local tradicional.
- Prescripcion electronica QBI2 de practica u otra prescripcion.

El usuario debe elegir si la solicitud sera:

- Orden local no QBI2.
- Practica QBI2 desde catalogo.
- Otra prescripcion QBI2 de texto libre.

### 7.4 Portal paciente

El portal paciente de la POC puede mantenerse como flujo de solicitud, no como flujo de emision directa.

Reglas:

- El paciente busca medicamentos en vivo.
- El paciente solicita renovacion.
- El medico revisa, edita diagnostico/posologia/cantidad y aprueba.
- Solo el medico emite QBI2.
- La solicitud queda vinculada a la historia y al documento emitido.

### 7.5 Ficha de paciente

Agregar bloque "Datos para receta electronica":

- CUIL/CUIT.
- Email valido.
- Domicilio estructurado.
- Cobertura QBI2 seleccionada.
- Afiliado/credencial.

Debe mostrar estado de completitud:

- Completo para emitir.
- Falta fecha de nacimiento.
- Falta cobertura QBI2.
- Falta CUIL.
- Falta email valido.
- Falta domicilio.

---

## 8. Casos de uso principales

Antes de listar casos, conviene fijar una distincion funcional:

- Indicacion local: instruccion clinica interna de medicacion o conducta. Vive en la historia y puede cambiarse sin interactuar con QBI2.
- Solicitud local: orden o pedido administrativo/clinico que hoy puede imprimirse como PDF local.
- Solicitud QBI2: pedido pendiente de aprobacion, todavia no emitido.
- Documento QBI2: receta, practica u otra prescripcion ya intentada o emitida contra QBI2.

Matriz de decision:

| Situacion | Debe usar QBI2 | Entidad local principal | Resultado |
| --- | --- | --- | --- |
| Ajustar medicacion cronica en historia | No necesariamente | `IndicacionesVisitas` | Indicacion interna |
| Entregar receta electronica al paciente | Si | `Qbi2Documento` | PDF/verificador QBI2 |
| Paciente pide renovacion | No emite directo | `Qbi2Solicitud` | Pendiente de medico |
| Orden de estudio local tradicional | No necesariamente | Solicitud local actual | PDF local |
| Orden electronica de practica | Si | `Qbi2Documento` | `numeroPrescripcion` QBI2 |
| Texto libre prescriptivo verificable | Si | `Qbi2Documento` | Otra prescripcion QBI2 |
| Cancelar documento ya emitido | Si | `Qbi2Documento` + `Qbi2Evento` | Anulacion QBI2 |

### CU-01: Medico emite receta desde historia

1. Abre historia clinica.
2. Click en "Nueva receta electronica".
3. Busca medicamento en QBI2 en vivo.
4. Selecciona medicamento por `regNo`.
5. Completa cantidad, tratamiento, posologia, diagnostico.
6. Sistema valida paciente, medico, cobertura y lugar de atencion.
7. Sistema arma payload.
8. QBI2 emite.
9. Sistema guarda documento, items, payload, respuesta, PDF y verificador.
10. Historia muestra documento emitido.

Variantes:

- Faltan datos del paciente: se redirige a completar datos.
- QBI2 devuelve duplicado: se ofrece reemitir con `forzarDuplicado` si corresponde.
- QBI2 devuelve error parcial: se muestra emitido parcial con detalle.

### CU-02: Medico emite receta desde indicacion existente

1. Abre indicaciones.
2. Elige una indicacion.
3. Click en "Recetar".
4. Si la indicacion no tiene `regNo`, busca medicamento QBI2.
5. Sistema propone posologia a partir de horarios/texto local.
6. Medico confirma o edita.
7. Se emite documento QBI2.
8. Queda enlace desde la indicacion al documento.

### CU-03: Medico agrupa varias indicaciones en una receta

1. Selecciona varias indicaciones.
2. Sistema valida maximo permitido por receta.
3. Para cada indicacion sin `regNo`, exige seleccion QBI2.
4. Emite una receta con N medicamentos o divide antes si se define regla local.
5. Si QBI2 divide, guarda documentos resultantes con mismo `idTransaccion`.

### CU-04: Paciente solicita renovacion desde portal

1. Paciente ingresa apellido/documento.
2. Sistema encuentra paciente e historia.
3. Paciente busca medicamentos QBI2 en vivo.
4. Envia solicitud con observacion.
5. Medico ve solicitud pendiente.
6. Medico aprueba, corrige o rechaza.
7. Si aprueba, se emite QBI2.
8. Paciente podria ver estado o recibir enlace segun decision posterior.

### CU-05: Practica QBI2 desde solicitudes

1. Medico abre solicitudes.
2. Elige categoria/tipo de practica.
3. Busca practica en QBI2 en vivo.
4. Selecciona practica por `id`.
5. Completa diagnostico y observaciones.
6. QBI2 emite prescripcion/orden.
7. Sistema guarda `numeroPrescripcion`, PDF y verificador.

### CU-06: Otras prescripciones

1. Medico elige "Otra prescripcion".
2. Escribe texto libre.
3. Agrega diagnostico textual o CIE-10.
4. QBI2 emite.
5. Sistema guarda documento como `otra_prescripcion`.

### CU-07: Recetas postdatadas

1. Medico activa postdatado.
2. Define cantidad y dias o fechas explicitas.
3. Sistema valida maximo local si se conoce.
4. QBI2 puede devolver varios documentos bajo `idTransaccion`.
5. Sistema guarda cada documento final y el agrupador.

Punto critico: confirmar el nombre exacto del campo (`recetasPostdatadas` vs `recetasPostadatas`) contra payload real antes de implementar.

### CU-08: Consulta de estado

1. Usuario abre documento emitido.
2. Click en "Consultar estado".
3. Sistema usa `idReceta` o `numeroPrescripcion`.
4. Actualiza estado local y guarda evento.

### CU-09: Anulacion

1. Usuario abre documento emitido.
2. Click en "Anular".
3. Informa motivo si QBI2 lo requiere.
4. Sistema usa `id` hash, no `idReceta`.
5. QBI2 confirma o rechaza.
6. Sistema actualiza estado y registra evento.

Reglas:

- No anular si ya esta anulado.
- No anular si esta vencido y QBI2 no lo permite.
- No anular si no hay hash.

### CU-10: Reintento de emision

1. Emision falla por red, timeout o error QBI2.
2. Documento queda `error_emision`.
3. Usuario corrige datos o reintenta.
4. El reintento crea nuevo evento y, segun decision, reutiliza documento o crea uno nuevo relacionado.

Recomendacion: si el payload cambia, crear nuevo documento intento. Si solo fue timeout y se puede consultar idempotencia/transaccion, evitar duplicar.

### CU-11: PDF y verificador

1. Documento emitido muestra `s3Link` y `verificador`.
2. Abrir PDF no debe depender de generar PDF local.
3. Si no hay PDF pero hay numero documental, permitir consulta/recuperacion si QBI2 lo soporta.

### CU-12: Medicamento sensible o paciente confidencial

1. Medicamento tiene marca HIV/sensible o medico activa confidencialidad.
2. Payload envia `ocultarPaciente`/`confidencial` segun contrato real.
3. Documento conserva snapshot de decision.
4. UI debe mostrar una advertencia discreta y evitar exponer datos innecesarios.

### CU-13: Cobertura no resuelta

1. Paciente tiene obra social textual pero no ids QBI2.
2. Antes de emitir, sistema exige resolver financiador/plan en vivo.
3. Se guarda seleccion en ficha del paciente.
4. Se emite usando ids canonicos.

### CU-14: Sin cobertura

1. Paciente no tiene cobertura o se decide emitir sin cobertura.
2. Payload debe reflejar ausencia de cobertura conforme contrato.
3. El documento queda emitido con snapshot sin financiador.

### CU-15: Error semantico con HTTP 200

1. QBI2 responde HTTP 200.
2. Cuerpo contiene `errores[]` o `response[]` fallido.
3. Parser clasifica `error_emision` o `emitido_parcial`.
4. UI no muestra "emitido" salvo que haya identificador documental valido.

---

## 9. Maquina de estados local

Estados recomendados para `Qbi2Documento`:

- `borrador`: aun no se intento emitir.
- `listo_para_emitir`: datos locales completos.
- `emitiendo`: lock transitorio durante POST.
- `emitido`: QBI2 devolvio documento valido.
- `emitido_parcial`: hubo una transaccion con algunos documentos y errores.
- `error_emision`: no se emitio documento util.
- `anulacion_pendiente`: se inicio anulacion.
- `anulado`: QBI2 confirmo anulacion.
- `error_anulacion`: fallo la anulacion.
- `vencido`: QBI2 informa vencimiento.
- `estado_desconocido`: no se pudo reconciliar estado.

Transiciones relevantes:

- `borrador -> listo_para_emitir`.
- `listo_para_emitir -> emitiendo`.
- `emitiendo -> emitido`.
- `emitiendo -> emitido_parcial`.
- `emitiendo -> error_emision`.
- `emitido -> anulado`.
- `emitido -> vencido`.
- `emitido -> estado_desconocido`.

No conviene borrar documentos QBI2. Si algo se cancela o anula, debe quedar evento.

---

## 10. Reglas de no-cache

No usar cache significa:

- No `Qbi2CacheEntry` para medicamentos.
- No `CachedVademecumService`.
- No stale/fresh windows.
- No responder busquedas desde MySQL.
- No jobs de refresh.

Si se guarda algo, debe ser una de estas categorias:

- Snapshot de lo elegido para un paciente.
- Snapshot de lo elegido para un documento.
- Payload enviado.
- Respuesta recibida.
- Evento/auditoria.

Ejemplo permitido:

- Guardar en `Qbi2ItemPrescripto` el `regNo`, nombre, droga y presentacion seleccionados para una receta emitida.

Ejemplo no permitido:

- Guardar resultados de `GetMedicamento?text=ator` para responder futuras busquedas de "ator".

---

## 11. Seguridad y auditoria

Requisitos:

- QBI2 solo desde backend.
- Token nunca al navegador.
- Logging sin bearer token.
- Timeouts cortos.
- Eventos por emision, consulta y anulacion.
- Registrar usuario medico que emite/anula.
- Registrar IP cuando el origen sea portal paciente.
- Conservar payload/respuesta para soporte, cuidando datos sensibles.

Permisos:

- Ver documentos QBI2: usuarios autenticados del sistema.
- Emitir: medico o rol autorizado.
- Anular: medico o rol autorizado; idealmente confirmacion explicita.
- Portal paciente: solo crea solicitudes, no emite.

---

## 12. Riesgos y puntos a validar

1. Campo `clienteAppId` vs `clientAppId`: centralizar en builder.
2. Campo `depto` vs `dpto`: confirmar payload real.
3. Diagnostico `codigoDiagnostico` vs `codigodiagnostico`: normalizar.
4. `idfinanciador` en respuesta vs `idFinanciador` en solicitud: normalizar.
5. `numeroPrescripcion` mal descrito como fecha: tratarlo como numero documental.
6. `recetasPostadatas` con error de tipeo: validar antes de usar.
7. `id` hash vs `idReceta`: guardar ambos siempre.
8. Sexo local `H/M`: validar mapeo.
9. CUIL del paciente: definir obligatoriedad real.
10. Medicamentos sensibles: confirmar flags reales de ocultamiento.
11. Duplicados: definir UX para `forzarDuplicado`.
12. Exito parcial: disenar UI antes de produccion.
13. Produccion vs HML: separar credenciales y base URL.
14. Vademecum sin cache: puede haber latencia; resolver con debounce y paginacion, no cache.
15. Idempotencia: definir conducta ante timeout luego de POST.

---

## 13. Plan de implementacion por fases

### Fase 0: Decisiones y limpieza conceptual

Entregables:

- Confirmar endpoints reales de QBI2 v9 para receta, practica, otras prescripciones, consulta y anulacion.
- Confirmar campos exactos para postdatadas y confidencialidad.
- Confirmar datos obligatorios de paciente/medico/cobertura.
- Decidir si `Qbi2` deja de llamarse POC en rutas y namespace.
- Marcar cache como legado y no usarlo en nuevas vistas.

Resultado esperado: contrato operativo cerrado para desarrollo.

### Fase 1: Modelo de datos

Entregables:

- Crear `Qbi2Documento`.
- Crear `Qbi2ItemPrescripto`.
- Crear `Qbi2Solicitud` general o adaptar `SolicitudReceta` hacia modelo general.
- Crear `Qbi2Evento`.
- Agregar campos QBI2 administrativos al paciente o crear perfil auxiliar.
- Crear perfil emisor/lugar de atencion.

Resultado esperado: se puede guardar una emision completa aunque no exista UI final.

### Fase 2: Servicios sin cache

Entregables:

- Cliente QBI2 endurecido.
- Servicios directos de catalogos.
- Builders por tipo de documento.
- Parser comun de respuesta.
- Servicios de emision, consulta y anulacion.
- Tests unitarios con respuestas simuladas.

Resultado esperado: integracion testeable por codigo, sin depender de la pantalla.

### Fase 3: UI minima dentro de historia

Entregables:

- Panel de documentos QBI2 en historia.
- Nueva receta desde historia.
- Busqueda directa de medicamento.
- Validacion de datos faltantes.
- Emision y visualizacion de PDF/verificador.

Resultado esperado: primer flujo real medico, no POC.

### Fase 4: Integracion con indicaciones

Entregables:

- Accion "Recetar" desde indicacion.
- Agrupacion de indicaciones.
- Vinculo indicacion-documento.
- Posologia propuesta desde horarios.

Resultado esperado: la medicacion interna puede originar recetas electronicas.

### Fase 5: Practicas y otras prescripciones

Entregables:

- Busqueda directa de practicas.
- Emision de practica desde solicitudes.
- Emision de otras prescripciones.
- Listado conjunto en historia.

Resultado esperado: cobertura completa de los tres generadores QBI2.

### Fase 6: Consulta, anulacion y reconciliacion

Entregables:

- Consultar estado.
- Anular.
- Manejar vencido/anulado/dispensado.
- Reconciliar `idTransaccion`.
- Vista de eventos.

Resultado esperado: ciclo de vida documental completo.

### Fase 7: Portal paciente productivo

Entregables:

- Portal como generador de solicitudes.
- Revision medica.
- Aprobacion/rechazo.
- Emision vinculada a historia.
- Mensajes claros al paciente.

Resultado esperado: renovaciones sin saltarse control medico.

### Fase 8: Hardening y salida a produccion

Entregables:

- Tests de regresion.
- Pruebas HML con casos reales.
- Configuracion productiva.
- Plan de rollback.
- Documentacion operativa.
- Monitoreo de errores QBI2.

Resultado esperado: integracion lista para operar.

---

## 14. Tests recomendados

Unitarios:

- Builder de paciente con datos completos.
- Builder rechaza datos faltantes.
- Mapeo de sexo.
- Mapeo de cobertura.
- Parser distingue `id` e `idReceta`.
- Parser detecta error con HTTP 200.
- Parser detecta emision parcial.
- Anulacion usa hash.
- Consulta usa numero documental.

Integracion con mocks:

- Receta exitosa.
- Receta con dos medicamentos.
- Receta postdatada con `idTransaccion`.
- Duplicado QBI.
- Timeout.
- HTTP 500.
- Respuesta texto/no JSON.
- Practica exitosa.
- Otra prescripcion exitosa.

UI:

- Historia muestra documentos.
- Faltan datos del paciente y bloquea emision.
- PDF y verificador aparecen al emitir.
- Anular cambia estado.
- Indicacion crea receta.
- Solicitud paciente queda pendiente y no emite sola.

---

## 15. Migracion desde la POC

Mantener de la POC:

- Cliente HTTP, con ajustes.
- Normalizadores de medicamentos, sin cache.
- Experiencia aprendida del payload HML.
- Flujo portal como solicitud pendiente.
- Manejo de `SolicitudReceta` como referencia historica.

Reemplazar:

- `Qbi2CacheEntry`.
- `MySQLCache`.
- `CachedVademecumService`.
- Pantallas `/qbi2-poc/...` como entrada principal.
- Payloads con defaults ficticios.
- `SolicitudReceta` como unico lugar donde vive la receta emitida.

Compatibilidad:

- Las rutas POC pueden quedar temporalmente detras de flag.
- La nueva integracion deberia tener namespace propio, por ejemplo `/qbi2/` o integrarse directamente en rutas de historia.
- Los datos ya emitidos por POC pueden migrarse creando `Qbi2Documento` desde `SolicitudReceta.respuesta_qbi2` cuando haya suficiente informacion.

---

## 16. Primer corte tecnico recomendado

El primer incremento que ya seria "integracion real" y no POC:

1. Crear `Qbi2Documento`, `Qbi2ItemPrescripto`, `Qbi2Evento`.
2. Implementar busqueda directa de medicamentos sin cache.
3. Implementar emision de receta desde historia.
4. Guardar hash, numero documental, PDF, verificador, payload y respuesta.
5. Mostrar documentos en historia.
6. Bloquear emision si faltan datos reales.

No incluir todavia:

- Portal paciente.
- Practicas.
- Otras prescripciones.
- Postdatadas.
- Anulacion.
- Consulta de estado.

Motivo: este corte valida el modelo documental correcto sin volver a caer en una POC aislada. Luego el mismo modelo soporta el resto.

---

## 17. Criterio final de diseno

La integracion debe ahorrar trabajo futuro evitando tres errores:

1. Modelar QBI2 como un boton que devuelve PDF.
2. Guardar solo un `idReceta`.
3. Mezclar solicitud, documento emitido y catalogo en una misma tabla.

El diseno robusto es:

- Solicitud: intencion pendiente de decision.
- Documento: resultado QBI2 con ciclo de vida.
- Item: contenido prescripto.
- Evento: trazabilidad.
- Snapshot: verdad historica de lo enviado.
- Catalogo: consulta en vivo, sin cache.

Con esa separacion, recetas, practicas, otras prescripciones, anulaciones, consultas, portal paciente e historia clinica pueden crecer sin reescribir el nucleo.
