-- Merge de datos:
-- - toma como base productiva `cardioprieto_merged` (clon de `cardioprieto_prod_12688`)
-- - reescribe historias 1..12679 desde `cardioprieto_src_3307`
-- - preserva historias >12679 desde la productiva
-- - preserva auth_* y django_* de la productiva
--
-- Uso:
--   mariadb -h 127.0.0.1 -P 3307 -uroot -pCorbis5 < migracion_db/06_merge_src_into_prod_range.sql

SET FOREIGN_KEY_CHECKS=0;
USE cardioprieto_merged;

-- IDs de pacientes del bloque a reescribir y pacientes usados por historias nuevas.
CREATE OR REPLACE TEMPORARY TABLE tmp_src_patient_ids AS
SELECT DISTINCT paciente_id
FROM cardioprieto_src_3307.historias_clinicas
WHERE id <= 12679;

CREATE OR REPLACE TEMPORARY TABLE tmp_preserved_patient_ids AS
SELECT DISTINCT paciente_id
FROM cardioprieto_merged.historias_clinicas
WHERE id > 12679;

-- Hijas de estudios ecocardiograma del bloque viejo.
DELETE se
FROM segmentos_ecocardiograma se
JOIN estudios_ecocardiograma ee ON ee.id = se.estudio_id
WHERE ee.historia_id <= 12679;

DELETE ce
FROM conclusiones_ecocardiograma ce
JOIN estudios_ecocardiograma ee ON ee.id = ce.estudio_id
WHERE ee.historia_id <= 12679;

-- Tablas hijas directas de historias.
DELETE FROM estudios_ecocardiograma WHERE historia_id <= 12679;
DELETE FROM carotidas WHERE historia_id <= 12679;
DELETE FROM stress WHERE idHC <= 12679;
DELETE FROM mmii WHERE idHC <= 12679;
DELETE FROM comentarios_visitas WHERE idHistoriaClinica <= 12679;
DELETE FROM indicaciones_visitas WHERE historia_clinica_id <= 12679;
DELETE FROM signos_vitales WHERE historia_id <= 12679;
DELETE FROM condiciones_medicas_historias WHERE historia_id <= 12679;

-- Historias del bloque viejo.
DELETE FROM historias_clinicas WHERE id <= 12679;

-- Pacientes solo del bloque viejo, excepto si tambien son usados por historias nuevas preservadas.
DELETE p
FROM pacientes p
JOIN tmp_src_patient_ids s ON s.paciente_id = p.id
LEFT JOIN tmp_preserved_patient_ids k ON k.paciente_id = p.id
WHERE k.paciente_id IS NULL;

-- Referencias chicas: se actualizan completas desde src.
DELETE FROM condiciones_medicas;
INSERT INTO condiciones_medicas SELECT * FROM cardioprieto_src_3307.condiciones_medicas;

DELETE FROM tipos_documentos;
INSERT INTO tipos_documentos SELECT * FROM cardioprieto_src_3307.tipos_documentos;

-- Pacientes del bloque viejo que no esten compartidos con historias nuevas preservadas.
INSERT INTO pacientes
SELECT p.*
FROM cardioprieto_src_3307.pacientes p
JOIN tmp_src_patient_ids s ON s.paciente_id = p.id
LEFT JOIN tmp_preserved_patient_ids k ON k.paciente_id = p.id
WHERE k.paciente_id IS NULL;

-- Historias y tablas hijas del bloque viejo desde src.
INSERT INTO historias_clinicas
SELECT *
FROM cardioprieto_src_3307.historias_clinicas
WHERE id <= 12679;

INSERT INTO condiciones_medicas_historias
SELECT *
FROM cardioprieto_src_3307.condiciones_medicas_historias
WHERE historia_id <= 12679;

INSERT INTO signos_vitales
SELECT *
FROM cardioprieto_src_3307.signos_vitales
WHERE historia_id <= 12679;

INSERT INTO indicaciones_visitas
SELECT *
FROM cardioprieto_src_3307.indicaciones_visitas
WHERE historia_clinica_id <= 12679;

INSERT INTO comentarios_visitas
SELECT *
FROM cardioprieto_src_3307.comentarios_visitas
WHERE idHistoriaClinica <= 12679;

INSERT INTO carotidas
SELECT *
FROM cardioprieto_src_3307.carotidas
WHERE historia_id <= 12679;

INSERT INTO stress
SELECT *
FROM cardioprieto_src_3307.stress
WHERE idHC <= 12679;

INSERT INTO mmii
SELECT *
FROM cardioprieto_src_3307.mmii
WHERE idHC <= 12679;

INSERT INTO estudios_ecocardiograma
SELECT *
FROM cardioprieto_src_3307.estudios_ecocardiograma
WHERE historia_id <= 12679;

INSERT INTO conclusiones_ecocardiograma
SELECT ce.*
FROM cardioprieto_src_3307.conclusiones_ecocardiograma ce
JOIN cardioprieto_src_3307.estudios_ecocardiograma ee ON ee.id = ce.estudio_id
WHERE ee.historia_id <= 12679;

INSERT INTO segmentos_ecocardiograma
SELECT se.*
FROM cardioprieto_src_3307.segmentos_ecocardiograma se
JOIN cardioprieto_src_3307.estudios_ecocardiograma ee ON ee.id = se.estudio_id
WHERE ee.historia_id <= 12679;

SET FOREIGN_KEY_CHECKS=1;
