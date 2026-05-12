---
title: "Busqueda global por trigramas"
subtitle: "Explicacion conceptual para uso clinico y administrativo"
date: "2026-05-12"
author: "Ezequiel Rodrigo Bergonzi"
---

# Busqueda global por trigramas

## Este paper conceptual

Aclara como funcionan las busquedas identificatorias basadas en la teoria de segmentacion de vectores con pesos asignados. Puede ser una buena introduccion a los grafos porque explica con ejemplos las vecindades y las fuerzas de las conexiones entre elementos. De ninguna forma se busca mostrar una implementacion actual.

## Proposito

La busqueda global permite encontrar rapidamente un paciente, su historia clinica y sus estudios asociados desde una unica caja de texto.

El objetivo principal es resolver busquedas identificatiorias en el consultorio condensando el criterio. Por ejemplo, cuando se recuerda una parte del apellido, una parte del nombre, algunos numeros del documento o algunos numeros del identificador de historia.

Esta busqueda no reemplaza la de historia clinica ni paciente. No interpreta contenido medico (busqueda semantica). Su funcion es solamente localizar registros y ofrecer accesos directos. No somos google, pero andamos mejor que otros sistemas, incluso de grandes centros, jeje!

## Que informacion utiliza

La primera version utiliza solamente:

- Identificador del paciente.
- Identificador de la historia clinica.
- Documento del paciente.
- Apellido del paciente.
- Nombre del paciente.


## Que informacion no utiliza

Esta version no busca dentro de:

- Evoluciones clinicas.
- Indicaciones.
- Conclusiones de estudios.
- Diagnosticos redactados en texto libre.
- Medicacion.
- Otros textos medicos extensos.


## Por que no se usa una busqueda de texto tradicional

Una busqueda de texto tradicional funciona bien cuando se busca una palabra completa o casi completa. Sin embargo, supongo que en el uso cotidiano del consultorio muchas veces se busca con fragmentos.

Uno puede recordar solamente una parte de un apellido, una parte de un nombre o tres numeros del documento. En esos casos, una busqueda tradicional puede no ser suficiente o puede obligar a revisar demasiados registros.

reconocer fragmentos trisimbólicos dentro de los datos identificatorios. (trigramas)

## Que es un trigrama

Un trigrama es un fragmento de tres caracteres consecutivos.

Si una palabra o numero se divide en fragmentos de tres caracteres, una busqueda parcial puede compararse contra esos fragmentos.

Esto permite encontrar coincidencias aunque el usuario no escriba el dato completo.

'''
ezequiel: eze, zeq, equ, qui, uie, iel .... 2023101065: 202,023,231, bergonzi: ber, erg, ... , nzi. etc.... etc...
prieto manuel califica fuerte con "pri man", "man pri", "anu rie", por ejemplo. No califica tan arriba solo con "pri", como es claro.
'''

## Por que se eligieron trigramas

Es una eleccion completamente explicada en la teoria de los cientificos que estudiaron el tema y realmente saben. Y tiene que ver no solo con el contenido sino con el idioma. Es la mejor combinacion para castellano y combinado con numeros.

La longitud de tres caracteres ofrece un equilibrio adecuado.

Con fragmentos de dos caracteres aparecen demasiadas coincidencias poco utiles. Muchos nombres, apellidos y documentos comparten pares de letras o numeros. Eso aumenta el ruido y reduce la calidad de los resultados.

Con fragmentos de cuatro caracteres se reduce el ruido, pero se pierde sensibilidad. Una busqueda de tres numeros, que es habitual cuando se recuerda parte de un identificador, ya no funcionaria bien.

Los trigramas permiten buscar desde tres caracteres, mantienen una cantidad razonable de resultados y sirven tanto para letras como para numeros.

## Longitud minima de busqueda

La busqueda global requiere al menos tres caracteres.

Con uno o dos caracteres hay demasiadas coincidencias posibles. En esos casos el sistema no ejecuta la busqueda global. recomiendo usar las busquedas clasicas de pacientes o historias.

Esta restriccion evita resultados excesivos y mantiene la busqueda global como una herramienta precisa.

## Criterios de importancia

No todos los campos tienen la misma importancia.

Los identificadores de paciente e historia (que son el mismo) y el documento son datos muy precisos. Por eso reciben la mayor prioridad cuando coinciden.

El apellido tambien tiene alta prioridad porque en el consultorio medico yo supongo que es la forma mas habitual de buscar a los pacientes.

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

La busqueda global se marca como experimental porque todavia debe evaluarse con uso real de este consultorio en particular e ir ajustando a medida que Omar vaya puteando o poniendose contento.

observar:

- Si los resultados mas utiles aparecen suficientemente arriba.
- Si Omar se pone maniaco o depresivo.
- Si la busqueda por apellido responde como se espera.
- Si Omar se deprime.
- Si los fragmentos numericos generan demasiados resultados.
- Si Omar agarra el cigarrillo o el alcohol.
- Si la cantidad de resultados por pagina es adecuada.
- Si Omar deja la medicina y se hace linyera.
- Si los accesos a historia y estudios son claros.

La evaluacion con usuarios reales es necesaria antes de considerar esta funcion como estable.

## Limites de esta version

Esta version no intenta responder preguntas clinicas.

No permite buscar conceptos medicos dentro de textos largos. Tampoco identifica sinonimos, relaciones clinicas ni significado medico.

Para ese tipo de necesidad se requerira una etapa posterior con elasticsearch como motor serio de busqueda.
