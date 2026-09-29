# Handoff para presupuestar la integración RCTA / QBI2

- Fecha de corte: 17 de septiembre de 2026
- Repositorio: `/home/eze/omar`
- Rama de trabajo: `qbi2/poc-integracion`

## 1. Propósito de este documento

Este documento reúne el trabajo realizado alrededor de la integración de
receta electrónica RCTA/QBI2 con el sistema de historias clínicas HHCC. Está
preparado para abrir una sesión separada dedicada exclusivamente a estimar:

1. esfuerzo real aproximado;
2. valor de reposición por un proveedor o desarrollador especializado;
3. presupuesto comercial recomendable para el cliente.

No contiene credenciales, tokens, contraseñas, datos legales privados, firma
biométrica ni datos personales completos. Los importes de Innovamed que se
incluyen son costos históricos del proveedor, no el valor del desarrollo.

## 2. Resumen ejecutivo

El alcance fue considerablemente mayor que construir una pantalla. Incluyó:

- gestión técnica y administrativa con Innovamed/RCTA;
- estudio de la documentación y del contrato de API;
- alta del cliente y recepción segura del ambiente de homologación;
- desarrollo de un cliente HTTP QBI2 con autenticación y manejo de errores;
- integración con medicamentos, diagnósticos, financiadores y prácticas;
- construcción de payloads de receta y práctica;
- emisión, previsualización, consulta de resultados y anulación de documentos;
- portal de solicitudes del paciente y cola de decisión médica;
- integración con pacientes reales de HHCC;
- cliente de receta simplificado inspirado en la interfaz de RCTA;
- configuración externa del médico, matrículas, sello, firma y marca;
- pruebas automatizadas y verificaciones reales contra HML;
- varios ciclos de UX, corrección y despliegue;
- diagnóstico de un incidente de recursos en QA y hardening del servidor;
- documentación funcional, técnica, operativa y de continuidad.

Al corte de este documento, el cliente simplificado está desplegado en QA y
responde en:

`http://129.212.132.248/recetas/lab/rcta-espontanea-2/`

La ruta redirige correctamente al login. La aplicación y sus bases están
activas. No se debe interpretar este estado como habilitación productiva:
siguen existiendo requisitos externos de Innovamed y decisiones de arquitectura
para una integración definitiva.

## 3. Gestión ante Innovamed / RCTA

Fuente principal: cadena de correo `Contacto RCTA integraciones.eml`, iniciada
por Innovamed y conservada localmente. La evidencia original contiene
credenciales HML y datos administrativos; no debe copiarse a presupuestos ni
entregables públicos.

### 3.1 Cronología de la gestión

#### 10 de abril de 2026 — contacto inicial de Innovamed

Innovamed presentó:

- propósito de la API QBI2/RCTA;
- alcance general de receta electrónica y red de dispensa;
- funcionalidades de creación de recetas, medicamentos, diagnósticos,
  vademécum y posdatado;
- documentación técnica en Atlassian;
- etapas formales de integración;
- datos administrativos necesarios para dar de alta al cliente;
- propuesta económica por volumen de prescripciones.

Las etapas informadas por Innovamed fueron:

1. presentación de documentación técnica;
2. alta de cliente;
3. entrega de claves de prueba;
4. desarrollo del cliente con soporte de Innovamed;
5. testing;
6. certificación;
7. producción.

#### 11 de abril de 2026 — respuesta de alta

Se respondió a Innovamed identificando la aplicación, sus responsables y sus
canales de contacto. Esta tarea fue parte de la coordinación necesaria para
obtener acceso técnico; no fue trabajo puramente programático.

#### 12 de mayo de 2026 — corrección y ampliación administrativa

Se enviaron datos corregidos de la aplicación y la entidad usuaria, incluyendo
la aclaración de que existían ambientes de producción y QA. También se
completaron los datos legales solicitados para el alta. Los valores concretos
se omiten aquí por privacidad.

#### 13 de mayo de 2026 — habilitación de homologación

Innovamed entregó:

- URL del ambiente HML;
- credenciales de prueba e identificador de aplicación;
- enlace a documentación actualizada;
- contacto con soporte de integraciones;
- contacto con administración para contrato y precios;
- requisitos para obtener las claves productivas;
- dos casos obligatorios de certificación.

Las credenciales se conservaron fuera del código y no se reproducen en este
documento.

### 3.2 Requisitos externos para producción

Innovamed indicó que, para entregar claves productivas, se requiere:

1. contrato firmado;
2. registro como recetario en RENAPDIS;
3. certificación de la integración con los casos solicitados.

Estos trámites no deben confundirse con el desarrollo. Al presupuestar conviene
separar:

- gestión ya realizada;
- acompañamiento de certificación pendiente;
- gestión contractual/RENAPDIS, si se contrata;
- soporte posterior para salida a producción.

### 3.3 Datos de certificación proporcionados

Innovamed indicó para HML:

- OSDE — número de afiliado de prueba `23200126801`;
- Accord Salud — número de afiliado de prueba `23256785`.

Son casos de certificación, no una lista exhaustiva de financiadores admitidos
por la plataforma.

### 3.4 Propuesta económica histórica de Innovamed

El correo del 10 de abril de 2026 informó estos precios mensuales por volumen,
sin IVA:

| Prescripciones mensuales | Precio informado |
| --- | ---: |
| 0 a 500 | Bonificado |
| 501 a 3.000 | ARS 52.900 |
| 3.001 a 5.000 | ARS 105.800 |
| 5.001 a 10.000 | ARS 211.500 |
| 10.001 a 20.000 | ARS 353.000 |
| Más de 20.000 | ARS 494.200 |

Estos valores son históricos, pueden haber cambiado y pertenecen al servicio
de Innovamed. No incluyen el desarrollo, mantenimiento, soporte ni gestión de
esta integración.

### 3.5 Trabajo de gestión que debe valorarse

- lectura y clasificación de la propuesta y documentación;
- recopilación, envío y corrección de datos de alta;
- coordinación entre titular, desarrollador, administración y soporte;
- recepción y custodia de credenciales;
- traducción de requisitos de certificación a casos técnicos;
- seguimiento de condiciones para producción;
- documentación interna para no perder decisiones ni repetir investigación.

## 4. Investigación y diseño técnico

Se analizó la API y se documentaron:

- autenticación Bearer y parámetros de aplicación;
- endpoints y entidades;
- diferencias de nombres entre respuestas y solicitudes;
- forma variable de listas y errores del proveedor;
- medicamentos, financiadores, planes, diagnósticos y prácticas;
- receta, práctica, posdatado, confidencialidad y sustitución;
- identificación documental, hash, número de receta, PDF y verificador;
- anulación por hash;
- errores semánticos devueltos incluso con HTTP 200;
- necesidad de conservar payload y respuesta para auditoría;
- separación conceptual entre solicitud, indicación clínica y documento
  efectivamente emitido;
- estrategia sin caché operativo para catálogos vivos de QBI2.

La documentación generada no fue meramente narrativa: funciona como análisis
funcional, especificación de campos, plan de arquitectura, matriz de riesgos y
guía de implementación.

## 5. Componentes desarrollados

### 5.1 Cliente HTTP QBI2

Se desarrolló una capa de cliente con:

- configuración por settings/entorno;
- URL base, token, identificador de aplicación y timeout;
- modos de autenticación;
- GET, POST y DELETE;
- serialización y decodificación JSON;
- normalización segura de URL en logs;
- clasificación de errores de configuración, HTTP, red y timeout;
- conservación del payload de error del proveedor para mostrar información
  útil al usuario.

### 5.2 Servicios de catálogos

Se implementaron servicios y normalizadores para:

- vademécum/medicamentos;
- diagnósticos;
- financiadores y planes;
- prácticas;
- paginado y variantes de forma de respuesta.

La decisión actual es consultar QBI2 en vivo y no mantener una copia operativa
del catálogo.

### 5.3 Constructores de payload y respuestas

Se desarrollaron constructores para:

- receta electrónica;
- práctica/pedido;
- paciente y domicilio;
- cobertura;
- profesional y lugar de atención;
- medicamentos, cantidad, tratamiento, sustitución y posología;
- diagnóstico codificado o texto libre;
- observaciones e indicaciones;
- campos de confidencialidad;
- firma, sello y logo;
- información extra;
- posdatado;
- resumen de respuesta con identificadores, PDF, verificador y errores.

También se implementaron preview local, emisión real HML y anulación por hash.

### 5.4 Portal del paciente y cola médica

Se construyó una PoC completa de solicitud de receta:

- validación del paciente contra historias clínicas;
- búsqueda directa de medicamentos;
- selección y agrupación de medicamentos;
- creación de solicitudes vinculadas a paciente e historia;
- auditoría de IP, agente de usuario y datos solicitados;
- estados pendiente, aprobada, rechazada, emitida, error y anulada;
- pantalla del médico para aprobar o rechazar;
- persistencia de payload, respuesta, error, identificador y PDF.

### 5.5 Cliente espontáneo completo

Se creó una pantalla técnica/piloto que permite:

- elegir receta o práctica;
- consultar medicamentos;
- consultar diagnósticos;
- consultar financiadores;
- consultar prácticas;
- armar y revisar el payload;
- emitir;
- mostrar respuesta técnica;
- abrir PDF/verificador;
- anular por hash.

Esta pantalla se conservó como herramienta técnica y referencia funcional.

### 5.6 Cliente simplificado `_2`

Se desarrolló un segundo cliente enfocado en el flujo real del profesional. Las
iteraciones incluyeron:

- diseño visual simplificado en gama roja;
- eliminación de encabezados, insignias y paneles innecesarios;
- panel de medicamentos con icono de cápsula;
- columna equilibrada con indicaciones debajo de medicamentos;
- búsqueda permanente de pacientes, sin paciente predeterminado;
- búsqueda repetible por apellido, nombre o DNI;
- selección y reemplazo ilimitado del paciente;
- carga de datos reales desde la base HHCC;
- visualización de sexo, fecha de nacimiento y contacto;
- enlace al editor canónico del paciente;
- edición en ventana auxiliar y recuperación del foco/contexto;
- refresco de los datos después de confirmar una edición;
- diagnóstico mediante catálogo o texto libre;
- medicamentos mediante vademécum vivo;
- revisión local del payload sin emitir;
- cobertura opcional y opción explícita “Sin cobertura”;
- eliminación de un mapeo local arbitrario de financiadores;
- propagación de los errores reales de QBI2;
- botón “Emitir en HML” permanentemente habilitado por decisión del usuario;
- confirmación antes del POST de emisión;
- aclaración fija “exclusivo Ezequiel” debajo de “Revisar datos”.

La interfaz no decide actualmente si una obra social está admitida por QBI2.
Si el payload es rechazado, debe mostrarse el mensaje real del proveedor.

## 6. Perfil profesional, firma, matrículas y marca

Se externalizó el perfil de emisión a un YAML privado fuera de la interfaz y
fuera del control de versiones. Incluye estructura para:

- identidad del médico;
- profesión y especialidad;
- matrícula nacional y provincial;
- sello de tres líneas;
- consultorio y domicilio;
- contacto;
- firma rasterizada;
- logo profesional/institucional.

También se realizó el tratamiento de activos gráficos:

- firma convertida a PNG con transparencia;
- logo preparado en PNG transparente;
- resolución de rutas relativas al YAML;
- incorporación como Base64 al payload cuando corresponde;
- redacción de imágenes en respuestas de diagnóstico/preview;
- exclusión de activos privados mediante `.gitignore`;
- despliegue mediante volumen de solo lectura.

## 7. Verificación real en HML

La integración no quedó sólo simulada. La evidencia local documenta:

1. una primera solicitud rechazada por HML con código `QBI184`; no generó una
   receta;
2. corrección del juego de datos usando la credencial de certificación OSDE;
3. emisión exitosa de una receta HML para el paciente de prueba autorizado;
4. recepción de número de receta, hash, PDF y estado correcto;
5. inspección visual del PDF con paciente, medicamento, firma, sello MN/MP y
   marca profesional.

La receta exitosa está documentada como no anulada. Después de esa prueba se
trabajó con la regla de no emitir recetas durante el estudio y los smoke tests
de interfaz.

## 8. Pruebas y aseguramiento de calidad

Se crearon pruebas para rutas, servicios, búsquedas, portal, cola médica,
payloads, preview, emisión simulada, errores del proveedor, anulación y cliente
simplificado.

Hitos registrados:

- baseline de 22 pruebas QBI2 correctas durante la etapa inicial;
- suite focalizada `main + Qbi2` con 34 pruebas correctas al consolidar HHCC;
- suite actual del cliente simplificado con 21 pruebas correctas;
- `manage.py check` sin errores en deploy;
- validación de sintaxis Compose y revisión HTTP posterior a cada release.

Política actual:

- tests sólo en desarrollo o runner aislado;
- nunca ejecutar la suite Django en el pequeño servidor QA;
- en QA usar únicamente `manage.py check`, logs y smoke HTTP;
- no emitir recetas como prueba de despliegue.

## 9. Despliegue, operación e incidente de QA

### 9.1 Trabajo de despliegue

- construcción y etiquetado de imágenes Docker;
- releases incrementales mediante capas overlay;
- backup/tag de rollback antes de promover `latest`;
- recreación exclusiva de `hhcc_app`, sin tocar las bases;
- perfil YAML montado como volumen de solo lectura;
- Nginx y ruta integrada al stack existente;
- verificación de proceso, logs, límites y HTTP;
- documentación de procedimientos y rollback.

### 9.2 Diagnóstico del incidente

Durante una validación en QA, la suite de tests agotó recursos del host de
1 vCPU y aproximadamente 1 GiB de RAM. El análisis posterior incluyó:

- revisión de OOM del kernel;
- análisis de `journald`, `sar`, carga, cola de procesos e I/O;
- inspección de MariaDB y PostgreSQL;
- descarte de errores de disco/EXT4;
- identificación de consumo reiterado de `fwupd`;
- identificación del autoreloader de Django como segundo proceso innecesario;
- verificación de contenedores sin límites de memoria o PIDs;
- revisión de intentos SSH durante la indisponibilidad.

No se modificó la configuración de SSH porque el usuario excluyó expresamente
esa medida.

### 9.3 Remediaciones aplicadas

- swap persistente de 1 GiB;
- `vm.swappiness=10`;
- `fwupd` y timer deshabilitados/enmascarados;
- Django `runserver --noreload` con un único proceso;
- límites de memoria, swap y PIDs para HHCC, MariaDB, Nginx, Holter y
  PostgreSQL;
- runbook que prohíbe tests en QA;
- limpieza de dos transferencias antiguas;
- eliminación controlada de 31 volúmenes anónimos huérfanos;
- limpieza de imágenes, tags, caché y releases obsoletos;
- preservación explícita de volúmenes activos y nombrados.

La limpieza redujo inicialmente el uso de disco de 74% a 49%. Al corte de este
documento el host se encuentra aproximadamente en 50%, con 12 GiB libres.

### 9.4 Estado verificado el 17 de septiembre de 2026

- `hhcc_app`: activo, cero reinicios;
- `hhcc_nginx`: activo;
- MariaDB HHCC: activa;
- Holter app: activa;
- PostgreSQL Holter: activa y saludable;
- Django: un proceso `runserver --noreload`;
- swap: 1 GiB activa;
- URL RCTA `_2`: responde `302` al login esperado.

Advertencia: el uso de `runserver --noreload` es adecuado como mitigación de
QA, pero no sustituye un servidor WSGI/ASGI productivo. Una salida a producción
debe presupuestar ese hardening por separado.

## 10. Documentación producida

| Documento | Propósito |
| --- | --- |
| `API_ENTITIES.md` | Mapa de entidades, endpoints y relaciones de la API. |
| `QBI2_RCTA_ESPONTANEA_CAMPOS.md` | Especificación campo por campo de receta y práctica. |
| `PLAN_INTEGRACION_QBI2_HISTORIAS.md` | Arquitectura objetivo, casos de uso, estados, riesgos y fases. |
| `PLAN_RECETAS.md` | Plan funcional/técnico amplio de prescripciones. |
| `QBI2_HML_CERTIFICACION.md` | Casos HML, resultado de certificación y advertencias. |
| `VERIFICACION_HHCC_QBI2_20260811.md` | Alcance y pruebas verificadas. |
| `20260811-185726.md` | Continuidad histórica de sesiones y repositorios. |
| `DEPLOYMENT_MODES.md` | Modos de deploy y actualización segura. |
| `INDISPENSABLES.md` | Funciones QBI2 que no deben perderse. |
| `deploy/QA_RUNBOOK.md` | Operación segura, verificación y limpieza de QA. |
| `hhcc/private/qbi2/README.md` | Manejo privado del perfil y los activos del profesional. |

También se generaron estilos y versiones PDF de documentación extensa para
facilitar revisión y entrega.

## 11. Evidencia principal en Git

Los tamaños de commits sirven como evidencia de actividad, pero no deben
sumarse como líneas netas facturables: algunos consolidan, mueven o eliminan
experimentos anteriores.

| Commit | Fecha | Resultado principal |
| --- | --- | --- |
| `a7d8d819` | 14/05/2026 | Primera integración exitosa con API QBI2. |
| `e6ef8405` | 22/05/2026 | PoC de confección de recetas HML. |
| `85226815` | 24/05/2026 | Portal del paciente y cola médica. |
| `783981ff` | 04/06/2026 | PoC agrupada en namespace aislado y preparada para QA. |
| `950f7a5e` | 04/06/2026 | Normalización del app label para QA. |
| `558f86de` | 11/08/2026 | Consolidación de piloto, HHCC y documentación integral. |
| `81fd6cb6` | 16/09/2026 | Cliente simplificado `_2` y perfil YAML privado. |
| `1cccb5f1` | 16/09/2026 | Simplificación de cabecera. |
| `faac82eb` | 16/09/2026 | Enlace al editor canónico del paciente. |
| `08d5ee05` | 16/09/2026 | Preservación de contexto al editar/cambiar paciente. |
| `95b80989` | 16/09/2026 | Búsqueda permanente y repetible de pacientes. |
| `c2f04d9d` | 16/09/2026 | Cobertura opcional / sin cobertura. |
| `ec41ac6f` | 16/09/2026 | Estabilización de recursos y runbook de QA. |
| `f1ec2eb8` | 16/09/2026 | Aclaración fija debajo de revisión. |
| `e426a7b1` | 16/09/2026 | Eliminación de mapeo arbitrario de financiadores. |
| `5c7f260e` | 16/09/2026 | Emisión HML siempre habilitada por requerimiento. |

Como referencia de escala, los componentes actuales de `hhcc/Qbi2`, sus
templates y tests representan varios miles de líneas, además de más de 3.000
líneas de análisis y documentación específica. La complejidad y la evidencia
funcional son mejores unidades de valoración que el conteo bruto de líneas.

## 12. Paquetes de trabajo para cotizar

Conviene presupuestar por paquetes separados para no ocultar actividades:

### A. Gestión de proveedor y onboarding

- comunicaciones con Innovamed;
- alta/corrección de cliente;
- recepción de HML;
- seguimiento de soporte, administración y requisitos productivos.

### B. Discovery y análisis funcional

- lectura de contrato de API;
- investigación de endpoints y formas reales de respuesta;
- modelado de casos de uso, estados, auditoría y riesgos;
- especificación de campos.

### C. Núcleo de integración QBI2

- cliente HTTP;
- autenticación;
- servicios de catálogo;
- normalización;
- errores;
- builders y parsers.

### D. PoC técnica completa

- receta/práctica espontánea;
- preview;
- emisión;
- PDF/verificador;
- anulación;
- diagnóstico técnico.

### E. Portal paciente y flujo médico

- validación HHCC;
- solicitud;
- modelo persistente;
- cola;
- aprobación/rechazo;
- auditoría.

### F. Cliente simplificado y UX

- diseño visual;
- múltiples iteraciones con feedback;
- búsqueda/edición de paciente;
- medicamentos;
- diagnóstico;
- cobertura;
- revisión/emisión;
- mensajes reales de proveedor.

### G. Identidad profesional y activos

- YAML externo;
- MN/MP y sello;
- firma rasterizada;
- logo;
- Base64;
- privacidad y deploy.

### H. QA, pruebas y certificación

- pruebas automatizadas;
- pruebas de integración;
- debugging de respuestas HML;
- caso real de certificación;
- inspección de PDF.

### I. DevOps, incident response y hardening

- imágenes y deploys;
- rollback;
- diagnóstico OOM/I/O;
- swap, servicios y límites;
- limpieza Docker;
- runbook operativo.

### J. Documentación y transferencia

- planes;
- especificación de campos;
- mapa de API;
- estado de certificación;
- continuidad entre sesiones;
- operación segura.

## 13. Pendientes y exclusiones importantes

No conviene vender el estado actual como integración productiva terminada. Se
deben explicitar, según el contrato comercial, los siguientes pendientes:

- confirmar firma del contrato de Innovamed;
- confirmar/gestionar registro RENAPDIS;
- completar certificación formal con Innovamed y obtener aceptación escrita;
- recibir y configurar claves productivas;
- definir el catálogo real de financiadores/planes sin reglas hardcodeadas;
- decidir dónde persistir IDs canónicos elegidos para cada paciente;
- desarrollar el modelo documental definitivo propuesto en los planes;
- integrar receta desde la historia clínica como flujo productivo final;
- completar reconciliación, consulta, reintento y auditoría productiva;
- revisar seguridad, permisos, trazabilidad y protección de datos;
- sustituir `runserver` por un runtime productivo;
- TLS/dominio y observabilidad productiva;
- pruebas exhaustivas de módulos clínicos especializados;
- capacitación, garantía y soporte posproducción.

Algunos de estos puntos tienen PoC o diseño ya realizado; no todos están
cerrados como producto.

## 14. Riesgos para el presupuesto

- La documentación del proveedor puede cambiar.
- HML y producción pueden comportarse distinto.
- La semántica de financiadores/planes requiere validación con datos reales.
- El sistema HHCC contiene datos legacy y campos incompletos.
- Los requisitos regulatorios y de certificación son externos.
- El cliente pidió deliberadamente permitir intentos de emisión aun con datos
  incompletos; esta decisión debe constar como requisito, no como defecto
  accidental.
- Firma, matrícula y datos médicos exigen tratamiento sensible.
- Una cotización cerrada debe definir cantidad de rondas de feedback y soporte.

## 15. Sugerencia para la nueva sesión de presupuesto

Prompt recomendado:

> Leé `PRESUPUESTO_RCTA_HANDOFF.md` completo. Necesito presupuestar el trabajo
> ya realizado y separar lo pendiente. Producí tres valuaciones: (1) esfuerzo
> real aproximado en horas por paquete, (2) valor de reposición por un proveedor
> argentino especializado y (3) precio comercial aconsejable. Expresá supuestos,
> moneda, IVA, tipo de cambio de referencia y rango de incertidumbre. Separá el
> costo histórico de Innovamed del precio del desarrollo. No valores la PoC como
> si fuera producción completa y no omitas gestión, investigación, QA, DevOps,
> documentación ni certificación.

Para obtener una cifra defendible, la nueva sesión debería preguntar además:

- quién es el destinatario del presupuesto;
- si se factura trabajo histórico, reposición o continuidad;
- moneda y mecanismo de actualización;
- si el precio incluye IVA;
- garantía y soporte incluidos;
- cesión de código/propiedad intelectual;
- urgencia y responsabilidad regulatoria;
- alcance exacto de la salida a producción.

## 16. Fuentes locales a consultar si hace falta profundizar

- `QBI2_HML_CERTIFICACION.md`
- `PLAN_INTEGRACION_QBI2_HISTORIAS.md`
- `PLAN_RECETAS.md`
- `QBI2_RCTA_ESPONTANEA_CAMPOS.md`
- `API_ENTITIES.md`
- `VERIFICACION_HHCC_QBI2_20260811.md`
- `20260811-185726.md`
- `deploy/QA_RUNBOOK.md`
- `hhcc/Qbi2/`
- cadena privada `Contacto RCTA integraciones.eml` — consultar sólo si es
  imprescindible y sin copiar credenciales.
