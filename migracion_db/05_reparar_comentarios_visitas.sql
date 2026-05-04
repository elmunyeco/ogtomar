-- Repara `comentarios_visitas` reconstruyendola desde `cardioprieto_old.comentarios`
-- con granularidad correcta: 1 fila por visita (fecha + historia + tipo),
-- concatenando con '\n' entre filas legacy del mismo grupo.
--
-- Uso:
--   mariadb -h 127.0.0.1 -P 3307 -uroot -pCorbis5 < migracion_db/05_reparar_comentarios_visitas.sql
--
-- Requisitos:
-- - Debe existir la base `cardioprieto_old` en la misma instancia.
-- - La tabla backup `comentarios_visitas_backup_pre_repair_20260421` se recrea en cada corrida.

SET FOREIGN_KEY_CHECKS=0;
SET SESSION group_concat_max_len = 1024 * 1024 * 32;

DROP TABLE IF EXISTS cardioprieto.comentarios_visitas_backup_pre_repair_20260421;
CREATE TABLE cardioprieto.comentarios_visitas_backup_pre_repair_20260421 AS
SELECT *
FROM cardioprieto.comentarios_visitas;

DELETE FROM cardioprieto.comentarios_visitas;

INSERT INTO cardioprieto.comentarios_visitas (fecha, comentarios, idHistoriaClinica, tipo)
SELECT
  CAST(CONCAT(c.fecha, ' 00:00:00') AS DATETIME),
  GROUP_CONCAT(
    REPLACE(
      REPLACE(
        REPLACE(c.comentario, '<br/>', '\n'),
        '<br />', '\n'
      ),
      '<br>', '\n'
    )
    ORDER BY c.id SEPARATOR '\n'
  ),
  c.idHistoriaClinica,
  CASE c.idTipoComentario
    WHEN 2 THEN 'INDIC'
    ELSE 'EVOL'
  END AS tipo
FROM cardioprieto_old.comentarios c
WHERE (c.eliminado IS NULL OR c.eliminado = 0)
  AND c.idTipoComentario IN (1, 2)
GROUP BY c.fecha, c.idHistoriaClinica, c.idTipoComentario;

SET FOREIGN_KEY_CHECKS=1;
