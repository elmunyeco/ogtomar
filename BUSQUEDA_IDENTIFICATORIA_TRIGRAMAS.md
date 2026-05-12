---
title: "Busqueda identificatoria integral por trigramas"
subtitle: "Diseno MySQL previo a Elasticsearch para pacientes, historias y accesos clinicos"
date: "2026-05-12"
---

# Busqueda identificatoria integral por trigramas

## Resumen ejecutivo

El objetivo no es implementar una busqueda clinica semantica todavia. El objetivo inmediato es una busqueda unica, tipo Google, que permita encontrar rapidamente un paciente o su historia clinica por fragmentos parciales de datos identificatorios.

Casos esperados:

- `quiel` debe encontrar `Ezequiel`.
- `berg` debe encontrar `Bergonzi`.
- `231010` debe encontrar un documento como `23101065`.
- `576` debe encontrar un paciente o historia cuyo identificador sea `2576`.

La respuesta no debe ser solamente una fila. Debe ser una tarjeta de resultado con enlaces accionables: editar paciente, abrir historia y abrir estudios agrupados por tipo y fecha.

## Por que no alcanza FULLTEXT clasico

MariaDB/MySQL `FULLTEXT` funciona bien para palabras completas o prefijos en ciertos modos, pero no esta pensado para encontrar substrings arbitrarios dentro de una palabra o de un numero.

Ejemplos problematicos:

- Buscar `quiel` dentro de `Ezequiel`.
- Buscar `576` dentro de `2576`.
- Buscar `231010` dentro de `23101065`.

Un indice `FULLTEXT(nombre, apellido)` puede ayudar para busquedas por palabras completas, pero no cubre bien el comportamiento de "cualquier ocurrencia" que se espera de una caja unica tipo Google.

La alternativa simple seria usar:

```sql
nombre LIKE '%quiel%'
OR apellido LIKE '%quiel%'
OR numDoc LIKE '%231010%'
OR CAST(id AS CHAR) LIKE '%576%'
```

Esto produce resultados correctos al principio, pero escala mal: obliga al motor a escanear muchas filas porque un patron con comodin inicial (`%texto`) no puede usar eficientemente un indice B-Tree normal.

## Decision recomendada

Implementar una tabla materializada de busqueda basada en trigramas.

La idea es construir un indice propio, dentro de MySQL, que represente cada paciente/historia como un documento buscable. Ese documento se descompone en fragmentos de tres caracteres. Luego la busqueda consulta esos fragmentos con indices normales.

Este diseno evita depender de escaneos completos con `LIKE '%...%'` y permite obtener candidatos rapidamente.

## Campos incluidos

### Paciente

Campos obligatorios:

| Campo | Motivo | Peso sugerido |
|---|---:|---:|
| `pacientes.id` | Identificador interno del paciente. Puede coincidir funcionalmente con historia en muchos casos. | 100 |
| `pacientes.numDoc` | Documento nacional u otro identificador administrativo. Es un acceso exacto fuerte, aunque no siempre sea el dato mas usado en consultorio. | 100 |
| `pacientes.apellido` | Campo clinicamente central para ubicar personas. En un consultorio medico se busca tanto por apellido como por documento o ID. | 100 |
| `pacientes.nombre` | Campo central para busqueda humana. | 70 |

Campos no incluidos en la primera etapa:

- `telefono`
- `celular`
- `mail`
- `obraSocial`
- `afiliado`

Estos campos pueden agregarse despues, pero conviene no mezclarlos al inicio para no degradar el ranking ni mostrar resultados inesperados.

### Historia clinica

Campos obligatorios:

| Campo | Motivo | Peso sugerido |
|---|---:|---:|
| `historias_clinicas.id` | Identificador directo de historia clinica. | 100 |
| `historias_clinicas.paciente_id` | Vinculo real con paciente. No debe asumirse siempre que `historia.id == paciente.id`. | 100 |

La tabla `historias_clinicas` no tiene texto clinico propio. Sus datos buscables vienen principalmente de su paciente asociado.

### Documento buscable base

Para cada historia/paciente se genera un texto normalizado similar a:

```text
2576 2576 23101065 ezequiel bergonzi
```

Donde:

- Primer `2576`: `paciente.id`.
- Segundo `2576`: `historia.id`.
- `23101065`: `paciente.numDoc`.
- `ezequiel`: `paciente.nombre`.
- `bergonzi`: `paciente.apellido`.

Aunque hoy muchas veces `paciente.id` e `historia.id` coincidan, la implementacion debe guardar ambos para no depender de una casualidad de datos.

## Normalizacion

Antes de generar trigramas, el texto debe normalizarse:

1. Convertir a minusculas.
2. Eliminar acentos y diacriticos.
3. Convertir `ñ` de forma estable, preferentemente a `n`.
4. Conservar letras y numeros.
5. Reemplazar separadores por espacios.
6. Colapsar espacios repetidos.

Ejemplo:

```text
"Ezequiel  Bergonzi - DNI 23.101.065"
```

se normaliza a:

```text
ezequiel bergonzi dni 23101065
```

## Por que trigramas

Un n-grama es un fragmento continuo de longitud `n`.

Para `ezequiel`, los trigramas son:

```text
eze zeq equ qui uie iel
```

Para `23101065`, los trigramas son:

```text
231 310 101 010 106 065
```

Para `2576`, los trigramas son:

```text
257 576
```

### Por que no bigramas

Los bigramas tienen longitud 2.

Ejemplo:

```text
ezequiel -> ez ze eq qu ui ie el
```

Ventajas:

- Permiten buscar fragmentos muy cortos.
- Aumentan sensibilidad.

Problemas:

- Generan demasiados candidatos.
- Producen muchos falsos positivos.
- Terminos como `ez`, `ar`, `an`, `os`, `ra` aparecen en demasiados nombres y apellidos.
- En documentos numericos, pares como `10`, `23`, `65` son demasiado frecuentes.

Para una busqueda global de pacientes, los bigramas tienden a traer ruido y a bajar la calidad del ranking.

### Por que no tetragramas

Los tetragramas tienen longitud 4.

Ejemplo:

```text
ezequiel -> ezeq zequ equi quie uiel
```

Ventajas:

- Reducen falsos positivos.
- Son mas especificos.

Problemas:

- Son menos tolerantes a busquedas cortas.
- No permiten encontrar bien IDs de 3 caracteres.
- Una busqueda como `576` no generaria ningun tetragrama.
- Requieren queries de longitud minima 4 para funcionar naturalmente.

Para el caso de uso real, donde se quiere encontrar `576` dentro de `2576`, tetragramas dejan afuera una busqueda importante.

### Equilibrio de trigramas

Los trigramas son el mejor compromiso:

- Permiten busquedas de tres caracteres, utiles para IDs y fragmentos de DNI.
- Reducen mucho el ruido respecto de bigramas.
- Mantienen buena tolerancia para fragmentos de nombres y apellidos.
- Funcionan bien para nombres, apellidos y numeros.

Regla recomendada:

```text
Longitud de query >= 3: usar trigramas.
Longitud de query 1 o 2: no ejecutar busqueda global.
```

Para queries de uno o dos caracteres, la interfaz debe mostrar un mensaje de error o advertencia:

```text
La busqueda global requiere al menos 3 caracteres.
Para busquedas de 1 o 2 caracteres, use la busqueda clasica de Historia o Paciente.
```

No conviene hacer excepciones de ID exacto en la busqueda global porque abre una conducta ambigua: una entrada como `7`, `12` o `45` puede representar fragmentos de documento, historia, paciente o texto. La busqueda global debe mantener una regla simple y predecible.

## Modelo de tablas

### Tabla de documentos

```sql
CREATE TABLE global_search_documents (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  document_key VARCHAR(80) NOT NULL,
  paciente_id BIGINT NOT NULL,
  historia_id BIGINT NULL,
  title VARCHAR(255) NOT NULL,
  subtitle VARCHAR(255) NULL,
  search_text_normalized TEXT NOT NULL,
  updated_at DATETIME NOT NULL,
  UNIQUE KEY global_search_documents_key_uniq (document_key),
  KEY global_search_documents_paciente_idx (paciente_id),
  KEY global_search_documents_historia_idx (historia_id)
);
```

Ejemplo de documento:

```text
document_key: paciente:2576
paciente_id: 2576
historia_id: 2576
title: Ezequiel Bergonzi
subtitle: DNI 23101065 - Historia #2576
search_text_normalized: 2576 2576 23101065 ezequiel bergonzi
```

### Tabla de trigramas

```sql
CREATE TABLE global_search_grams (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  document_id BIGINT NOT NULL,
  gram CHAR(3) NOT NULL,
  weight INT NOT NULL DEFAULT 1,
  KEY global_search_grams_gram_idx (gram),
  UNIQUE KEY global_search_grams_doc_gram_uniq (document_id, gram),
  CONSTRAINT global_search_grams_document_fk
    FOREIGN KEY (document_id)
    REFERENCES global_search_documents (id)
    ON DELETE CASCADE
);
```

El indice clave es:

```sql
KEY global_search_grams_gram_idx (gram)
```

Ese indice permite resolver la busqueda por fragmentos sin escanear todos los pacientes.

## Generacion de trigramas

Cada token normalizado se descompone por separado.

Ejemplo:

```text
ezequiel bergonzi 23101065 2576
```

produce:

```text
eze zeq equ qui uie iel
ber erg rgo gon onz nzi
231 310 101 010 106 065
257 576
```

No conviene generar trigramas cruzando espacios, por ejemplo `el ` o `l b`, porque agregan ruido y no representan busquedas naturales.

## Consulta de busqueda

Para una query:

```text
quiel
```

se normaliza y se generan trigramas:

```text
qui uie iel
```

Luego se buscan documentos candidatos:

```sql
SELECT
  d.id,
  d.paciente_id,
  d.historia_id,
  d.title,
  d.subtitle,
  SUM(g.weight) AS score,
  COUNT(DISTINCT g.gram) AS matched_grams
FROM global_search_grams g
JOIN global_search_documents d ON d.id = g.document_id
WHERE g.gram IN ('qui', 'uie', 'iel')
GROUP BY d.id
ORDER BY matched_grams DESC, score DESC, d.id DESC
LIMIT 25;
```

Despues de obtener candidatos, conviene confirmar coincidencia contra `search_text_normalized` en Python o SQL para reducir falsos positivos.

## Ranking

El ranking debe priorizar matches identificatorios fuertes.

Orden sugerido:

1. ID exacto de historia.
2. ID exacto de paciente.
3. Documento exacto.
4. Apellido exacto o de alta coincidencia.
5. Documento parcial.
6. Apellido parcial.
7. Nombre parcial.
8. Coincidencia por trigramas generales.

Los pesos sugeridos ayudan, pero no reemplazan reglas explicitas para coincidencias exactas.

## Resultado tipo Google

Cada resultado debe agrupar la informacion alrededor del paciente/historia.

Ejemplo:

```text
Ezequiel Bergonzi
DNI 23101065 - Paciente #2576 - Historia #2576

[Paciente] Editar paciente
[Historia] Abrir historia clinica
[Eco] Ecocardiograma - 2025-04-10
[Stress] Ecostress - 2024-11-03
[Carotidas] Carotidas - 2024-08-20
[MMII] Doppler MMII - 2023-12-01
```

La busqueda devuelve entidades encontradas. La vista arma enlaces accionables:

- Edicion del paciente.
- Apertura/edicion de historia clinica.
- Estudios por tipo y fecha.

## Actualizacion del indice

Primera etapa:

- Crear comando `rebuild_global_search_index`.
- Reconstruir todo el indice desde MySQL.
- Ejecutarlo despues de deploy o cambios grandes.

Segunda etapa:

- Reindexar un paciente/historia al crear o editar paciente.
- Reindexar al crear una historia.
- Reindexar si cambia el vinculo paciente-historia.

Como los campos iniciales son pocos, la reconstruccion completa deberia ser simple y confiable.

## Migraciones minimas complementarias

Aunque la busqueda principal use trigramas, conviene agregar indice normal sobre documento:

```sql
CREATE INDEX pacientes_numdoc_idx ON pacientes (numDoc);
```

Ese indice ayuda para busquedas exactas o por prefijo y no interfiere con el sistema de trigramas.

## Limites conocidos

Este diseno no reemplaza Elasticsearch para busqueda clinica profunda.

No busca todavia:

- Comentarios de evolucion.
- Indicaciones.
- Conclusiones de estudios.
- Diagnosticos textuales.
- Sinonimos medicos.
- Busqueda semantica por significado.

Lo que resuelve bien es la busqueda identificatoria global: encontrar rapido a la persona correcta y mostrar todos sus accesos clinicos relevantes.

## Conclusion

Para la necesidad inmediata, trigramas materializados en MySQL son una solucion intermedia robusta: mucho mejor que `LIKE '%...%'`, menos compleja que Elasticsearch y alineada con el comportamiento esperado de una caja unica tipo Google.

Los campos iniciales deben ser pocos y fuertes:

```text
paciente.id
historia.id
paciente.numDoc
paciente.apellido
paciente.nombre
```

Apellido queda incluido con el mismo peso que documento e ID porque, en el flujo real de un consultorio medico, muchas busquedas empiezan por apellido. El ranking no debe tratarlo como un dato secundario.
