SELECT p.id, p.nombre, p.apellido, p.numDoc, h.id AS historiaClinicaID
FROM pacientes p
LEFT JOIN historias_clinicas h ON p.id = h.idPaciente
WHERE MATCH(p.nombre, p.apellido) AGAINST('bergonzi' IN BOOLEAN MODE)
   OR p.numDoc LIKE '%bergonzi%'
   OR h.id LIKE '%bergonzi%';
