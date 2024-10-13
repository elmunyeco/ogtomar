ALTER TABLE pacientes ALTER COLUMN idTipoDoc_id SET DEFAULT 1;
ALTER TABLE pacientes ADD FULLTEXT INDEX nombre_apellido_idx (nombre, apellido);
ALTER TABLE pacientes ADD COLUMN idTipoDoc_temp INT(10);
