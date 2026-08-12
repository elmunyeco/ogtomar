# QBI2 - Campos de receta/practica

Abstract:

La pantalla es un mashup armado desde la herramienta de pruebas de innovamed (y la documentacion disponible. Es decir: sabemos que campos acepta el API y como se llaman tecnicamente, pero no siempre esta claro que significa funcionalmente cada campo en el circuito medico. La explicacion de abajo mezcla:

- lo que surge de la herramienta de pruebas de innovamed;
- lo que surge de la documentacion textual revisada;
- inferencias / adivinanza / tiro al aire

Donde dice "obligatorio funcional" significa que, aunque el Swagger (la herramienta de pruebas de innovamed) no siempre lo marque como obligatorio, me parece necesario para emitir un documento medico. Donde dice "opcional/incierto", conviene validarlo con vos, Omar.

## Tipo de pedido

### Completar

Define que clase de documento se va a emitir.

- `Receta`: usa el endpoint de receta y envia medicamentos.
- `Practica`: usa el endpoint de practica y envia una prescripcion de practica.

Obligatorio. No es texto libre.

## Receta

Panel usado cuando se quiere prescribir medicacion.

### Buscar medicamento

Campo de busqueda contra el vademecum de QBI2.

No se envia al endpoint de emision. Sirve para completar los datos reales del medicamento: `regNo`, producto, droga y presentacion.

Recomendacion: usarlo siempre que sea posible, porque reduce errores de escritura e identificacion.

### RegNo

Identificador del medicamento en el catalogo QBI2/Farmalink.

Probablemente es el campo mas importante para que QBI2 reconozca el producto. No conviene cargarlo manualmente salvo que lo conozcas con certeza.

Obligatoriedad: probablemente obligatorio para una receta validada contra vademecum.

### Producto

Nombre comercial del medicamento.

Puede ser texto, pero deberia venir del vademecum si se eligio un medicamento catalogado.

Obligatoriedad: funcionalmente importante.

### Droga

Principio activo.

Puede ser texto libre, pero si se eligio del vademecum deberia respetar lo devuelto por QBI2.

Obligatoriedad: funcionalmente importante.

### Presentacion

Forma, concentracion y envase del medicamento.

Ejemplo: `10 mg comp.x 30`.

Puede ser texto, pero conviene que venga del catalogo para evitar inconsistencias.

Obligatoriedad: funcionalmente importante.

### Cantidad

Cantidad de envases/unidades prescriptas.

Obligatorio funcional. Debe ser numerico y mayor o igual a 1.

### Tratamiento

Campo tecnico de QBI2 para tipo de tratamiento:

- `0`: normal.
- `1`: prolongado.

No es texto libre. El criterio medico define cuando corresponde cada valor.

Obligatoriedad: en esta prueba se envia siempre. en el cliente web tambien? no queda claro.

### Sustitucion

Indica si se permite o no sustitucion del medicamento.

Valores usados:

- vacio: no se envia;
- `S`: permite generico/sustitucion;
- `N`: no sustituir.

Obligatoriedad: opcional. Si se deja vacio, QBI2 aplica su comportamiento por defecto.

### Forzar duplicado

Campo tecnico para intentar emitir aunque QBI2 detecte duplicidad.

No se realmente para que carajo sirve. O lo sabe Omar o estamos fritos.

Obligatoriedad: opcional.

### Posologia

Indicacion de uso del medicamento.

Texto libre. Deberia completarla el medico.

Obligatoriedad: funcionalmente importante.

### Observacion del item

Observacion asociada al medicamento puntual, no a todo el documento. No se para que está, que significa, nada.

Texto libre.

Obligatoriedad: opcional.

## Practica

Panel usado cuando se quiere prescribir una practica/estudio/procedimiento.

Punto importante detectado: `GetPracticas` devuelve `nomenclador` con `snomed` y `nbu`, pero el campo `codigo` de la prescripcion no es necesariamente ese nomenclador. Segun la documentacion revisada, `codigo` hace referencia a un codigo propio de la practica y actualmente no se consulta ni valida contra nomencladores especificos. O sea que no es el mismo caso del vademecum

### Buscar practica

Campo de busqueda contra el catalogo de practicas de QBI2.

No se envia al endpoint de emision. Sirve para completar ID, nombre, categoria, SNOMED y NBU cuando QBI2 los devuelve.

Recomendacion: No usarlo. No verlo. Nada. No sirve para nada

### Tipo

Filtro de busqueda para practicas.

Texto libre como filtro; no esta claro funcionalmente que valores espera QBI2.

### Categoria

Como filtro: acota la busqueda de practicas.

Texto libre como filtro; no esta claro funcionalmente que valores espera QBI2.

### ID practica

Identificador interno de la practica en QBI2.

Segun la documentacion, si se envia el ID de la practica, QBI2 lo toma como dato mandatorio frente al nombre. Es decir: si ID y nombre no coinciden, manda el ID.

Obligatoriedad: recomendable cuando la practica viene del catalogo. La verdad que es una porqueria todo lo de practica.

### Nombre practica

Nombre de la practica.

Puede ser texto libre si no se envia ID. La documentacion indica que QBI2 intenta matchear el texto contra su base. Yo no lo pude comprobar.

Obligatoriedad: obligatorio funcional si no hay ID; igualmente conviene enviarlo para legibilidad.

### Codigo propio

Se envia como `codigo`.

No es SNOMED. No es NBU. Es un codigo propio/libre de la practica. La documentacion revisada dice que actualmente no se valida contra nomencladores especificos.

Texto libre.

Obligatoriedad: opcional/incierta/Al recontrapedo

### SNOMED

Se envia como `codSnomed`.

Viene de `nomenclador.snomed` cuando se elige una practica desde `GetPracticas`.

Obligatoriedad: opcional segun Swagger; clinicamente puede ser relevante si el circuito necesita codificacion normalizada, dice la documentacion. Pero no me queda claro NUNCA si alguna vez se necesita codificacion normalizada.

### NBU

QBI2 lo devuelve dentro de `nomenclador.nbu` en la busqueda de practicas.

Puede venir del catalogo. No esta claro si QBI2 la valida al emitir.

Obligatoriedad: opcional/incierta/Al recontrapedo.

### Categoria

Categoria de la practica enviada en la prescripcion.

Puede venir del catalogo. No esta claro si QBI2 la valida al emitir.

Obligatoriedad: opcional/incierta/Al recontrapedo.

### Cantidad

Cantidad de practicas solicitadas.

Obligatorio funcional. Debe ser numerico y mayor o igual a 1.

### Descripcion libre

Texto libre para describir o ampliar la practica.

Puede servir cuando el nombre/codigo no alcanza, o cuando se prescribe una practica de manera mas narrativa.

Obligatoriedad: opcional. Yo diria que siempre se use esto.

### Confidencial

Marca la prescripcion como confidencial.

No esta claro desde la documentacion funcional cuando debe usarse.

Obligatoriedad: opcional.

## Datos clinicos comunes

Estos campos se envian tanto para receta como para practica.

### Diagnostico

Campo de busqueda contra diagnosticos QBI2.

No se envia directamente. Sirve para completar texto diagnostico y codigo diagnostico.

### Texto diagnostico

Diagnostico en lenguaje humano.

Texto libre. En la prueba se envia como diagnostico general y tambien dentro del item medicamento/practica.

Obligatoriedad: obligatorio funcional para un documento medico real. La obligatoriedad tecnica exacta depende de QBI2.

### Codigo diagnostico

Codigo asociado al diagnostico.

Idealmente deberia venir del catalogo de QBI2, por ejemplo CIE-10 u otro codigo que QBI2 devuelva.

Puede quedar vacio si se usa texto libre, pero eso debe validarse con QBI2 y con el criterio medico.

Obligatoriedad: opcional/incierta.

### Imprimir diagnostico

Controla si el diagnostico aparece impreso en el documento.

Valores:

- `S`: imprimir;
- `N`: no imprimir;
- vacio: no enviar decision.

Obligatoriedad: opcional.

### Indicaciones generales

Indicaciones del documento completo.

Texto libre. No es lo mismo que posologia del medicamento.

Obligatoriedad: opcional, salvo que el medico decida que siempre debe completarse.

### Observaciones generales

Observaciones del documento completo.

Texto libre.

Obligatoriedad: opcional.

## Paciente

Datos de identificacion, contacto y domicilio del paciente.

### Nombre

Nombre del paciente.

Obligatorio funcional.

### Apellido

Apellido del paciente.

Obligatorio funcional.

### Tipo doc

Tipo de documento.

Ejemplo: `DNI`.

Deberia venir normalizado desde el sistema, no escrito a mano si hay padron local.

Obligatoriedad: obligatorio funcional.

### Nro doc

Numero de documento.

Obligatorio funcional.

### Sexo

Codigo de sexo/genero que QBI2 recibe.

Valores usados en la prueba: `M`, `F`, `X`, `O`.

No es texto libre en la UI actual.

Obligatoriedad: funcionalmente importante; validacion exacta a confirmar.

### Fecha nacimiento

Fecha de nacimiento en formato ISO (`YYYY-MM-DD`).

Obligatorio funcional para identificar paciente y validar cobertura.

### CUIL

Identificador fiscal/laboral argentino.

Texto/numerico.

Obligatoriedad: opcional si QBI2/financiador no lo exige.

### Email

Contacto del paciente.

Puede ser importante si QBI2 envia o permite acceso digital al documento.

Obligatoriedad: opcional/incierta.

### Telefono

Contacto del paciente.

Texto/numerico. No esta claro si QBI2 valida formato.

Obligatoriedad: opcional/incierta.

### Localidad

Parte del domicilio del paciente.

Texto libre.

### Provincia

Parte del domicilio del paciente.

Texto libre en la prueba; conviene normalizarlo en el sistema final.

### Ocultar paciente

Indica a QBI2 ocultar datos visibles del paciente si el circuito lo contempla.

Obligatoriedad: opcional.

### Calle

Domicilio del paciente.

Texto libre.

### Numero

Numero del domicilio.

Texto libre/corto.

### CP

Codigo postal.

Obligatoriedad: opcional/incierta.

### Pais

Codigo de pais.

En la prueba se usa `AR`.

## Cobertura

Datos de financiador, plan y afiliacion.

Pueden quedar vacios si el circuito admite paciente particular/sin cobertura. Si hay cobertura, conviene seleccionar financiador y plan desde catalogo.

### Buscar financiador

Consulta financiadores y planes en QBI2.

No se envia directamente. Sirve para completar IDs y nombres.

### ID financiador

Identificador interno de QBI2 para el financiador.

No cargar a mano salvo que se conozca.

Obligatoriedad: funcionalmente necesaria si se prescribe con cobertura.

### Nro financiador

Numero/codigo del financiador.

Puede ser distinto del ID interno. Viene del catalogo.

Obligatoriedad: funcionalmente necesaria si QBI2 lo exige para cobertura.

### Plan ID

Identificador del plan.

Obligatoriedad: opcional si no hay cobertura; probablemente necesario si el financiador exige plan.

### Plan

Nombre del plan.

Texto; conviene seleccionarlo desde el catalogo del financiador.

### Nro afiliado

Numero de afiliado del paciente.

Obligatorio funcional cuando se prescribe con cobertura.

### DNI titular

Documento del titular de la cobertura.

Puede ser necesario si el paciente no es titular o si el financiador lo exige.

Obligatoriedad: opcional/incierta.

## Medico y lugar de atencion

Datos del profesional emisor y del lugar desde donde se emite.

En el cliente definitivo, muchos de estos datos deberian venir precargados del usuario medico y no ser editables en cada emision.

### Nombre medico

Nombre del profesional.

Obligatorio funcional.

### Apellido medico

Apellido del profesional.

Obligatorio funcional.

### DNI medico

Documento del profesional.

QBI2 lo recibe como `medico.nroDoc`.

Obligatoriedad: funcionalmente importante.

### Sexo medico

Codigo de sexo/genero del profesional.

Valores usados en la prueba: `M`, `F`, `X`, `O`.

Obligatoriedad: incierta.

### Matricula tipo

Tipo de matricula.

Valores usados:

- `MN`: matricula nacional;
- `MP`: matricula provincial.

Obligatorio funcional para validez del documento medico.

### Matricula numero

Numero de matricula.

Obligatorio funcional.

### Provincia matricula

Provincia emisora de la matricula cuando aplica.

Texto/codigo a normalizar en el sistema final.

Obligatoriedad: importante para matricula provincial.

### Especialidad

Especialidad del medico.

Texto libre. Se usa tambien para matricula/sello en el payload armado.

Obligatoriedad: funcionalmente importante.

### Profesion

Profesion del emisor.

Texto libre. En este circuito normalmente `Medico`.

### CUIT

Identificador tributario del profesional.

Puede ser requerido por QBI2 o financiador.

Obligatoriedad: opcional/incierta.

### ID REFEPS

Identificador del profesional en registro/red federal, si se usa.

Obligatoriedad: opcional si no esta disponible.

### Email medico

Contacto del profesional.

Puede servir para trazabilidad o notificaciones.

### Consultorio

Nombre del lugar de atencion.

Texto libre.

### Calle consultorio

Domicilio del lugar de atencion.

Texto libre.

### Numero consultorio

Numero del domicilio del consultorio.

Texto libre/corto.

### Contacto consultorio

Telefono u otro contacto del lugar de atencion.

Texto libre.

### Email consultorio

Email del lugar de atencion.

Obligatoriedad: opcional.

## Campos importantes que no estan en la pantalla simple

Ver tambien `INDISPENSABLES.md`.

### Anulacion

Indispensable para operar documentos reales ya emitidos, pero no forma parte de la confeccion del pedido.

Endpoints:

- receta: `DELETE /apirecipe/Receta/{hash}`;
- practica: `DELETE /apirecipe/Practica/{hashPrescripcion}`.

### Postdatadas

QBI2 contempla datos de postdatadas, pero se sacaron de la pantalla simple porque agregan reglas propias.

### Informacion extra

`informacionExtra` permite enviar pares `key/value`. Es util para integracion/trazabilidad, pero no deberia cargarlo manualmente el medico salvo necesidad especifica.

### Payload/respuesta tecnica

Util para desarrollo y soporte. No debe competir con el formulario clinico del medico.
