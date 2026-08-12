INFORME TÉCNICO  DQBI2-IT-014
======================================================================

MODELO DE ENTIDADES DE LA INTERFAZ QBI2 RECIPE
Especificación conceptual para integración

----------------------------------------------------------------------
DOCUMENTO N.°      : DQBI2-IT-014
REVISIÓN          : 1
FECHA             : 19 de junio de 1976
SISTEMA           : QBI2 Recipe (microservicio de recetas electrónicas)
FUENTE NORMATIVA  : DQBI2 v9 (documentación de interfaz, cap. 01-09)
CLASIFICACIÓN     : Uso técnico interno
DISTRIBUCIÓN      : Integración / Análisis de sistemas / Control de calidad
----------------------------------------------------------------------


RESUMEN

   El presente informe especifica el modelo conceptual de entidades
   que define la interfaz QBI2 Recipe, microservicio destinado a la
   generación, gestión, validación y anulación de recetas y
   prescripciones electrónicas. El documento no reproduce la
   especificación de interfaz extremo por extremo; describe el modelo
   implementable: actores del dominio, catálogos maestros, ítems
   prescriptos, documentos emitidos y elementos de control. Cada
   entidad declara dónde se materializa (solicitud, respuesta, ambas o
   solo dominio) y registra, en su propia fila, las inconsistencias de
   nomenclatura observadas en la fuente, por ser éstas el punto donde
   una integración incorrecta produce falla.

DESCRIPTORES

   Receta electrónica; prescripción; cobertura médica; catálogo
   maestro; identificador documental; anulación por código de control;
   máquina de estados; integración de sistemas.


======================================================================
1.  ALCANCE Y CRITERIO DE CLASIFICACIÓN
======================================================================

1.1  Objeto

   QBI2 Recipe es un microservicio que unifica la generación, gestión,
   validación y anulación de recetas y prescripciones electrónicas.
   Opera como interfaz única entre médicos, pacientes, financiadores y
   entidades validadoras. La interfaz expone dos clases de operación:
   buscadores (consulta de catálogos maestros) y generadores
   (operaciones transaccionales que producen un documento, su archivo
   PDF y su enlace verificador).

1.2  Criterio de clasificación de una entidad

   a)  Si el elemento aparece en el cuerpo de la solicitud o en la
       respuesta (estructura JSON), se clasifica como entidad o
       sub-entidad técnica y se documenta con su estructura.

   b)  Si el elemento no aparece en la estructura JSON pero gobierna
       reglas, validaciones o errores, se clasifica como concepto de
       dominio y se registra en la sección 7.

1.3  Niveles que no deben confundirse

   a)  Sub-entidad operativa: posee estructura propia. Ejemplos:
       RecetasPostdatadas, AccionPDF.

   b)  Atributo-bandera: indicador escalar suelto. Ejemplos:
       forzarDuplicado, permiteSustitucion, ocultarPaciente,
       imprimirDiagnostico. No debe ubicarse al nivel de una entidad.


======================================================================
2.  MAPA GENERAL: FLUJO DE DATOS
======================================================================

   El modelo se sostiene cuando se observa qué identificador egresa de
   cada catálogo e ingresa a la operación de generación.

   CONSULTA (GET)                        IDENTIFICADOR QUE VIAJA
   -------------------------------------------------------------------
   GetDiagnostico        --------------> coddiagnostico
   GetMedicamento        --------------> regNo
   GetPracticas          --------------> id (de práctica)
   GetFinanciadores      --------------> idFinanciador / planId

                          | (se compone el ítem prescripto y los
                          |  actores del documento)
                          v
   GENERACIÓN (POST)   GenerarReceta / GenerarPractica /
                       GenerarOtrasPrescripciones
                          |
                          v
   RESPUESTA           id (HASH)  +  idReceta | numeroPrescripcion
                       + s3Link (PDF) + verificador
                       [+ idTransaccion si hubo división -> N recetas]
                          |
                          v
   CONSULTA / ANULACIÓN
        - consultar  ->  idReceta / numeroPrescripcion (o idTransaccion)
        - anular     ->  id (HASH)

2.1  Cardinalidades

   ClienteApp   N:M  Financiador   (con permisos; gobierna los
                                    financiadores habilitados)
   Financiador  1:N  Plan
   Financiador  1:N  Cobertura
   Cobertura         referencia Financiador + Plan
   Receta       1:N  MedicamentoPrescripto
   Transaccion  1:N  Documento     (resultado de la división: los
                                    medicamentos, planes y postdatadas
                                    se separan en varias recetas bajo
                                    un mismo idTransaccion)

2.2  Ciclo de vida del documento emitido

   emitido ---> pendiente / autorizado ---> dispensado
      |                                          |
      +-----------> vencido                      |
      +-----------> anulado <--------------------+

   La ausencia de esta máquina de estados deja inexplicables los
   errores de anulación; en particular QBI7 (la receta ha vencido) y
   la regla que prohíbe anular recetas ya anuladas.


======================================================================
3.  ENTIDADES CANÓNICAS (COMPARTIDAS)
======================================================================

   Las entidades de esta sección se reutilizan sin variación en
   Receta, Práctica y Otras Prescripciones. Su documentación única es
   la decisión central del modelo.

3.1  Paciente
   Propósito ........ Sujeto del documento; sus datos se validan
                      contra la cobertura.
   Materialización .. solicitud (datos de entrada) e impresión en PDF.
   Identificador .... cuil (cadena, mínimo 11) / afiliadoCredencial
                      para la cobertura.
   Campos clave ..... cuil, fechaNaci (AAAA-MM-DD), email (debe
                      contener @), domicilio, cobertura.
   Obligatoriedad ... si el medicamento es sensible (p. ej. HIV), los
                      datos del paciente se codifican en el PDF, según
                      configuración del ClienteApp.
   Relaciones ....... referencia Cobertura; debe coincidir con
                      ClienteApp (QBI113).

3.2  Medico
   Propósito ........ Emisor clínico del documento.
   Materialización .. solicitud e impresión en PDF.
   Identificador .... Matricula (sub-objeto).
   Sub-objetos ...... Matricula, Sello, Domicilio.
   Relaciones ....... debe coincidir con ClienteApp (QBI113).

3.3  Matricula  (sub-entidad embebida)
   Propósito ........ Identificación matriculada del médico (nacional
                      o provincial).
   Materialización .. solicitud.
   Relaciones ....... embebida en Medico.

3.4  Sello  (sub-entidad embebida)
   Propósito ........ Texto del sello o firma a imprimir en el PDF.
   Materialización .. solicitud; se compone en el PDF.
   Campos ........... linea1, linea2, linea3 (p. ej. nombre,
                      especialidad, matrícula). Máximo aprox. 45
                      caracteres por línea.
   Obligatoriedad ... opcional.

3.5  Domicilio  (sub-entidad embebida)
   Propósito ........ Dirección estructurada (de paciente o lugar de
                      atención).
   Materialización .. solicitud.
   Campos ........... calle (mínimo 2), numero, piso, depto,
                      codigoPostal, localidad, municipio, provincia,
                      pais, observacion, direccion (texto libre
                      alternativo en una sola línea).
   Inconsistencia ... "dpto" frente a "depto"; verificar contra el
                      payload real antes de mapear.

3.6  Cobertura
   Propósito ........ Vínculo del paciente con su financiador y plan;
                      habilita la validación de cobertura.
   Materialización .. solicitud.
   Campos clave ..... afiliadoCredencial / afiliadoCrede (número de
                      afiliado), idFinanciador, nroFinanciador,
                      planId, plan.
   Prioridad ........ planId  >  plan
                      idFinanciador  >  nroFinanciador
   Relaciones ....... referencia Financiador + Plan.
   Nota ............. tieneCobertura es false por defecto; cambia si
                      la consulta de medicamento detecta cobertura.

3.7  LugarAtencion  (sub-entidad embebida)
   Propósito ........ Datos del consultorio o lugar de emisión que se
                      imprimen en el PDF.
   Materialización .. solicitud; se compone en el PDF.
   Campos ........... nombreConsultorio, domicilio, datosContacto,
                      email, logo (URL).

3.8  SubEmisor  (sub-entidad embebida)
   Propósito ........ Entidad emisora secundaria (cadena o franquicia)
                      con identidad visual propia.
   Materialización .. solicitud (opcional).
   Campos ........... nombre, cuit, direccion, logoLink, logoBase64.

3.9  InformacionExtra  (sub-entidad embebida)
   Propósito ........ Texto libre para observaciones adicionales del
                      documento.
   Materialización .. solicitud (opcional).
   Campos ........... observacion (texto libre).


======================================================================
4.  CATÁLOGOS MAESTROS (CONSULTA POR GET)
======================================================================

   No son documentos; son las fuentes de los identificadores que luego
   viajan a la generación.

   CATÁLOGO      OPERACIÓN                IDENTIF. REUTILIZADO   SALIDA
   -------------------------------------------------------------------
   Diagnostico   GetDiagnostico?text=     coddiagnostico         iddiagnostico,
                 (CIE-10)                  (p. ej. B010)          coddiagnostico,
                                                                  descdiagnostico
   Financiador   GetFinanciadores         idFinanciador, planId  idfinanciador,
                                                                  nrofinanciador,
                                                                  planes[]
   Plan          (anidado en Financiador)  planId                id, nombre
   Medicamento   GetMedicamento           regNo (n.° de          regNo,
                                          registro del           tieneCobertura,
                                          producto)              nombre/droga/
                                                                  presentación
   Practica      GetPracticas?clienteAppId= id (de práctica)     id, practica,
                                                                  categoria, tipo

4.1  Inconsistencias de catálogo

   a)  Diagnostico: "codigoDiagnostico" frente a "codigodiagnostico"
       según la operación.
   b)  Financiador: la respuesta emplea minúsculas (idfinanciador,
       nrofinanciador) mientras el cuerpo de generación emplea
       notación mixta (idFinanciador, nroFinanciador).

4.2  Reglas de prioridad de catálogo

   a)  regNo presente vuelve opcionales nombre, droga y presentación
       del medicamento.
   b)  id de práctica  >  nombre de práctica.
   c)  profesión  >  especialidad.


======================================================================
5.  ÍTEMS PRESCRIPTOS (CONTENIDO CLÍNICO)
======================================================================

   En esta sección residen las diferencias reales entre los tres
   generadores. Comparten el esqueleto de actores de la sección 3,
   pero difieren en el ítem.

5.1  MedicamentoPrescripto  (operación GenerarReceta)
   Identificador .... regNo (si está presente, vuelve opcionales
                      nombre, droga y presentación).
   Banderas ......... permiteSustitucion ("S"/"N", altera el PDF),
                      imprimirDiagnostico ("S"/"N"/"").
   Cardinalidad ..... Receta 1:N MedicamentoPrescripto.

5.2  PracticaPrescripta  (operación GenerarPractica)
   Identificador .... id de práctica (del catálogo).
   Nota ............. una práctica equivale a una orden de servicio
                      clínico.

5.3  PrescripcionLibre  (operación GenerarOtrasPrescripciones)
   Identificador .... sin código de catálogo: texto libre.
   Nota ............. posología y diagnóstico como texto libre o
                      CIE-10 (p. ej. "Resfriado leve").


======================================================================
6.  DOCUMENTO EMITIDO Y CONTROL
======================================================================

6.1  DocumentoPrescripto (respuesta)

   Entidad común de respuesta, con dos variantes: RecetaEmitida
   (GenerarReceta) y PrescripcionEmitida (GenerarPractica /
   GenerarOtrasPrescripciones).

   Doble identificador:

   CAMPO               TIPO                 SEMÁNTICA      USO
   -------------------------------------------------------------------
   id                  HASH (cadena;        identidad      ANULAR
                       p. ej.               del documento
                       K7G94MRNDMASMS...)
   idReceta            cadena numérica      número         CONSULTAR
                       (p. ej.              documental
                       100023659898)
   numeroPrescripcion  cadena               número         CONSULTAR
                                            documental
                                            (variante
                                            Otras Prescr.)

   ADVERTENCIA. Tratar id e idReceta como un único "id" produce falla
   de integración. El primero anula; el segundo consulta. No son
   intercambiables.

   Campos de la respuesta:

   id ................... HASH (anulación).
   idReceta /
   numeroPrescripcion ... número documental (consulta).
   fecha ................ fecha de emisión (DD/MM/AAAA).
   s3Link ............... enlace de descarga del PDF.
   verificador .......... enlace de verificación del emisor y datos.
   status / estado ...... posición en el ciclo de vida (sección 2.2).

   INCONSISTENCIA. El campo numeroPrescripcion figura en la fuente
   descrito como "Fecha de emisión de la prescripción"; el valor real
   es un número documental. No debe confiarse en la descripción.

6.2  RecetasPostdatadas  (sub-entidad operativa)
   Propósito ........ Generar varias recetas con fechas futuras a
                      partir de una sola solicitud.
   Materialización .. solicitud.
   Campos ........... cantidad, diasAPosdatar, fechas[] (alternativa
                      explícita).
   Efecto ........... produce división -> varias recetas bajo un
                      idTransaccion. Existe un máximo de postdatadas
                      permitidas; excederlo es error.
   Inconsistencia ... figura como "recetasPostadatas" (error de
                      tipeo) en el ejemplo de payload. Verificar el
                      nombre exacto.

6.3  AccionPDF  (sub-entidad operativa)
   Propósito ........ Controlar la generación o entrega del PDF
                      resultante.
   Materialización .. solicitud / control.

6.4  Errores[] e idTransaccion  (resultado parcial)
   Propósito ........ Reportar fallas, totales o parciales, de la
                      transacción.
   Materialización .. respuesta.
   Campos ........... error (código QBI, p. ej. QBI136), mensaje,
                      idTransaccion.
   Relación ......... idTransaccion agrupa las N recetas de la
                      división.

   ADVERTENCIA. El código HTTP 200 no implica éxito total. Una
   respuesta 200 puede contener fallas parciales en errores[] o
   response[] bajo un idTransaccion; debe inspeccionarse el cuerpo, no
   sólo el código HTTP. Errores pertinentes: QBI153 (no se encontró
   información para el idTransaccion) y QBI154 (debe ingresarse
   idTransaccion, o bien número de receta más número de financiador).

6.5  Atributos-bandera (no son entidades)

   Indicadores escalares de la solicitud. Se registran aquí para que
   no se confundan con sub-entidades.

   forzarDuplicado ...... booleano. Fuerza la emisión aun detectando
                          un duplicado de negocio.
   permiteSustitucion ... "S"/"N". Altera el PDF (permite sustitución
                          por genérico).
   ocultarPaciente /
   confidencial ......... booleano. Oculta o codifica los datos del
                          paciente en el PDF.
   imprimirDiagnostico .. "S"/"N"/"". Imprime o no el diagnóstico en
                          el PDF.


======================================================================
7.  CONCEPTOS DE DOMINIO (NO SON ENTIDADES JSON)
======================================================================

   No aparecen como objetos en solicitud o respuesta. Gobiernan
   reglas, validaciones y errores.

   CONCEPTO     DESCRIPCIÓN                       APARICIÓN
   -------------------------------------------------------------------
   ClienteApp   Ancla de identidad y              sólo como clienteAppId
                autorización (ver 7.1).           (escalar), no objeto.
   Mandataria   Entidad que delega o gestiona     glosario y errores
                la emisión.                       (QBI143/144).
   Validador    Entidad validadora de la          glosario y errores.
                prescripción.
   Alfabeta     Proveedor de la base de           explica el origen de
                medicamentos.                     regNo.
   Farmacia     Punto de dispensa.                explica el estado
                                                  "dispensado".
   Verum        Verificador externo del           enlace en
                documento.                        verificador.

7.1  ClienteApp como ancla de autorización

   Aunque viaja como escalar clienteAppId, gobierna el contexto de
   autorización y se trata como concepto de primer orden:

   a)  Define qué financiadores puede usar la integración (QBI234,
       QBI125).
   b)  Define los permisos de operación (QBI69).
   c)  Controla la codificación de regNo sensible (p. ej.
       medicamentos HIV) y la de los datos del paciente.
   d)  Aporta logos e identidad visual del PDF.
   e)  Debe coincidir con médico y paciente del documento (QBI113).

   INCONSISTENCIA. "clienteAppId" frente a "clientAppId" según la
   operación. Mapeada incorrectamente, rompe la autorización.


======================================================================
APÉNDICE A.  REGISTRO DE INCONSISTENCIAS CONOCIDAS
======================================================================

   INCONSISTENCIA                          UBICACIÓN          RIESGO
   -------------------------------------------------------------------
   clienteAppId / clientAppId              autorización       falla de
                                                              permisos
   dpto / depto                            Domicilio          dato no
                                                              mapeado
   codigoDiagnostico /                     Diagnostico        diagnóstico
   codigodiagnostico                                          perdido
   idfinanciador (resp.) /                 Financiador,       cobertura no
   idFinanciador (sol.)                    Cobertura          resuelta
   numeroPrescripcion descrito             Prescripcion       id documental
   como "fecha"                            Emitida            mal interpretado
   recetasPostadatas (error de tipeo)      RecetasPostdatadas campo no
                                                              enviado
   id (HASH) tratado como idReceta         documento emitido  anulación y
                                                              consulta
                                                              cruzadas

----------------------------------------------------------------------
FIN DEL DOCUMENTO DQBI2-IT-014
----------------------------------------------------------------------
