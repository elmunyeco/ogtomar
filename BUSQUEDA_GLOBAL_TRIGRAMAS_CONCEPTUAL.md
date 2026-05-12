---
title: "Busqueda global por trigramas"
subtitle: "Explicacion conceptual para uso clinico y administrativo"
date: "2026-05-12"
---

# Busqueda global por trigramas

## Proposito

La busqueda global permite encontrar rapidamente un paciente, su historia clinica y sus estudios asociados desde una unica caja de texto.

El objetivo principal es resolver busquedas identificatorias frecuentes en un consultorio medico. Por ejemplo, cuando se recuerda una parte del apellido, una parte del nombre, algunos numeros del documento o algunos numeros del identificador de historia.

Esta busqueda no reemplaza la historia clinica ni interpreta contenido medico. Su funcion es localizar registros y ofrecer accesos directos.

## Que informacion utiliza

La primera version utiliza solamente datos identificatorios:

- Identificador del paciente.
- Identificador de la historia clinica.
- Documento del paciente.
- Apellido del paciente.
- Nombre del paciente.

Tambien muestra accesos a los estudios ya cargados para esa historia, separados por tipo y fecha.

## Que informacion no utiliza

Esta version no busca dentro de:

- Evoluciones clinicas.
- Indicaciones.
- Conclusiones de estudios.
- Diagnosticos redactados en texto libre.
- Medicacion.
- Otros textos medicos extensos.

Es una busqueda de identificacion y acceso, no una busqueda clinica de contenido.

## Por que no se usa una busqueda de texto tradicional

Una busqueda de texto tradicional funciona bien cuando se busca una palabra completa o casi completa. Sin embargo, en el uso cotidiano del consultorio muchas veces se busca con fragmentos.

Un usuario puede recordar solamente una parte de un apellido, una parte de un nombre o tres numeros del documento. En esos casos, una busqueda tradicional puede no ser suficiente o puede obligar a revisar demasiados registros.

La busqueda global se disena para reconocer fragmentos dentro de los datos identificatorios.

## Que es un trigrama

Un trigrama es un fragmento de tres caracteres consecutivos.

Si una palabra o numero se divide en fragmentos de tres caracteres, una busqueda parcial puede compararse contra esos fragmentos.

Esto permite encontrar coincidencias aunque el usuario no escriba el dato completo.

## Por que se eligieron trigramas

La longitud de tres caracteres ofrece un equilibrio adecuado.

Con fragmentos de dos caracteres aparecen demasiadas coincidencias poco utiles. Muchos nombres, apellidos y documentos comparten pares de letras o numeros. Eso aumenta el ruido y reduce la calidad de los resultados.

Con fragmentos de cuatro caracteres se reduce el ruido, pero se pierde sensibilidad. Una busqueda de tres numeros, que es habitual cuando se recuerda parte de un identificador, ya no funcionaria bien.

Los trigramas permiten buscar desde tres caracteres, mantienen una cantidad razonable de resultados y sirven tanto para letras como para numeros.

## Longitud minima de busqueda

La busqueda global requiere al menos tres caracteres.

Con uno o dos caracteres hay demasiadas coincidencias posibles. En esos casos el sistema no ejecuta la busqueda global y recomienda usar las busquedas clasicas de pacientes o historias.

Esta restriccion evita resultados excesivos y mantiene la busqueda global como una herramienta precisa.

## Criterios de importancia

No todos los campos tienen la misma importancia.

Los identificadores de paciente, historia y documento son datos muy precisos. Por eso reciben la mayor prioridad cuando coinciden.

El apellido tambien tiene alta prioridad porque en un consultorio medico es una forma habitual de buscar pacientes.

El nombre tambien es importante, aunque por lo general es menos especifico que el apellido.

El orden general de relevancia es:

1. Identificador de historia o paciente.
2. Documento.
3. Apellido.
4. Nombre.

## Como se presentan los resultados

Cada resultado se organiza alrededor de una persona y su historia clinica.

El sistema muestra:

- Nombre y apellido.
- Documento.
- Identificador de paciente.
- Identificador de historia.
- Acceso a la ficha del paciente.
- Acceso a la historia clinica.
- Accesos a estudios asociados, identificados por tipo y fecha.

Los estudios se muestran de forma compacta para facilitar la lectura.

## Por que los resultados pueden ocupar varias paginas

Algunas busquedas parciales pueden coincidir con muchos registros. Por ejemplo, tres numeros pueden aparecer en documentos, identificadores de paciente o identificadores de historia.

Cuando hay muchos resultados, se usa paginacion. Esto permite mantener la pantalla ordenada sin ocultar coincidencias validas.

## Estado experimental

La busqueda global se marca como experimental porque todavia debe evaluarse con uso real.

Durante esta etapa conviene observar:

- Si los resultados mas utiles aparecen suficientemente arriba.
- Si la busqueda por apellido responde como se espera.
- Si los fragmentos numericos generan demasiados resultados.
- Si la cantidad de resultados por pagina es adecuada.
- Si los accesos a historia y estudios son claros.

La evaluacion con usuarios reales es necesaria antes de considerar esta funcion como estable.

## Limites de esta version

Esta version no intenta responder preguntas clinicas.

No permite buscar conceptos medicos dentro de textos largos. Tampoco identifica sinonimos, relaciones clinicas ni significado medico.

Para ese tipo de necesidad se requerira una etapa posterior con un motor de busqueda clinica mas amplio.

## Resumen

La busqueda global por trigramas es una herramienta de localizacion rapida.

Su funcion es encontrar pacientes e historias a partir de fragmentos identificatorios y ofrecer accesos directos al trabajo clinico.

La decision de usar trigramas busca equilibrar sensibilidad, precision y velocidad sin introducir todavia una infraestructura de busqueda externa.
