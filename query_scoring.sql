SELECT *,
       (MATCH(nombre, apellido) AGAINST('Ezequiel' IN NATURAL LANGUAGE MODE)) * 2 AS fulltext_score,  -- Mayor peso para full-text
       (CAST(numDoc AS CHAR) LIKE '%Ezequiel%') * 1 AS doc_score,  -- Peso para coincidencias parciales en numDoc
       (CAST(idhistoriaclinica AS CHAR) LIKE '%Ezequiel%') * 1 AS id_score,  -- Peso para coincidencias parciales en idhistoriaclinica
       ((MATCH(nombre, apellido) AGAINST('Ezequiel' IN NATURAL LANGUAGE MODE)) * 2 +
        (CAST(numDoc AS CHAR) LIKE '%Ezequiel%') * 1 +
        (CAST(idhistoriaclinica AS CHAR) LIKE '%Ezequiel%') * 1) AS total_score  -- Puntuación total
FROM pacientes
LEFT JOIN historias_clinicas ON pacientes.id = historias_clinicas.idPaciente
WHERE MATCH(nombre, apellido) AGAINST('Ezequiel' IN NATURAL LANGUAGE MODE)
   OR CAST(numDoc AS CHAR) LIKE '%Ezequiel%'
   OR CAST(historias_clinicas.id AS CHAR) LIKE '%Ezequiel%'
ORDER BY total_score DESC;

