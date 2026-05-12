---
title: "Arquitectura de Busqueda Global Clinica"
subtitle: "Propuesta tecnica para evolucionar desde busquedas separadas a un subsistema extensible"
date: "2026-05-08"
---

# Arquitectura de Busqueda Global Clinica

## Proposito

El sistema hoy tiene dos busquedas principales: una por pacientes y otra por historias clinicas. Ese esquema resolvio una etapa inicial, pero ya no representa bien como se usa clinicamente el sistema.

La necesidad nueva es una busqueda unica, capaz de encontrar informacion semanticamente buscable en pacientes, historias clinicas y, mas adelante, en estudios, indicaciones, comentarios, medicacion y otras entidades.

La decision importante no es solamente agregar un input mas grande. La decision importante es definir un subsistema de busqueda extensible, mantenible y compatible con el estado actual de `~/omar`.

## Punto de partida real

El sistema operativo esta en `~/omar`.

El stack actual es:

- Django 5.
- MariaDB / MySQL como base principal.
- Docker Compose para app, base y nginx.
- `main` como nucleo clinico.
- Apps separadas para estudios: `ecocardiograma`, `carotidas`, `ecostress`, `mmii`.
- Historia clinica como centro de navegacion.

La base ya contiene indices tradicionales y un indice `FULLTEXT` en `pacientes` sobre `nombre, apellido`. No existe todavia un subsistema de busqueda global.

## Problema actual

Las busquedas actuales estan acopladas a pantallas especificas:

- `Pacientes`: busca por documento, nombre o apellido.
- `Historias`: busca por ID, documento, nombre o apellido.

Ese enfoque tiene varios limites:

- Duplica logica.
- Obliga al usuario a decidir primero "donde buscar".
- No escala bien a indicaciones, comentarios o estudios.
- Tiende a generar vistas con muchos `Q(...)`, joins y reglas especiales.
- No permite construir un ranking global coherente.
- No permite evolucionar facilmente hacia busqueda semantica real.

## Decision actualizada 2026-05-08

La decision cambio a partir de una definicion funcional nueva: Omar quiere aprovechar la base de historias clinicas como base para un sistema de investigacion medica.

Con ese objetivo, Elasticsearch si tiene sentido como componente central. No debe usarse solamente como "otro buscador" paralelo, sino como fuente canonica del indice de busqueda textual.

La separacion correcta es:

```text
MySQL / Django
Fuente de verdad clinica y transaccional.

Elasticsearch
Fuente de verdad de busqueda textual, FTS, ranking e investigacion medica.
```

MySQL sigue mandando para datos clinicos, relaciones, usuarios, permisos, integridad y operaciones CRUD. Elasticsearch no reemplaza esa verdad. Es un indice secundario, reconstruible desde MySQL.

La consecuencia practica es importante: no conviene hacer crecer dos motores FTS distintos. Si se introduce Elasticsearch, la busqueda textual operativa y la busqueda de investigacion deben consultar el mismo backend.

## Recomendacion

La recomendacion es crear una app Django nueva, por ejemplo `search`, pero orientada desde el inicio a Elasticsearch como backend principal de busqueda.

Primera etapa recomendada:

```text
Django search app
+ Elasticsearch
+ documentos clinicos denormalizados
+ indexadores por dominio
+ cola/outbox de indexacion
+ comando de reconstruccion completa
```

MariaDB `FULLTEXT` puede quedar como fallback transitorio o como apoyo durante una etapa de migracion, pero no debe ser la estrategia principal si el sistema va a evolucionar hacia investigacion medica.

## Modelo propuesto

El modelo conceptual sigue siendo el de documentos denormalizados, pero esos documentos viven en Elasticsearch.

Documento base:

```text
clinical_search_document
- document_id
- entity_type
- entity_id
- paciente_id
- historia_id
- paciente_nombre
- paciente_apellido
- paciente_documento
- titulo
- subtitulo
- texto
- texto_normalizado
- fecha_relevante
- tags
- metadata
- updated_at
- deleted_at
```

Campos principales:

- `document_id`: identificador estable del documento de indice, por ejemplo `paciente:7544` o `comentario:24030`.
- `entity_type`: identifica el tipo de entidad indexada.
- `entity_id`: ID de la entidad original en MySQL.
- `paciente_id`: permite navegar o filtrar por paciente.
- `historia_id`: permite volver al centro clinico del sistema.
- `paciente_nombre`, `paciente_apellido`, `paciente_documento`: campos repetidos para busquedas y filtros sin joins.
- `titulo`: texto corto visible en resultados.
- `subtitulo`: contexto humano del resultado.
- `texto`: cuerpo buscable.
- `texto_normalizado`: version auxiliar para busqueda tolerante a acentos, mayusculas u otras variantes.
- `tags`: etiquetas clinicas o tecnicas derivadas.
- `metadata`: datos auxiliares para renderizar, filtrar o depurar.
- `fecha_relevante`: fecha clinica o administrativa util para ordenar.

La indexacion debe poder reconstruirse completa desde MySQL. Nunca debe existir informacion en Elasticsearch que sea irrecuperable desde la base principal.

## Entidades indexables

La primera version puede incluir:

- Paciente.
- Historia clinica.
- Comentarios de evolucion.
- Indicaciones.

Luego se pueden agregar:

- Ecocardiogramas.
- Carotidas.
- Ecostress.
- MMII.
- Solicitudes.
- PDFs o textos derivados de informes, si en algun momento se decide indexarlos.

## Ejemplos de documentos

### Paciente

```text
entity_type: paciente
entity_id: 7544
paciente_id: 7544
historia_id: 7544
titulo: "Pirulero, Pirulin - DNI 12"
subtitulo: "HC 7544 - Uruguayan Medical - Afiliado 000100010101"
texto: "Pirulin Pirulero DNI 12 Uruguayan Medical afiliado 000100010101 ..."
```

### Historia clinica

```text
entity_type: historia
entity_id: 7544
paciente_id: 7544
historia_id: 7544
titulo: "Historia clinica 7544 - Pirulero, Pirulin"
subtitulo: "Ultima visita: 05/05/2026"
texto: "Condiciones medicas activas, ultimos comentarios, resumen clinico ..."
```

### Comentario de evolucion

```text
entity_type: comentario
entity_id: 123
paciente_id: 7544
historia_id: 7544
titulo: "Evolucion - Pirulero, Pirulin"
subtitulo: "HC 7544 - 05/05/2026"
texto: "Paciente refiere disnea..."
```

### Estudio

```text
entity_type: ecocardiograma
entity_id: 12624
paciente_id: 11549
historia_id: 11549
titulo: "Ecocardiograma - Apellido, Nombre"
subtitulo: "HC 11549 - Fecha de estudio ..."
texto: "Funcion sistolica conservada. Valvula aortica..."
```

## Servicio de busqueda

El buscador no deberia consultar directamente todas las tablas del sistema. Deberia consultar el indice Elasticsearch a traves de un servicio Django estable.

Propuesta de estructura:

```text
hhcc/search/
- models.py
- services.py
- indexers.py
- tasks.py
- views.py
- urls.py
- management/commands/reindex_all.py
```

Responsabilidades:

- `models.py`: define modelos auxiliares locales si hacen falta, por ejemplo una outbox de indexacion.
- `indexers.py`: transforma entidades del dominio en documentos buscables.
- `services.py`: ejecuta busquedas, ranking, filtros y normalizacion contra Elasticsearch.
- `tasks.py`: procesa indexacion diferida o reintentos.
- `views.py`: endpoint web/API del buscador.
- `reindex_all.py`: reconstruccion completa del indice desde MySQL.

## Indexadores por dominio

Cada entidad importante deberia saber como publicarse al buscador mediante un indexador.

Ejemplos:

```text
PacienteIndexer
HistoriaIndexer
ComentarioIndexer
IndicacionIndexer
EcoIndexer
CarotidasIndexer
EcostressIndexer
MmiiIndexer
```

Esto evita que el buscador conozca detalles internos de cada modelo. El buscador solo trabaja con documentos.

## Indexacion background

Las altas, ediciones y borrados no deben depender fuertemente de Elasticsearch dentro de la misma request.

Flujo recomendado:

```text
Request Django
  -> guarda en MySQL
  -> registra tarea/outbox de indexacion
  -> responde OK al usuario

Worker background
  -> procesa pendientes
  -> actualiza Elasticsearch
```

Motivo: si Elasticsearch esta caido, el sistema clinico debe poder seguir cargando datos. Lo que queda degradado es la busqueda, no la operacion clinica principal.

Debe existir un comando `reindex_all` que borre/recree o sincronice el indice completo desde MySQL. Ese comando es obligatorio para recuperacion, deploys y cambios de mapping.

## Tipos de busqueda

Conviene distinguir tres niveles.

### 1. Busqueda exacta

Casos:

- DNI.
- ID de historia clinica.
- ID de paciente.
- Numero de afiliado.
- Fechas.

Esto requiere ranking especial, porque si el usuario escribe `7544`, probablemente espera ver primero la historia o paciente con ese ID.

### 2. Busqueda textual

Casos:

- Nombre.
- Apellido.
- Obra social.
- Medicacion.
- Condiciones.
- Comentarios.
- Conclusiones de estudios.

Esto se resuelve bien con Elasticsearch, normalizacion, analyzers y pesos por campo.

### 3. Busqueda semantica futura

Casos:

- "pacientes con estenosis carotidea"
- "ecos con funcion sistolica deteriorada"
- "pacientes anticoagulados"
- "estudios compatibles con isquemia"

Esto no conviene resolver desde el primer dia con embeddings. Primero hay que consolidar el indice documental. Luego se puede agregar un backend semantico encima.

## Ranking

El ranking no debe depender solo del score bruto de Elasticsearch.

Se recomienda combinar:

- Score de Elasticsearch.
- Coincidencia exacta por ID o documento.
- Peso por tipo de entidad.
- Recencia.
- Prioridad clinica del destino.

Ejemplo de prioridad inicial:

```text
1. Historia clinica exacta por ID
2. Paciente exacto por documento
3. Paciente por nombre/apellido
4. Comentarios o indicaciones
5. Estudios
```

La regla practica es que, aunque el match venga de un comentario o estudio, muchas veces el destino natural debe ser abrir la historia clinica.

## UI recomendada

La UI no deberia reemplazar el flujo clinico. Deberia acelerar la entrada.

Opciones razonables:

- Una pantalla `/buscar/` con buscador global.
- Un input global en el header, si se quiere acceso permanente.
- Resultados agrupados por tipo.
- Accion principal orientada a historia clinica.

Cada resultado deberia mostrar:

- Tipo de resultado.
- Nombre del paciente.
- Historia clinica asociada.
- Fragmento o motivo de coincidencia.
- Fecha relevante.
- Accion principal.

Ejemplo:

```text
[Evolucion] Pirulero, Pirulin - HC 7544
Coincidencia: "disnea de esfuerzo..."
Fecha: 05/05/2026
Abrir historia
```

## Operacion de Elasticsearch

Elasticsearch introduce costo operativo, pero queda justificado si el objetivo incluye investigacion medica sobre texto clinico libre.

Requisitos minimos:

- Indice reconstruible desde MySQL.
- Mapping versionado o documentado.
- Comando `reindex_all`.
- Tareas de indexacion con reintentos.
- Health check del indice.
- Modo degradado si Elasticsearch no responde.
- Backups de MySQL como verdad principal; Elasticsearch se puede regenerar.

## Por que no mantener dos FTS principales

No conviene que pacientes use MySQL `FULLTEXT` y que investigacion use Elasticsearch como caminos principales separados.

Motivos:

- Los resultados pueden diferir para la misma busqueda.
- El ranking tendria semanticas distintas.
- La UI seria dificil de explicar y depurar.
- La evolucion a sinonimos, analyzers o busqueda medica quedaria duplicada.
- Cada fix de busqueda habria que resolverlo dos veces.

La regla recomendada es simple:

```text
Todo lo que sea busqueda textual usa Elasticsearch.
Todo lo que sea persistencia clinica usa MySQL.
```

MySQL `FULLTEXT` queda como fallback transitorio, no como camino estrategico.

## Por que no migrar a PostgreSQL ahora

PostgreSQL tiene excelente busqueda full-text y podria ser una buena base para otro sistema. Pero en este caso no recomiendo migrar solo por busqueda.

Motivos:

- El sistema ya esta montado sobre MariaDB.
- La migracion de datos ya esta trabajada para MariaDB.
- El deploy actual ya esta resuelto con MariaDB.
- Cambiar motor de base por esta razon tendria un costo alto y distraeria del objetivo.

## Por que no empezar con embeddings

La busqueda semantica puede ser valiosa, especialmente en dominio clinico. Pero no deberia ser la primera capa.

Primero hay que definir:

- Que entidades se indexan.
- Como se relacionan con paciente e historia.
- Que resultado abre cada entidad.
- Como se reconstruye el indice.
- Que permisos o restricciones aplican.

Una vez que eso existe, embeddings puede ser una extension, no el fundamento inicial.

## Plan incremental

### Fase 1: Decision y contrato

- Documentar que MySQL es verdad clinica/transaccional.
- Documentar que Elasticsearch es verdad de busqueda textual e investigacion.
- Definir interfaz interna `search.services` para que la UI no dependa directamente del cliente Elasticsearch.
- Definir modo degradado si Elasticsearch esta caido.

### Fase 2: Documentos indexables

- Disenar mapping Elasticsearch.
- Definir documentos para paciente, historia, visita/comentario, indicacion/medicacion y estudio.
- Definir `document_id` estable por entidad.
- Definir que campos son buscables, filtrables y mostrables.

### Fase 3: Reconstruccion completa

- Crear comando `reindex_all`.
- Permitir reconstruir el indice completo desde MySQL.
- Validar conteos por tipo de documento.
- Dejar logs claros de errores de indexacion.

### Fase 4: Indexacion background

- Registrar pendientes de indexacion despues de altas, ediciones y borrados.
- Procesar pendientes con worker o comando recurrente.
- Reintentar errores sin bloquear la carga clinica.
- Asegurar que borrados o cambios de estado se reflejen en el indice.

### Fase 5: Busqueda operativa

- Cambiar buscadores de pacientes e historias para consultar Elasticsearch.
- Mantener MySQL como fallback temporal si se decide necesario.
- Ordenar resultados con prioridad clinica: historia/paciente exacto primero, luego matches textuales.
- Mostrar fragmentos, tipo de resultado, fecha relevante y accion principal.

### Fase 6: Investigacion medica

- Crear una pantalla o modulo de investigacion clinica.
- Agregar filtros por edad, sexo, fechas, tipo de estudio, medicacion, diagnosticos y texto libre.
- Agregar agregaciones utiles para cohortes y conteos.
- Evaluar sinonimos/analyzers medicos.
- Evaluar embeddings solo despues de consolidar el indice documental.

## Decision recomendada

La direccion arquitectonica recomendada es:

```text
Django search app
+ Elasticsearch como backend principal
+ documentos clinicos denormalizados
+ indexadores por dominio
+ servicio central de busqueda
+ indexacion background
+ reindex_all desde MySQL
```

Esta decision acepta una complejidad operativa mayor porque el objetivo ya no es solamente buscar pacientes o historias, sino explotar clinicamente la base para investigacion medica.

MySQL queda como verdad clinica. Elasticsearch queda como verdad de busqueda.

## Conclusion

El buscador global debe convertirse en un subsistema propio, no en una vista gigante.

La primera version debe nacer con una abstraccion interna estable y con Elasticsearch como backend canonico de busqueda textual. Eso evita construir una solucion intermedia con MariaDB `FULLTEXT` que despues habria que reemplazar o mantener en paralelo.

El objetivo no es solamente encontrar pacientes. El objetivo es permitir que cualquier dato clinicamente relevante lleve rapidamente al contexto correcto: la historia clinica del paciente, y que esos mismos datos puedan alimentar consultas de investigacion medica.
