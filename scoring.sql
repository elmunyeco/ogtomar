SELECT *,
       (MATCH(p.nombre, p.apellido) AGAINST('Ezequiel' IN NATURAL LANGUAGE MODE)) * 2 AS fulltext_score,
       (CAST(p.numDoc AS CHAR) LIKE '%Ezequiel%') * 1 AS doc_score,
       (CAST(h.id AS CHAR) LIKE '%Ezequiel%') * 1 AS id_score,  -- Cambié a h.id
       (p.nombre LIKE '%Ezequiel%' OR p.apellido LIKE '%Ezequiel%') * 1 AS name_like_score,
       ((MATCH(p.nombre, p.apellido) AGAINST('Ezequiel' IN NATURAL LANGUAGE MODE)) * 2 +
        (CAST(p.numDoc AS CHAR) LIKE '%Ezequiel%') * 1 +
        (CAST(h.id AS CHAR) LIKE '%Ezequiel%') * 1 +
        (p.nombre LIKE '%Ezequiel%' OR p.apellido LIKE '%Ezequiel%') * 1) AS total_score
FROM pacientes p
LEFT JOIN historias_clinicas h ON p.id = h.paciente_id
WHERE MATCH(p.nombre, p.apellido) AGAINST('Ezequiel' IN NATURAL LANGUAGE MODE)
   OR CAST(p.numDoc AS CHAR) LIKE '%Ezequiel%'
   OR CAST(h.id AS CHAR) LIKE '%Ezequiel%'  -- Cambié a h.id
   OR p.nombre LIKE '%Ezequiel%'
   OR p.apellido LIKE '%Ezequiel%'
ORDER BY total_score DESC;


