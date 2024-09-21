SELECT p.id, p.nombre, p.apellido, p.numDoc, h.id AS historiaClinicaID
FROM pacientes p
LEFT JOIN historias_clinicas h ON p.id = h.idPaciente
WHERE p.nombre LIKE '%berg%'
   OR  p.apellido LIKE '%berg%'
   OR p.numDoc LIKE '%bergonzi%'
   OR h.id LIKE '%bergonzi%';
