ALTER TABLE pacientes ADD FULLTEXT INDEX nombre_apellido_idx (nombre, apellido);
