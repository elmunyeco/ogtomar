---
title: "Arquitectura de Busqueda Global Clinica"
subtitle: "Propuesta tecnica para evolucionar desde busquedas separadas a un subsistema extensible"
date: "2026-05-05"
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

## Recomendacion

La recomendacion es crear una app Django nueva, por ejemplo `search`, con una tabla propia de documentos de busqueda denormalizados.

Primera etapa recomendada:

```text
Django search app
+ MariaDB FULLTEXT
+ tabla denormalizada search_documents
+ servicio central de busqueda
```

No recomiendo empezar por Elasticsearch, OpenSearch, Meilisearch, Typesense ni embeddings. Todos pueden tener lugar mas adelante, pero introducirlos desde el primer paso agregaria operacion, complejidad y puntos de falla antes de validar el uso real.

## Modelo propuesto

Crear una tabla similar a esta:

```text
search_documents
- id
- entity_type
- entity_id
- paciente_id
- historia_id
- titulo
- subtitulo
- texto
- texto_normalizado
- fecha_relevante
- metadata_json
- updated_at
```

Campos principales:

- `entity_type`: identifica el tipo de entidad indexada.
- `entity_id`: ID de la entidad original.
- `paciente_id`: permite navegar o filtrar por paciente.
- `historia_id`: permite volver al centro clinico del sistema.
- `titulo`: texto corto visible en resultados.
- `subtitulo`: contexto humano del resultado.
- `texto`: cuerpo buscable.
- `texto_normalizado`: version auxiliar para busqueda tolerante a acentos, mayusculas u otras variantes.
- `metadata_json`: datos auxiliares para renderizar o filtrar sin hacer joins inmediatos.
- `fecha_relevante`: fecha clinica o administrativa util para ordenar.

El indice `FULLTEXT` deberia aplicarse sobre una combinacion de:

```text
titulo, subtitulo, texto, texto_normalizado
```

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

El buscador no deberia consultar directamente todas las tablas del sistema. Deberia consultar `search_documents`.

Propuesta de estructura:

```text
hhcc/search/
- models.py
- services.py
- indexers.py
- views.py
- urls.py
- management/commands/rebuild_search_index.py
```

Responsabilidades:

- `models.py`: define `SearchDocument`.
- `indexers.py`: transforma entidades del dominio en documentos buscables.
- `services.py`: ejecuta busquedas, ranking, filtros y normalizacion.
- `views.py`: endpoint web/API del buscador.
- `rebuild_search_index.py`: reconstruccion completa del indice.

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

Esto se resuelve bien con `FULLTEXT`, normalizacion y pesos por campo.

### 3. Busqueda semantica futura

Casos:

- "pacientes con estenosis carotidea"
- "ecos con funcion sistolica deteriorada"
- "pacientes anticoagulados"
- "estudios compatibles con isquemia"

Esto no conviene resolver desde el primer dia con embeddings. Primero hay que consolidar el indice documental. Luego se puede agregar un backend semantico encima.

## Ranking

El ranking no debe depender solo del score de MariaDB.

Se recomienda combinar:

- Score `FULLTEXT`.
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

## Evolucion futura del stack

La tabla `search_documents` permite empezar simple y migrar despues.

Si MariaDB alcanza:

- Se mantiene todo dentro de Django + MariaDB.
- Menor operacion.
- Menor riesgo.

Si se necesita busqueda mas potente:

- Typesense o Meilisearch para busqueda rapida, simple, tolerante a errores y con buena experiencia de usuario.
- OpenSearch si se necesita control avanzado, analitica o queries mas complejas.
- Qdrant o embeddings si se confirma una necesidad real de busqueda semantica por significado.

La clave es disenar el buscador con una interfaz interna estable. El backend puede cambiar despues sin romper la UI.

## Por que no empezar con un motor externo

No conviene empezar con Elasticsearch/OpenSearch/Meilisearch/Typesense porque:

- Todavia no esta validado el comportamiento real esperado del buscador.
- Agrega servicios al deploy.
- Agrega sincronizacion entre DB e indice externo.
- Agrega nuevos modos de falla.
- Aumenta complejidad operativa.

El sistema hoy necesita primero una abstraccion correcta, no necesariamente un motor mas grande.

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

### Fase 1: Fundacion

- Crear app `search`.
- Crear modelo `SearchDocument`.
- Crear comando `rebuild_search_index`.
- Indexar pacientes e historias.
- Crear endpoint o vista `/buscar/`.

### Fase 2: Clinica basica

- Agregar comentarios EVOL.
- Agregar indicaciones.
- Agregar condiciones medicas.
- Ajustar ranking para que la historia clinica sea el destino principal.

### Fase 3: Estudios

- Agregar ecocardiograma.
- Agregar carotidas.
- Agregar ecostress.
- Agregar mmii.
- Definir que campos clinicos de cada estudio son realmente buscables.

### Fase 4: Experiencia de usuario

- Agrupar resultados por tipo.
- Agregar highlights.
- Agregar filtros por entidad, fecha o paciente.
- Evaluar autocomplete.

### Fase 5: Motor externo si hace falta

- Medir uso y limites de MariaDB.
- Elegir Typesense, Meilisearch, OpenSearch o vector search segun necesidad real.
- Mantener estable la interfaz interna del servicio de busqueda.

## Decision recomendada

La direccion arquitectonica recomendada es:

```text
Django search app
+ SearchDocument denormalizado
+ MariaDB FULLTEXT
+ indexadores por dominio
+ servicio central de busqueda
+ posibilidad futura de backend externo
```

Esta decision respeta el estado actual del sistema, mantiene baja la complejidad inicial y crea una base solida para crecer hacia estudios y busqueda semantica real cuando tenga sentido.

## Conclusion

El buscador global debe convertirse en un subsistema propio, no en una vista gigante.

La primera version debe vivir dentro del stack actual para reducir riesgo y acelerar aprendizaje. La arquitectura debe quedar preparada para crecer, pero sin introducir operacion innecesaria antes de tiempo.

El objetivo no es solamente encontrar pacientes. El objetivo es permitir que cualquier dato clinicamente relevante lleve rapidamente al contexto correcto: la historia clinica del paciente.
