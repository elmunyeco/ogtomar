PLAN TECNICO DE IMPLEMENTACION
RECETA ELECTRONICA QBI2 EN HISTORIAS CLINICAS
PAGINA DE PEDIDO DE RECETAS DEL PACIENTE

DOCUMENTO: PLAN-RECETAS
SISTEMA: HHCC / CARDIOPRIETO
MODULO: QBI2
BASE DE TRABAJO: PLAN_INTEGRACION_QBI2_HISTORIAS.md

========================================================================
1. OBJETO
========================================================================

El objeto de este documento es definir la implementacion tecnica de la
receta electronica QBI2 dentro del sistema de historias clinicas.

El alcance incluye:

01. Integracion de documentos QBI2 dentro de la historia clinica.
02. Emision de recetas desde la historia clinica.
03. Emision de recetas desde indicaciones existentes.
04. Registro documental de practicas y otras prescripciones.
05. Pagina publica para pedido de recetas por parte del paciente.
06. Cola medica de aprobacion, rechazo y emision.
07. Consulta de estado, anulacion y auditoria.
08. Eliminacion del uso operativo de la POC como camino principal.

La receta electronica no reemplaza la historia clinica. La historia
clinica conserva la primacia funcional. QBI2 actua como sistema externo
emisor de documentos electronicos verificables.


========================================================================
2. ESTADO ACTUAL DEL CODIGO
========================================================================

El sistema se encuentra en:

    /home/eze/omar/hhcc

Aplicaciones relevantes:

    main        Historia clinica, pacientes, indicaciones.
    Qbi2        POC de vademecum, portal paciente y receta HML.

Modelos actuales relevantes:

    main.Paciente
    main.HistoriaClinica
    main.ComentariosVisitas
    main.IndicacionesVisitas
    Qbi2.SolicitudReceta

Vistas actuales relevantes:

    main.views.detalle_historia_con_historial
    main.views.indicaciones_list
    main.views.indicacion_agregar
    main.views.indicacion_editar
    Qbi2.views.pacientes_portal_page
    Qbi2.views.solicitudes_receta_page
    Qbi2.views.validar_paciente_portal
    Qbi2.views.aprobar_solicitud_receta
    Qbi2.views.rechazar_solicitud_receta

Archivos actuales de interes:

    hhcc/main/models.py
    hhcc/main/views.py
    hhcc/main/templates/detalle_historia_con_historial_2.html
    hhcc/main/templates/indicaciones/lista.html
    hhcc/Qbi2/models.py
    hhcc/Qbi2/views.py
    hhcc/Qbi2/client.py
    hhcc/Qbi2/services.py
    hhcc/Qbi2/recipes.py
    hhcc/Qbi2/portal.py
    hhcc/Qbi2/templates/Qbi2/pacientes_portal.html
    hhcc/Qbi2/templates/Qbi2/solicitudes_receta.html

Condicion actual:

    La POC permite buscar medicamentos, solicitar recetas desde portal
    paciente y emitir HML desde la cola medica. La emision queda guardada
    dentro de SolicitudReceta. No existe un documento QBI2 independiente
    asociado a la historia clinica.

Riesgo actual:

    SolicitudReceta representa intencion, decision y resultado emitido en
    una unica tabla. Esto impide modelar correctamente documentos, estados,
    anulacion, consulta, multiples items, practicas, otras prescripciones
    y respuesta completa de QBI2.


========================================================================
3. PRINCIPIO DE DISENO
========================================================================

La integracion se implementara como modulo documental.

Regla principal:

    HistoriaClinica es el eje de navegacion y de contexto clinico.
    Qbi2Documento es el registro local de un documento electronico
    emitido, intentado, consultado o anulado contra QBI2.

Consecuencias:

01. Una solicitud de receta no es una receta.
02. Una indicacion local no es una receta QBI2.
03. Una orden local PDF no es una practica QBI2.
04. Un documento QBI2 debe existir aunque la solicitud original cambie.
05. La respuesta completa de QBI2 debe persistirse para auditoria.
06. El PDF QBI2 no se genera localmente.
07. La busqueda de catalogos QBI2 se ejecuta en vivo.
08. No se usara cache operativo de catalogos QBI2.


========================================================================
4. MODELO DE DATOS OBJETIVO
========================================================================

4.1. TABLA Qbi2Documento
------------------------

Entidad principal. Representa receta, practica u otra prescripcion.

Campos:

    id
    historia_clinica_id
    paciente_id
    tipo
    origen
    estado_local
    estado_qbi2
    cliente_app_id
    qbi2_id_hash
    qbi2_id_receta
    qbi2_numero_prescripcion
    qbi2_id_transaccion
    fecha_emision
    fecha_documento_qbi2
    fecha_vencimiento_qbi2
    pdf_url
    verificador_url
    payload_enviado
    respuesta_qbi2
    errores_qbi2
    ultimo_error
    paciente_snapshot
    medico_snapshot
    cobertura_snapshot
    lugar_atencion_snapshot
    sub_emisor_snapshot
    solicitado_por_id
    emitido_por_id
    anulado_por_id
    created_at
    updated_at

Valores de tipo:

    receta
    practica
    otra_prescripcion

Valores de origen:

    historia
    indicacion
    solicitud
    portal_paciente
    manual
    reintento

Valores de estado_local:

    borrador
    listo_para_emitir
    emitiendo
    emitido
    emitido_parcial
    error_emision
    anulacion_pendiente
    anulado
    error_anulacion
    vencido
    estado_desconocido

Indices:

    (historia_clinica_id, created_at DESC)
    (paciente_id, created_at DESC)
    (tipo, estado_local)
    qbi2_id_hash
    qbi2_id_receta
    qbi2_numero_prescripcion
    qbi2_id_transaccion


4.2. TABLA Qbi2ItemPrescripto
-----------------------------

Entidad hija de Qbi2Documento.

Campos:

    id
    documento_id
    tipo_item
    reg_no
    medicamento_nombre_producto
    medicamento_nombre_droga
    medicamento_presentacion
    practica_id
    practica_nombre
    practica_categoria
    practica_tipo
    texto_libre
    cantidad
    tratamiento
    posologia
    diagnostico_texto
    diagnostico_codigo
    permite_sustitucion
    imprimir_diagnostico
    forzar_duplicado
    metadata_qbi2
    created_at
    updated_at

Valores de tipo_item:

    medicamento
    practica
    texto_libre


4.3. TABLA Qbi2Solicitud
------------------------

Entidad de intencion. Se utiliza para flujos que requieren decision
medica antes de emitir.

Campos:

    id
    historia_clinica_id
    paciente_id
    tipo
    origen
    estado
    payload_borrador
    observacion_paciente
    observacion_medico
    creada_por_id
    decidida_por_id
    documento_resultante_id
    request_ip
    request_user_agent
    fecha_decision
    created_at
    updated_at

Valores de estado:

    pendiente
    aprobada
    rechazada
    cancelada
    convertida_en_documento
    error_emision


4.4. TABLA Qbi2Evento
---------------------

Registro inmutable de auditoria tecnica.

Campos:

    id
    documento_id
    solicitud_id
    tipo_evento
    endpoint
    request_resumen
    response_resumen
    http_status
    error
    usuario_id
    ip
    created_at

Valores de tipo_evento:

    catalogo_busqueda
    payload_generado
    validacion_local_error
    emision_intento
    emision_ok
    emision_parcial
    emision_error
    consulta_estado
    anulacion_intento
    anulacion_ok
    anulacion_error


4.5. TABLA Qbi2PerfilEmisor
---------------------------

Configuracion local de medico, sello y lugar de atencion.

Campos:

    id
    activo
    nombre
    apellido
    tipo_doc
    nro_doc
    id_tributario
    profesion
    especialidad
    matricula_tipo
    matricula_numero
    sello_linea_1
    sello_linea_2
    sello_linea_3
    email
    telefono
    consultorio_nombre
    consultorio_contacto
    consultorio_email
    consultorio_direccion
    consultorio_codigo_postal
    consultorio_localidad
    consultorio_provincia
    created_at
    updated_at


========================================================================
5. IDENTIFICADORES QBI2
========================================================================

QBI2 devuelve mas de una identidad documental.

Regla:

    qbi2_id_hash se utiliza para anular.
    qbi2_id_receta se utiliza para consultar receta.
    qbi2_numero_prescripcion se utiliza para consultar practica u otra
    prescripcion.
    qbi2_id_transaccion agrupa documentos resultantes de una operacion.

No son intercambiables.

Tabla de uso:

    +--------------------------+-------------------------------+
    | Campo local              | Uso                           |
    +--------------------------+-------------------------------+
    | qbi2_id_hash             | anulacion                     |
    | qbi2_id_receta           | consulta de receta            |
    | qbi2_numero_prescripcion | consulta de practica/texto    |
    | qbi2_id_transaccion      | agrupacion / trazabilidad     |
    +--------------------------+-------------------------------+


========================================================================
6. DATOS REQUERIDOS PARA EMISION
========================================================================

6.1. PACIENTE
-------------

Datos existentes:

    tipo documento
    numero documento
    nombre
    apellido
    fecha nacimiento
    sexo
    email
    telefono
    celular
    direccion libre
    localidad
    obra social
    plan
    afiliado

Datos a agregar o normalizar:

    cuil_cuit
    provincia
    codigo_postal
    domicilio_calle
    domicilio_numero
    domicilio_piso
    domicilio_departamento
    qbi2_id_financiador
    qbi2_nro_financiador
    qbi2_plan_id
    qbi2_plan_nombre_snapshot
    afiliado_credencial

Validaciones:

    fecha nacimiento obligatoria
    email valido obligatorio si QBI2 lo requiere
    telefono o celular obligatorio
    sexo mapeado explicitamente
    domicilio estructurado obligatorio
    cobertura QBI2 resuelta si se emite con cobertura

No se usaran datos ficticios para emision productiva.


6.2. COBERTURA
--------------

La cobertura local de texto no alcanza para QBI2.

Flujo:

01. Usuario abre ficha del paciente.
02. Usuario busca financiador en QBI2 en vivo.
03. Usuario busca o selecciona plan en QBI2 en vivo.
04. Sistema guarda los identificadores elegidos en el paciente.
05. Sistema conserva snapshot del nombre seleccionado.

Esto no constituye cache de catalogo. Es dato administrativo del paciente.


6.3. MEDICO Y LUGAR DE ATENCION
-------------------------------

Los datos se obtienen de Qbi2PerfilEmisor activo.

Si no existe perfil activo, no se permite emitir.


========================================================================
7. SERVICIOS INTERNOS
========================================================================

7.1. CLIENTE HTTP
-----------------

Archivo base:

    hhcc/Qbi2/client.py

Responsabilidades:

    configurar base_url
    configurar bearer token
    configurar cliente_app_id
    aplicar timeout
    ejecutar GET y POST
    parsear JSON
    devolver texto si la respuesta no es JSON
    registrar errores sin secretos
    exponer excepciones propias

Excepciones:

    Qbi2Error
    Qbi2ConfigurationError
    Qbi2HTTPError
    Qbi2InvalidResponseError


7.2. CATALOGOS EN VIVO
----------------------

Servicios:

    Qbi2MedicamentoService.buscar(texto, pagina)
    Qbi2DiagnosticoService.buscar(texto)
    Qbi2FinanciadorService.buscar(texto)
    Qbi2PlanService.buscar(financiador, texto)
    Qbi2PracticaService.buscar(texto)

Reglas:

    no leer cache
    no escribir cache
    normalizar salida
    conservar raw solo en evento si corresponde
    devolver identificadores canonicos y campos minimos de display


7.3. BUILDERS DE PAYLOAD
------------------------

Servicios:

    build_generar_receta_payload(documento)
    build_generar_practica_payload(documento)
    build_generar_otras_prescripciones_payload(documento)

Responsabilidades:

    validar datos locales antes de invocar QBI2
    mapear paciente
    mapear medico
    mapear cobertura
    mapear lugar de atencion
    mapear items
    usar identificadores canonicos QBI2
    guardar payload antes del intento de emision

Restricciones:

    no inventar fecha de nacimiento
    no inventar email
    no inventar domicilio
    no inventar matricula
    no inventar cobertura


7.4. PARSER DE RESPUESTA
------------------------

Servicio:

    parse_qbi2_document_response(response, tipo)

Salida normalizada:

    ok
    parcial
    estado_qbi2
    id_hash
    id_receta
    numero_prescripcion
    id_transaccion
    pdf_url
    verificador_url
    fecha_documento
    fecha_vencimiento
    errores
    ultimo_error

Regla:

    HTTP 200 no implica exito documental. El cuerpo de respuesta manda.


7.5. WORKFLOWS DOCUMENTALES
---------------------------

Servicios:

    emitir_documento(documento, usuario)
    consultar_documento(documento, usuario)
    anular_documento(documento, motivo, usuario)
    reintentar_documento(documento, usuario)

Transacciones:

    El documento se bloquea con select_for_update durante emision,
    anulacion o reintento.


========================================================================
8. RUTAS PROPUESTAS
========================================================================

Rutas de historia:

    GET  /historia/<id>/qbi2/documentos/
    GET  /historia/<id>/qbi2/receta/nueva/
    POST /historia/<id>/qbi2/receta/previsualizar/
    POST /historia/<id>/qbi2/receta/emitir/
    GET  /historia/<id>/qbi2/practica/nueva/
    POST /historia/<id>/qbi2/practica/emitir/
    GET  /historia/<id>/qbi2/otra-prescripcion/nueva/
    POST /historia/<id>/qbi2/otra-prescripcion/emitir/

Rutas de documento:

    GET  /qbi2/documentos/<id>/
    POST /qbi2/documentos/<id>/consultar/
    POST /qbi2/documentos/<id>/anular/
    POST /qbi2/documentos/<id>/reintentar/

Rutas de catalogo:

    GET /qbi2/api/catalogos/medicamentos/
    GET /qbi2/api/catalogos/diagnosticos/
    GET /qbi2/api/catalogos/financiadores/
    GET /qbi2/api/catalogos/planes/
    GET /qbi2/api/catalogos/practicas/

Rutas de portal paciente:

    GET  /recetas/pedir/
    POST /recetas/api/validar-paciente/
    GET  /recetas/api/medicamentos/
    POST /recetas/api/solicitudes/

Rutas de cola medica:

    GET  /qbi2/solicitudes/
    GET  /qbi2/solicitudes/<id>/
    POST /qbi2/solicitudes/<id>/aprobar/
    POST /qbi2/solicitudes/<id>/rechazar/
    POST /qbi2/solicitudes/<id>/emitir/


========================================================================
9. INTEGRACION EN HISTORIA CLINICA
========================================================================

Pantalla:

    hhcc/main/templates/detalle_historia_con_historial_2.html

Cambios:

01. Agregar accion superior "Recetas".
02. Agregar bloque "Recetas y prescripciones electronicas".
03. Mostrar ultimos documentos QBI2 de la historia.
04. Agregar acceso a nueva receta.
05. Agregar acceso a nueva practica.
06. Agregar acceso a otra prescripcion.

Datos a mostrar:

    fecha
    tipo
    estado local
    estado QBI2
    diagnostico
    items
    PDF
    verificador
    acciones disponibles

Acciones:

    consultar estado
    anular
    reintentar
    abrir documento
    abrir payload/respuesta para soporte


========================================================================
10. INTEGRACION EN INDICACIONES
========================================================================

Pantalla:

    hhcc/main/templates/indicaciones/lista.html

Cambios:

01. Agregar accion "Recetar" por indicacion.
02. Agregar accion "Agregar a receta".
03. Agregar vista de recetas relacionadas.

Regla:

    Una indicacion local no se convierte automaticamente en receta.

Flujo de indicacion a receta:

01. Usuario selecciona indicacion.
02. Sistema abre formulario de receta QBI2.
03. Si la indicacion no tiene regNo, sistema exige busqueda en QBI2.
04. Usuario selecciona medicamento canonico.
05. Sistema propone posologia desde horarios locales.
06. Usuario completa diagnostico, cantidad y tratamiento.
07. Sistema crea Qbi2Documento.
08. Sistema crea Qbi2ItemPrescripto.
09. Sistema emite contra QBI2.
10. Sistema vincula documento e indicacion.

Tabla puente recomendada:

    Qbi2DocumentoIndicacion

Campos:

    documento_id
    indicacion_id
    metadata
    created_at


========================================================================
11. PAGINA DE PEDIDO DE RECETAS DEL PACIENTE
========================================================================

La pagina publica no emite recetas. La pagina publica crea solicitudes.

Pantalla actual a transformar:

    hhcc/Qbi2/templates/Qbi2/pacientes_portal.html

Nueva funcion:

    Pedido de renovacion de receta.

Flujo:

01. Paciente ingresa apellido.
02. Paciente ingresa documento.
03. Sistema busca paciente activo.
04. Sistema busca historia clinica principal.
05. Si no existe historia, rechaza.
06. Paciente busca medicamentos en QBI2 en vivo.
07. Paciente selecciona medicamentos.
08. Paciente ingresa observacion opcional.
09. Sistema crea Qbi2Solicitud.
10. Sistema informa recepcion de solicitud.

Datos guardados:

    paciente_id
    historia_clinica_id
    tipo = receta
    origen = portal_paciente
    estado = pendiente
    payload_borrador con medicamentos seleccionados
    observacion_paciente
    request_ip
    request_user_agent

Limites:

    maximo de medicamentos por solicitud configurado
    no se permite medicamento sin regNo
    no se permite paciente inexistente
    no se permite paciente de baja
    no se emite desde contexto anonimo


========================================================================
12. COLA MEDICA
========================================================================

Pantalla actual a transformar:

    hhcc/Qbi2/templates/Qbi2/solicitudes_receta.html

Funcion:

    Revision de solicitudes pendientes.

Datos por solicitud:

    fecha
    paciente
    historia
    documento
    medicamentos
    observacion paciente
    estado
    datos faltantes

Acciones:

    abrir historia
    aprobar
    editar y aprobar
    rechazar
    emitir

Flujo de aprobacion:

01. Usuario medico abre solicitud.
02. Sistema muestra medicamentos solicitados.
03. Usuario completa diagnostico.
04. Usuario completa posologia.
05. Usuario ajusta cantidad y tratamiento.
06. Sistema valida datos requeridos.
07. Sistema crea Qbi2Documento.
08. Sistema crea Qbi2ItemPrescripto.
09. Sistema emite contra QBI2.
10. Sistema vincula Qbi2Solicitud.documento_resultante.
11. Sistema cambia estado de solicitud.
12. Sistema registra Qbi2Evento.

Flujo de rechazo:

01. Usuario informa motivo opcional.
02. Sistema cambia estado a rechazada.
03. Sistema registra fecha_decision y decidida_por.


========================================================================
13. PRACTICAS Y OTRAS PRESCRIPCIONES
========================================================================

Practica QBI2:

01. Usuario abre historia.
02. Usuario selecciona nueva practica.
03. Usuario busca practica en QBI2 en vivo.
04. Usuario selecciona practica canonica.
05. Usuario completa diagnostico.
06. Sistema emite.
07. Sistema guarda numeroPrescripcion.
08. Sistema muestra PDF y verificador.

Otra prescripcion:

01. Usuario abre historia.
02. Usuario selecciona otra prescripcion.
03. Usuario escribe texto libre.
04. Usuario completa diagnostico.
05. Sistema emite.
06. Sistema guarda numeroPrescripcion.
07. Sistema muestra PDF y verificador.


========================================================================
14. CONSULTA, ANULACION Y REINTENTO
========================================================================

Consulta:

    receta:
        usar qbi2_id_receta

    practica u otra prescripcion:
        usar qbi2_numero_prescripcion

Anulacion:

    usar qbi2_id_hash

Reglas:

01. No anular documento sin hash.
02. No anular documento ya anulado.
03. No anular documento vencido si QBI2 no lo permite.
04. Guardar cada intento en Qbi2Evento.
05. Actualizar estado local solo despues de parsear respuesta.

Reintento:

01. Si el payload no cambia y el error fue de red, reutilizar documento.
02. Si el payload cambia, crear nuevo documento relacionado.
03. Evitar duplicacion si existe numero documental consultable.


========================================================================
15. MIGRACION DESDE POC
========================================================================

Secuencia:

01. Crear modelos nuevos.
02. Crear migraciones.
03. Mantener SolicitudReceta sin borrar.
04. Crear servicios nuevos.
05. Cambiar aprobacion actual para crear Qbi2Documento.
06. Mostrar documentos en historia.
07. Cambiar portal paciente para crear Qbi2Solicitud.
08. Cambiar cola medica para leer Qbi2Solicitud.
09. Migrar datos historicos de SolicitudReceta si corresponde.
10. Desactivar rutas de laboratorio.

Ruta POC retirada:

    /qbi2-poc/lab/receta/ (eliminada junto con su API y artefactos)


========================================================================
16. PRUEBAS
========================================================================

Pruebas unitarias:

01. Builder de receta con paciente completo.
02. Builder de receta con paciente incompleto.
03. Builder de practica.
04. Parser con respuesta exitosa.
05. Parser con errores y HTTP 200.
06. Parser con respuesta parcial.
07. Identificacion de id hash.
08. Identificacion de idReceta.
09. Identificacion de numeroPrescripcion.
10. Validacion de medico emisor.

Pruebas de servicios:

01. Busqueda de medicamento sin cache.
02. Emision exitosa.
03. Error HTTP.
04. Timeout.
05. Consulta de estado.
06. Anulacion.
07. Reintento.

Pruebas de vistas:

01. Historia muestra documentos.
02. Historia permite nueva receta.
03. Indicacion permite recetar.
04. Portal crea solicitud.
05. Cola medica aprueba solicitud.
06. Cola medica rechaza solicitud.
07. Documento emitido muestra PDF.


========================================================================
17. ORDEN DE IMPLEMENTACION
========================================================================

Etapa 01:

    Crear modelos Qbi2Documento, Qbi2ItemPrescripto, Qbi2Solicitud,
    Qbi2Evento y Qbi2PerfilEmisor.

Etapa 02:

    Crear migraciones y pruebas de modelo.

Etapa 03:

    Implementar servicios de catalogo sin cache.

Etapa 04:

    Implementar validadores de paciente, cobertura, medico y lugar de
    atencion.

Etapa 05:

    Implementar builders productivos de payload.

Etapa 06:

    Implementar parser normalizado de respuesta QBI2.

Etapa 07:

    Implementar emision de receta desde historia.

Etapa 08:

    Mostrar documentos QBI2 en historia.

Etapa 09:

    Transformar portal paciente en creador de Qbi2Solicitud.

Etapa 10:

    Transformar cola medica en aprobador y emisor.

Etapa 11:

    Integrar receta desde indicaciones.

Etapa 12:

    Implementar practicas.

Etapa 13:

    Implementar otras prescripciones.

Etapa 14:

    Implementar consulta, anulacion y reintento.

Etapa 15:

    Retirar POC como camino principal.


========================================================================
18. CRITERIOS DE ACEPTACION
========================================================================

01. Una receta emitida aparece en la historia clinica.
02. Una receta emitida conserva payload y respuesta completa.
03. Una receta emitida conserva id hash e idReceta por separado.
04. Una receta puede consultarse.
05. Una receta puede anularse usando hash.
06. Una solicitud del paciente no emite directamente.
07. La cola medica puede aprobar y emitir.
08. La cola medica puede rechazar.
09. Una indicacion puede originar receta previa seleccion QBI2.
10. No se usan datos ficticios en emision productiva.
11. No se usa cache operativo de catalogos QBI2.
12. Los errores QBI2 con HTTP 200 quedan como error semantico.
13. Practicas y otras prescripciones quedan asociadas a historia.
14. El PDF QBI2 se abre desde el enlace devuelto por QBI2.
15. El verificador se conserva y se muestra.


========================================================================
19. DECISION FINAL
========================================================================

La implementacion debe separar intencion, documento y evento.

    Qbi2Solicitud representa pedido.
    Qbi2Documento representa documento electronico.
    Qbi2ItemPrescripto representa contenido prescripto.
    Qbi2Evento representa auditoria tecnica.

La pagina del paciente crea pedidos. El medico emite. La historia clinica
conserva la trazabilidad completa.
