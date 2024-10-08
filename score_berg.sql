SELECT p.nombre, p.apellido,
       (MATCH(p.nombre, p.apellido) AGAINST('Berg' IN NATURAL LANGUAGE MODE)) * 2 AS fulltext_score,
       (p.nombre LIKE '%Berg%' AND p.apellido LIKE '%Berg') * 5 AS complete_match_score,  -- Coincidencia completa de ambas palabras
       (p.nombre LIKE '%Berg' AND p.apellido LIKE '%Berg%') * 5 AS reverse_match_score,  -- Coincidencia completa invertida
       (p.nombre LIKE '%Berg%' OR p.apellido LIKE '%Berg%') * 2 AS first_word_score,  -- Coincidencia con la primera palabra
       (p.nombre LIKE '%Berg' OR p.apellido LIKE '%Berg%') * 2 AS second_word_score,  -- Coincidencia con la segunda palabra
       ((MATCH(p.nombre, p.apellido) AGAINST('Berg' IN NATURAL LANGUAGE MODE)) * 2 +
        (p.nombre LIKE '%Berg%' AND p.apellido LIKE '%Berg') * 5 +
        (p.nombre LIKE '%Berg' AND p.apellido LIKE '%Berg%') * 5 +
        (p.nombre LIKE '%Berg%' OR p.apellido LIKE '%Berg%') * 2 +
        (p.nombre LIKE '%Berg' OR p.apellido LIKE '%Berg%') * 2) AS total_score
FROM pacientes p
LEFT JOIN historias_clinicas h ON p.id = h.paciente_id
WHERE MATCH(p.nombre, p.apellido) AGAINST('Berg' IN NATURAL LANGUAGE MODE)
   OR p.nombre LIKE '%Berg%'
   OR p.apellido LIKE '%Berg%'
   OR p.nombre LIKE '%Berg'
   OR p.apellido LIKE '%Berg'
ORDER BY total_score DESC;










