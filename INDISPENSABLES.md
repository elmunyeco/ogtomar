# Indispensables QBI2

## Pedido espontaneo medico

Esta pantalla debe mantenerse enfocada en confeccionar y emitir un pedido:

- elegir si es receta o practica
- completar el item medico
- completar diagnostico
- completar paciente
- completar cobertura
- completar medico y lugar de atencion
- emitir

Criterio de interfaz actual: si un campo o accion no ayuda directamente a completar ese circuito, se oculta o se mueve fuera de la pantalla principal. Si sobra, confunde, y esta mal.

## Funciones indispensables que no deben perderse

Estas funciones son importantes para un cliente QBI2 completo, aunque se hayan sacado de la pantalla de confeccion para no sobrecargarla.

### Anulacion

La anulacion es indispensable para operar documentos reales ya emitidos.

Motivo:

- permite cancelar una receta o practica emitida por error
- debe usar el hash devuelto por QBI2
- para recetas corresponde `DELETE /apirecipe/Receta/{hash}`
- para practicas corresponde `DELETE /apirecipe/Practica/{hashPrescripcion}`
- debe quedar auditada localmente cuando se integre al circuito definitivo

Decision de UI:

- no va en la pantalla principal de confeccion
- debe estar en una accion posterior, asociada al documento emitido
- debe requerir confirmacion explicita y rol autorizado

### Postdatadas

Las postdatadas pueden ser necesarias para recetas/prescripciones futuras, pero no forman parte del flujo minimo de confeccion.

Motivo:

- QBI2 contempla cantidad, dias o fechas postdatadas
- afecta la semantica del documento emitido
- requiere validaciones propias y posiblemente reglas de negocio por cobertura o practica

Decision de UI:

- no va en el formulario simple inicial
- debe volver como opcion avanzada cuando el circuito basico este claro
- debe mostrarse solo si aplica al tipo de pedido elegido

### Informacion extra

`informacionExtra` sirve para enviar pares libres `key/value` a QBI2.

Motivo:

- puede transportar datos de integracion como siniestro, prestador, referencia externa u otros identificadores
- es util para trazabilidad y conciliacion entre sistemas
- no es informacion que el medico deba cargar manualmente en el flujo normal

Decision de UI:

- no va en la pantalla principal de confeccion
- debe poblarse desde el sistema cuando exista una fuente confiable
- si se expone manualmente, debe estar en una seccion avanzada o administrativa

### Payload y respuesta tecnica

Ver payloads y respuestas crudas es util para desarrollo y soporte, pero no para el medico.

Motivo:

- ayuda a diagnosticar integraciones
- permite comparar lo enviado contra lo recibido
- sirve para depurar errores de QBI2

Decision de UI:

- no va en la pantalla principal de confeccion
- puede existir en una vista tecnica separada o detras de permisos de soporte/desarrollo
- nunca debe competir visualmente con los campos clinicos del circuito
