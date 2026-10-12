*RECETAS — CÓMO QUEDA EL CIRCUITO*

Resumen de las decisiones de uso para el médico y el paciente. La versión con las últimas mejoras está disponible en local y en testing para pruebas.

*1. REGLAS GENERALES*

- El paciente pide medicación. El médico revisa el pedido, puede modificarlo y decide si emite o rechaza. Enviar un pedido no equivale a tener una receta.
- Cada pedido puede contener hasta *9 medicamentos*. Es un límite configurable del sistema, no una afirmación sobre un máximo oficial publicado por RCTA.
- Se trabaja con un pedido único, aunque RCTA genere varios documentos. El límite operativo actual contempla hasta *3 documentos por pedido*.
- Una emisión sólo se considera completa cuando la respuesta confirma que se cubrieron los medicamentos solicitados. Si falta alguno, se informa una emisión incompleta y se conservan los documentos que sí se generaron.
- Se puede elegir *Sin cobertura* para un pedido, aunque el paciente tenga obra social o prepaga registrada. Esa elección no borra su cobertura guardada.
- Los medicamentos se buscan tanto por *nombre comercial como por droga*. Se priorizan coincidencias exactas o por comienzo del nombre comercial, luego de la droga, y después coincidencias dentro de esos nombres.
- Los resultados de los buscadores se despliegan hacia abajo. Para sumar otro medicamento se usa el botón circular con *+*. No se agrega dos veces la misma presentación al mismo pedido.

*2. MÓDULO DEL PACIENTE*

*Ingreso y datos personales*

- El portal del paciente usa la gama del azul, conservando el logo del consultorio.
- Se ingresa con *documento y apellido completo*. Si el apellido es compuesto, deben figurar todas sus partes.
- Al quinto intento fallido se bloquea el ingreso para ese documento durante *10 minutos*.
- El paciente puede modificar *sexo, dirección, teléfono, celular, correo, cobertura, plan y número de afiliado*. Los cambios deben guardarse.
- El nombre, el apellido y el documento no se modifican desde este portal. Los datos clínicos y las decisiones sobre el tratamiento corresponden al médico.

*Condiciones para pedir una receta*

- El plazo máximo actual desde la última atención registrada es de *5 años*. Es configurable. La prueba temporal con 10 años ya se dejó sin efecto.
- Si no hay una atención registrada, o la última supera ese plazo, no se permite confeccionar ni enviar el pedido. El aviso explica cuál de esas situaciones ocurre y, cuando existe, informa la fecha registrada.
- Si la cobertura guardada todavía no está validada contra el catálogo, el paciente debe buscarla en *Mis datos*, elegir el plan si corresponde y guardar los cambios. También puede optar por *Sin cobertura* para ese pedido.
- *Cada impedimento tiene su propio cartel*. Si hay más de uno, se muestran todos. Resolver un problema no oculta los demás.
- Los carteles se actualizan al guardar datos, cambiar la cobertura del pedido o volver a la ventana. Elegir Sin cobertura elimina el impedimento de cobertura, pero no uno de falta de seguimiento médico.
- Aunque se intente enviar el pedido por otra vía, no llega a la cola médica mientras incumpla las condiciones aplicables.

*Confeccionar el pedido*

- Se eligen entre *1 y 9 medicamentos*, buscando por marca o droga, o usando la lista habitual.
- El paciente selecciona el medicamento y su presentación. No completa diagnósticos ni decide la aprobación del tratamiento.
- La interacción guía una elección por vez: el botón *+* queda desactivado mientras está abierto el selector, antes de elegir el primer medicamento y al alcanzar el máximo permitido.
- Antes de enviar se pueden quitar medicamentos del pedido con la *×*.
- Al enviar aparece la confirmación de recepción. El pedido queda pendiente de revisión médica y se puede consultar en *Mis pedidos*.

*Mi medicación habitual*

- Es una lista personal que se arma con medicamentos de *recetas efectivamente emitidas*, tanto a partir de pedidos del paciente como de emisiones espontáneas del médico.
- Para entrar en la lista, un medicamento debe aparecer en *al menos dos pedidos distintos emitidos*. Una solicitud aislada no alcanza; tampoco cuentan pedidos pendientes, rechazados o con error de emisión.
- La lista se ordena por *cantidad de pedidos emitidos*. Si hay empate, aparece primero el medicamento emitido más recientemente.
- Un pedido cuenta una sola vez para cada medicamento, aunque haya generado varios PDF. Dosis y presentaciones diferentes se mantienen separadas.
- Primero se muestran los *seis más frecuentes*. Con *Ver más habituales* se despliega el resto.
- *La lista habitual puede tener más de nueve medicamentos*. El límite de nueve corresponde a lo que se puede incluir en un pedido, no al tamaño de la lista personal.
- *Agregar al pedido* suma la presentación elegida. Los habituales y los medicamentos del buscador comparten el mismo límite: no son dos cupos separados.
- La *×* quita un medicamento de la lista habitual sin pedir confirmación. No borra recetas anteriores ni lo quita de un pedido que ya se esté armando. Se puede seguir encontrando en el buscador general.
- La lista es una ayuda para repetir pedidos frecuentes; no reemplaza las indicaciones del médico ni certifica que un tratamiento siga vigente.

*Mis pedidos y respuesta del médico*

- El paciente puede consultar sus pedidos, sus estados, las observaciones médicas registradas y los PDF disponibles.
- Los pedidos rechazados muestran el *motivo completo escrito por el médico*, abierto por defecto. No hay un motivo interno distinto de otro suavizado para el paciente.
- En los rechazos antiguos sin motivo se aclara que el médico no dejó uno registrado; no se inventa una explicación.
- La lista se actualiza al entrar, al volver a la ventana, después de enviar un pedido o mediante *Actualizar*. Si hay muchos pedidos, se recorren por páginas.
- Poder consultar pedidos anteriores es independiente de estar habilitado para hacer uno nuevo.
- *El rechazo se comunica dentro del portal*. Por ahora no genera un correo ni un WhatsApp automático.

*3. MÓDULO DEL MÉDICO*

*Accesos y presentación*

- En el menú *Recetas*, *Gestión* abre la cola de pedidos y *Emisión* permite confeccionar una receta espontánea.
- La pantalla médica usa la gama del rojo y el estilo de los otros menús del sistema.
- La prioridad visual está en trabajar con la receta. La navegación reúne *Nueva receta, Pendientes e Historial*; los estados secundarios no ocupan grandes tarjetas.
- Los textos dirigidos al médico mantienen una redacción impersonal, por ejemplo *Ingresar* o *Seleccionar*, evitando el tuteo.

*Emisión espontánea*

- La pantalla comienza *sin paciente seleccionado*. La búsqueda está disponible desde el inicio y permite elegir sucesivamente distintos pacientes por apellido, nombre o documento.
- Al elegir un paciente se cargan sus datos de historias clínicas y su cobertura guardada. También se puede emitir como particular mediante *Sin cobertura*.
- *Editar datos del paciente* abre la página habitual de edición en una ventana aparte. Al confirmar, se actualizan los datos y se recupera el contexto de la receta.
- El médico selecciona la fecha, los medicamentos y sus presentaciones, y puede ajustar cantidades, posología, indicaciones y texto adicional.
- El diagnóstico es obligatorio. En la emisión espontánea se puede elegir del catálogo o escribir como texto libre.
- Están disponibles las opciones de tratamiento prolongado y ocultar datos del paciente en el documento.
- La firma, el logo y los datos profesionales forman parte de la configuración del consultorio; no es necesario completarlos en cada receta ni existe un panel de perfil que ocupe la pantalla.
- Antes de emitir se pide confirmación. Durante la operación se muestra que está en curso; luego aparece el resultado explícito.

*Revisar pedidos del paciente*

- El médico puede revisar los datos personales, abrir su edición y modificar los medicamentos antes de emitir. El diagnóstico y las indicaciones corresponden al médico.
- Para emitir se usa *Aprobar y emitir*. Un error de emisión no se presenta como un rechazo decidido por el médico.
- Para rechazar, el *motivo es obligatorio*. El formulario avisa expresamente que el paciente verá ese texto. No existe una segunda explicación reservada para el médico.
- El resultado de la operación se muestra en la misma pantalla, sin obligar al médico a ir a otra bandeja para enterarse de lo ocurrido.

*Resultados y errores*

- El éxito tiene una confirmación visible; los errores muestran el motivo informado por RCTA cuando está disponible, no sólo una referencia genérica a un error HTTP.
- No se bloquea una emisión de homologación sólo por una suposición local sobre qué financiador debería ser aceptado. Los rechazos del proveedor se muestran como tales.
- Si una emisión falla sin generar documentos, se puede devolver a Pendientes para corregir y volver a intentar. Esa acción no emite automáticamente.
- Si RCTA generó sólo parte de los documentos, se informa *emisión incompleta*, se conservan los PDF y se evita un reintento automático que pueda duplicarlos.

*Historial*

- Tiene un selector discreto de *estado* para no mostrar siempre todo junto.
- Las fechas se eligen de dos maneras: *Período* —una semana, un mes, seis meses o un año— o *Desde–hasta*. Se alterna entre ambos modos.
- Por defecto se muestra *un mes*. El filtro se aplica a la fecha de creación del pedido e incluye ambos extremos. El intervalo elegido queda visible.
- Los filtros se conservan al cambiar de estado, recorrer páginas y volver de una aprobación o rechazo.
- Si quedan pendientes fuera del período, aparece un aviso con acceso a *Ver todos los pendientes*.
- Las recetas con error tienen *Quitar del historial*. Dejan de aparecer en el historial médico, pero se conservan sus antecedentes y los documentos existentes. *Quitar del historial no anula una receta en RCTA*.
- El historial no acumula avisos generales como “Paciente actualizado exitosamente” o mensajes de otros formularios. Se mantienen los resultados propios de las recetas y las validaciones necesarias para la operación en curso.

*PDF y correo*

- Los documentos emitidos se pueden abrir desde el resultado o el historial correspondiente. El paciente también puede consultar los PDF disponibles en *Mis pedidos*.
- En Gestión se puede preparar un borrador de correo con los PDF adjuntos, listo para abrir en un cliente de correo compatible, revisar y enviar.
- El asunto es: *Receta emitida por Dr. Omar Prieto Cardiología Integral*.
- El cuerpo comienza con: *Su receta está disponible a continuación*.
- El correo no se envía solo: el médico revisa el destinatario y confirma el envío.

*4. ALCANCE DE LAS PRUEBAS ACTUALES*

- Las aplicaciones local y de testing están conectadas a *homologación de QBI2/RCTA*. Los resultados de esas pruebas no equivalen a una puesta en producción.
- Una cobertura encontrada en el catálogo puede ser rechazada por las condiciones del entorno de homologación. El sistema debe informar el motivo recibido.
- Las últimas mejoras de habituales, Mis pedidos y motivos de rechazo están disponibles en testing para revisión.
- Portal del paciente: http://129.212.132.248/recetas/paciente/ingresar/
- Ingreso del médico: http://129.212.132.248/login/
