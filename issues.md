# Issues pendientes — circuito de recetas

Última revisión: 5 de octubre de 2026  
Rama revisada: `release/rcta-produccion`  
Alcance: portal del paciente, emisión espontánea del médico y gestión de solicitudes.

## Estado de la revisión

- La revisión se realizó en el entorno local, sin emitir recetas ni generar pedidos reales.
- Se recorrieron las variantes visuales y funcionales de paciente y médico en escritorio y móvil.
- Se probaron login válido e inválido, edición de datos, búsquedas, selección de medicamentos, diagnóstico catalogado y libre, vista previa y las bandejas pendiente, aprobada, rechazada, emitida y error de emisión.
- Los casos artificiales utilizados para revisar las bandejas fueron eliminados al terminar.
- La cola real quedó intacta: 3 solicitudes emitidas, 2 rechazadas y 1 aprobada.
- Ezequiel Rodrigo Bergonzi conserva `sexo = H` (`Hombre`) en HHCC; para RCTA se transforma correctamente en `M` (`Masculino`).
- Las 62 pruebas automatizadas del proyecto finalizaron correctamente.
- No hay migraciones pendientes.
- La imagen local quedó instalada con `DEBUG=False` y las migraciones de cobertura canónica y limitación de acceso aplicadas.
- Esta ronda no fue desplegada en testing remoto.

## Corregidos en esta ronda

### 1. Verificar todos los medicamentos realmente emitidos

Innovamed no publica un máximo numérico por documento en el correo, los PDF ni el Swagger consultados. El Swagger define `medicamentos` como una lista sin `maxItems` y aclara que una llamada puede generar una o varias recetas.

La única evidencia concreta disponible es la respuesta real de homologación del 18 de septiembre de 2026: una llamada con 10 medicamentos devolvió cuatro documentos agrupados `3 + 3 + 3 + 1`. Por eso el límite no se presenta como una regla contractual de Innovamed, sino como una salvaguarda operativa configurable:

- `QBI2_MEDICATIONS_PER_DOCUMENT=3`, según lo observado en HML.
- `QBI2_MAX_DOCUMENTS_PER_REQUEST=3`, según la decisión funcional.
- Máximo actual por operación: 9 medicamentos.
- Si Innovamed confirma otra capacidad por documento, el máximo se recalcula como el producto de ambas variables. Por ejemplo, `4 × 3 = 12`.

La aplicación hace una sola llamada con el pedido completo y deja que RCTA genere los documentos. Guarda todos los documentos devueltos y compara los `RegNo` solicitados con los informados por RCTA. Una respuesta parcial queda como `error_emision`, conserva sus PDF y bloquea el reintento automático para evitar duplicados.

### 2. Persistir y proteger la emisión espontánea

La emisión espontánea ahora crea la solicitud local antes de llamar a RCTA, persiste payload, respuesta, estado, errores y todos los PDF. El botón queda deshabilitado durante la operación y cada intento lleva una clave de idempotencia única: repetir la misma operación recupera el resultado guardado sin volver a llamar al proveedor.

También usa la misma validación de cantidad e integridad que la cola médica y aparece en la gestión general de recetas.

### 3. Proteger el ingreso y la habilitación del portal del paciente

- El quinto ingreso fallido para un mismo documento lo bloquea durante 10 minutos; el documento se conserva únicamente como hash.
- Un paciente con cobertura heredada sin `idFinanciador` canónico debe actualizarla desde QBI2 antes de confeccionar o enviar un pedido.
- `Sin cobertura` continúa disponible como decisión explícita.
- El servidor impide crear una solicitud si falta esa actualización o si venció el seguimiento clínico; manipular el navegador no evita la regla.
- La antigüedad máxima se configura en el YAML único mediante `portal_pacientes.antiguedad_maxima_atencion_anios` y quedó en 5 años.
- `DEBUG` quedó desactivado y Nginx sirve los archivos estáticos recolectados.

### 4. Integrar el catálogo de facturadores de QBI2

- Paciente y médico buscan financiadores y planes en `GetFinanciadores`.
- HHCC persiste `idFinanciador` y `planId` junto con sus nombres canónicos.
- La selección vuelve a validarse en el servidor contra QBI2 antes de guardarse.
- No se incorporaron mapeos manuales ni se alteraron los rechazos de RCTA.

## Prioridad crítica pendiente

### 5. Completar el endurecimiento antes de producción

La configuración actual no es apta para exponer el portal a pacientes por Internet:

- El acceso local se realiza por HTTP.
- `ALLOWED_HOSTS=["*"]`.
- CORS permite cualquier origen.
- `X-Frame-Options` permite embeber el sistema desde otros sitios.
- Las cookies de sesión y CSRF no están marcadas como `Secure`.
- No hay redirección obligatoria a HTTPS ni HSTS.
- La configuración contiene secretos y credenciales con valores incorporados al código.

Corregir antes de liberar:

- Servir exclusivamente mediante HTTPS.
- Mover secretos y credenciales a variables o archivos privados del entorno.
- Restringir hosts y orígenes permitidos.
- Habilitar cookies seguras y protección contra framing.
- Evaluar un segundo factor sencillo —por ejemplo un código de un solo uso— porque documento y apellido son datos fáciles de conocer.

## Prioridad alta

### 6. Validar medicamentos en el servidor

El servidor acepta los datos del medicamento enviados por el navegador si contienen un `RegNo`. Se comprobó que un mensaje manipulado con `RegNo = INVENTADO-999` atraviesa la normalización local.

La cantidad ya se valida en el servidor con el máximo operativo configurable. Sigue pendiente resolver cada medicamento nuevamente contra el catálogo antes de guardar o emitir.

Corregir:

- Volver a resolver cada `RegNo` contra el vademécum antes de guardar o emitir.
- Utilizar nombre, droga y presentación devueltos por QBI2, no los enviados por el cliente.
- Rechazar identificadores desconocidos y duplicados.

### 7. Mejorar rendimiento y semántica de la búsqueda de medicamentos

Mediciones contra homologación:

- `lot`: aproximadamente 5,1 segundos, 165 resultados y 9 páginas consultadas.
- `enal`: aproximadamente 5,2 segundos, 197 resultados y 10 páginas consultadas.
- `losar`: aproximadamente 4,1 segundos, 154 resultados y 8 páginas consultadas.

Las páginas se consultan secuencialmente. Una búsqueda inexistente provoca un HTTP 404 del proveedor y la interfaz lo presenta como error, aunque semánticamente debería ser un resultado vacío.

Corregir:

- Evitar recorrer hasta 10 páginas en serie para cada búsqueda.
- Incorporar caché de búsquedas y/o consultas concurrentes controladas.
- Entregar una primera tanda rápidamente y cargar el resto bajo demanda.
- Tratar `Medicamento no encontrado` como una búsqueda sin resultados cuando corresponda.
- Mantener el orden de relevancia acordado: producto exacto/prefijo, droga exacta/prefijo y luego coincidencias internas.

### 8. Unificar el diagnóstico en gestión y emisión

La emisión espontánea permite elegir un diagnóstico del catálogo o escribir texto libre. La gestión de solicitudes sólo ofrece texto libre.

Además, el catálogo de diagnósticos conserva el orden del proveedor. Al buscar `hiper`, la primera opción fue hipertrofia de amígdalas y la segunda hipertensión esencial.

Corregir:

- Incorporar en gestión el mismo selector de catálogo más texto libre utilizado en emisión espontánea.
- Ordenar diagnósticos por coincidencia exacta, prefijo y contenido.
- Mostrar claramente cuándo se utiliza código CIE-10 y cuándo texto libre.

### 9. Incorporar seguimiento para el paciente

El paciente puede enviar una solicitud, pero el portal no muestra después si está pendiente, aprobada, rechazada, emitida o con error. Tampoco permite acceder al resultado emitido.

Corregir:

- Mostrar las solicitudes del paciente y su estado actual.
- Mostrar fecha, medicamentos y una explicación comprensible del estado.
- Permitir acceder al PDF cuando corresponda, con el mecanismo de autorización adecuado.
- No exponer detalles técnicos internos de RCTA en la vista del paciente.

## Prioridad media

### 10. Mostrar errores de validación junto al campo correspondiente

El endpoint de actualización del perfil devuelve errores por campo, pero el frontend sólo muestra el mensaje general `Revisá los datos ingresados.`. No señala qué valor debe corregirse.

Corregir:

- Renderizar el error debajo o junto a cada campo.
- Llevar el foco al primer campo inválido.
- Mantener un resumen general accesible mediante `role="alert"`.
- Conservar los valores ingresados.

### 11. Evitar solicitudes duplicadas del paciente

El botón queda deshabilitado durante una solicitud normal, pero el servidor no tiene idempotencia. Un reintento del navegador, un proxy o dos mensajes equivalentes podrían crear solicitudes duplicadas.

Corregir:

- Generar una clave de idempotencia por envío.
- Reutilizar la respuesta de una operación ya procesada.
- Evaluar una ventana corta de detección de pedidos idénticos del mismo paciente.
- Mostrar el número de solicitud confirmado al finalizar.

## Comportamientos verificados

- Las rutas anónimas del médico redirigen al login.
- El catálogo del paciente responde `401` sin sesión de paciente.
- La sesión del paciente vence a los 30 minutos.
- La identidad del paciente utilizada para emitir se vuelve a leer desde HHCC en el servidor.
- La firma rasterizada y el logo se incorporan completos al payload real; la vista previa sólo los reemplaza por una leyenda redactada.
- El sexo local `H` se transforma en `M` para RCTA.
- La interfaz médica ya utiliza redacción impersonal: `Seleccionar`, `Ingresar`, `Revisar`, etcétera.
- Las interfaces revisadas no mostraron desbordamiento horizontal en móvil.
- La cola presenta errores de RCTA con descripción, código y referencia técnica.
- La edición del paciente se abre en otra ventana y devuelve el foco al circuito de receta.
- No hay IDs HTML duplicados en las vistas médicas revisadas.
- El login del paciente conserva foco inicial, etiquetas y dimensiones táctiles adecuadas en móvil.

## Fuera de esta revisión

- El mecanismo definitivo de correo y entrega de PDF se tratará por separado.
- No se realizaron emisiones reales contra RCTA.
- No se aplicaron correcciones funcionales a partir de estos hallazgos.
