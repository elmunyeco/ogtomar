ALTER TABLE pacientes ALTER COLUMN idTipoDoc_id SET DEFAULT 1;
ALTER TABLE pacientes ADD FULLTEXT INDEX nombre_apellido_fulltext_idx (nombre, apellido);
ALTER TABLE pacientes DROP FOREIGN KEY pacientes_idTipoDoc_id_6d4a5435_fk_tipos_documentos_id;
ALTER TABLE pacientes DROP INDEX pacientes_idTipoDoc_id_numDoc_d5b9acca_uniq;
-- cargar las tablas tipos_documentos, pacientes e historias_clinicas
-- correr post_migration_pacientes.py
ALTER TABLE pacientes ADD CONSTRAINT pacientes_idTipoDoc_id_numDoc_d5b9acca_uniq UNIQUE (idTipoDoc_id, numDoc);
ALTER TABLE pacientes ADD CONSTRAINT pacientes_idTipoDoc_id_6d4a5435_fk_tipos_documentos_id FOREIGN KEY (idTipoDoc_id) REFERENCES tipos_documentos(id);
-- Borrar idTipoDoc_temp desde el model y migrar.
