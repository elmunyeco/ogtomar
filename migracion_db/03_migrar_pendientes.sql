-- Migracion pendientes (doppler, eco_*)
-- Requiere cardioprieto_old cargado y estudios_ecocardiograma ya migrados.

SET FOREIGN_KEY_CHECKS=0;
USE cardioprieto;

-- Doppler -> MMII
INSERT INTO cardioprieto.mmii (
  idMMII, artFemComunDerecha, artFemSuperficialDerecha, artFemProfundaDerecha, artPopliteaDerecha, artInfrapatelaresDerecha,
  artFemComunIzquierda, artFemSuperficialIzquierda, artFemProfundaIzquierda, artPopliteaIzquierda, artInfrapatelaresIzquierda,
  conclusion, idHC, fecha_estudio
)
SELECT
  d.idDoppler, d.artFemComunDerecha, d.artFemSuperficialDerecha, d.artFemProfundaDerecha, d.artPopliteaDerecha, d.artInfrapatelaresDerecha,
  d.artFemComunIzquierda, d.artFemSuperficialIzquierda, d.artFemProfundaIzquierda, d.artPopliteaIzquierda, d.artInfrapatelaresIzquierda,
  d.conclusion, d.idHC, COALESCE(h.fechaAlta, CURDATE())
FROM cardioprieto_old.doppler d
LEFT JOIN cardioprieto_old.historiaclinica h ON h.id = d.idHC
ON DUPLICATE KEY UPDATE
  artFemComunDerecha=VALUES(artFemComunDerecha), artFemSuperficialDerecha=VALUES(artFemSuperficialDerecha),
  artFemProfundaDerecha=VALUES(artFemProfundaDerecha), artPopliteaDerecha=VALUES(artPopliteaDerecha),
  artInfrapatelaresDerecha=VALUES(artInfrapatelaresDerecha), artFemComunIzquierda=VALUES(artFemComunIzquierda),
  artFemSuperficialIzquierda=VALUES(artFemSuperficialIzquierda), artFemProfundaIzquierda=VALUES(artFemProfundaIzquierda),
  artPopliteaIzquierda=VALUES(artPopliteaIzquierda), artInfrapatelaresIzquierda=VALUES(artInfrapatelaresIzquierda),
  conclusion=VALUES(conclusion), idHC=VALUES(idHC), fecha_estudio=VALUES(fecha_estudio);

-- Mapa de ecocardiogramas
CREATE TEMPORARY TABLE tmp_ecos_map AS
SELECT o.old_id, n.new_id
FROM (
  SELECT id AS old_id, idHC, fecha,
         ROW_NUMBER() OVER (PARTITION BY idHC, fecha ORDER BY id) AS rn
  FROM cardioprieto_old.ecocardiograma
) o
JOIN (
  SELECT id AS new_id, historia_id, fecha,
         ROW_NUMBER() OVER (PARTITION BY historia_id, fecha ORDER BY id) AS rn
  FROM cardioprieto.estudios_ecocardiograma
) n
ON n.historia_id = o.idHC AND n.fecha = o.fecha AND n.rn = o.rn;

-- Segmentos (precalcula si todos son 0)
CREATE TEMPORARY TABLE tmp_eco_segmentos AS
SELECT
  idEstudioeco,
  (IFNULL(s1,0)=0 AND IFNULL(s2,0)=0 AND IFNULL(s3,0)=0 AND IFNULL(s4,0)=0 AND
   IFNULL(s5,0)=0 AND IFNULL(s6,0)=0 AND IFNULL(s7,0)=0 AND IFNULL(s8,0)=0 AND
   IFNULL(s9,0)=0 AND IFNULL(s10,0)=0 AND IFNULL(s11,0)=0 AND IFNULL(s12,0)=0 AND
   IFNULL(s13,0)=0 AND IFNULL(s14,0)=0 AND IFNULL(s15,0)=0 AND IFNULL(s16,0)=0) AS all_zero,
  s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14,s15,s16
FROM cardioprieto_old.eco_segmentos;

-- Segmentos ecocardiograma
INSERT IGNORE INTO cardioprieto.segmentos_ecocardiograma (numero_segmento, estado, estudio_id)
SELECT 1, CASE WHEN s.all_zero=1 THEN 1 ELSE s.s1 END, m.new_id FROM tmp_eco_segmentos s JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco WHERE s.all_zero=1 OR s.s1 IS NOT NULL
UNION ALL SELECT 2, CASE WHEN s.all_zero=1 THEN 1 ELSE s.s2 END, m.new_id FROM tmp_eco_segmentos s JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco WHERE s.all_zero=1 OR s.s2 IS NOT NULL
UNION ALL SELECT 3, CASE WHEN s.all_zero=1 THEN 1 ELSE s.s3 END, m.new_id FROM tmp_eco_segmentos s JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco WHERE s.all_zero=1 OR s.s3 IS NOT NULL
UNION ALL SELECT 4, CASE WHEN s.all_zero=1 THEN 1 ELSE s.s4 END, m.new_id FROM tmp_eco_segmentos s JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco WHERE s.all_zero=1 OR s.s4 IS NOT NULL
UNION ALL SELECT 5, CASE WHEN s.all_zero=1 THEN 1 ELSE s.s5 END, m.new_id FROM tmp_eco_segmentos s JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco WHERE s.all_zero=1 OR s.s5 IS NOT NULL
UNION ALL SELECT 6, CASE WHEN s.all_zero=1 THEN 1 ELSE s.s6 END, m.new_id FROM tmp_eco_segmentos s JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco WHERE s.all_zero=1 OR s.s6 IS NOT NULL
UNION ALL SELECT 7, CASE WHEN s.all_zero=1 THEN 1 ELSE s.s7 END, m.new_id FROM tmp_eco_segmentos s JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco WHERE s.all_zero=1 OR s.s7 IS NOT NULL
UNION ALL SELECT 8, CASE WHEN s.all_zero=1 THEN 1 ELSE s.s8 END, m.new_id FROM tmp_eco_segmentos s JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco WHERE s.all_zero=1 OR s.s8 IS NOT NULL
UNION ALL SELECT 9, CASE WHEN s.all_zero=1 THEN 1 ELSE s.s9 END, m.new_id FROM tmp_eco_segmentos s JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco WHERE s.all_zero=1 OR s.s9 IS NOT NULL
UNION ALL SELECT 10, CASE WHEN s.all_zero=1 THEN 1 ELSE s.s10 END, m.new_id FROM tmp_eco_segmentos s JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco WHERE s.all_zero=1 OR s.s10 IS NOT NULL
UNION ALL SELECT 11, CASE WHEN s.all_zero=1 THEN 1 ELSE s.s11 END, m.new_id FROM tmp_eco_segmentos s JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco WHERE s.all_zero=1 OR s.s11 IS NOT NULL
UNION ALL SELECT 12, CASE WHEN s.all_zero=1 THEN 1 ELSE s.s12 END, m.new_id FROM tmp_eco_segmentos s JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco WHERE s.all_zero=1 OR s.s12 IS NOT NULL
UNION ALL SELECT 13, CASE WHEN s.all_zero=1 THEN 1 ELSE s.s13 END, m.new_id FROM tmp_eco_segmentos s JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco WHERE s.all_zero=1 OR s.s13 IS NOT NULL
UNION ALL SELECT 14, CASE WHEN s.all_zero=1 THEN 1 ELSE s.s14 END, m.new_id FROM tmp_eco_segmentos s JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco WHERE s.all_zero=1 OR s.s14 IS NOT NULL
UNION ALL SELECT 15, CASE WHEN s.all_zero=1 THEN 1 ELSE s.s15 END, m.new_id FROM tmp_eco_segmentos s JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco WHERE s.all_zero=1 OR s.s15 IS NOT NULL
UNION ALL SELECT 16, CASE WHEN s.all_zero=1 THEN 1 ELSE s.s16 END, m.new_id FROM tmp_eco_segmentos s JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco WHERE s.all_zero=1 OR s.s16 IS NOT NULL;

-- Conclusiones ecocardiograma
INSERT INTO cardioprieto.conclusiones_ecocardiograma (
  situs, comentario_situs, vasos_normoimplantados, comentario_vasos, concordancia_atrioventricular, comentario_concordancia,
  auricula_izq, ventriculo_izq, funcion_sistolica, funcion_diastolica, motilidad_segmentaria, comentario_motilidad,
  valvula_aortica, comentario_valvula_aortica, valvula_mitral, comentario_valvula_mitral, valvula_tricuspide, comentario_valvula_tricuspide,
  valvula_pulmonar, comentario_valvula_pulmonar, pericardio, comentario_pericardio, defectos_congenitos, comentario_defectos,
  conclusion_texto, comentario_final, estudio_id
)
SELECT
  NULL, NULL, NULL, NULL, NULL, NULL,
  '', '', NULL, NULL, NULL, NULL,
  '', NULL, '', NULL, '', NULL,
  '', NULL, NULL, NULL, NULL, NULL,
  COALESCE(REPLACE(REPLACE(cb.conclusionB, '<br/>', '\n'), '<br>', '\n'), ''),
  COALESCE(NULLIF(ec.conc, ''), ''),
  m.new_id
FROM tmp_ecos_map m
LEFT JOIN cardioprieto_old.eco_conclusionB cb ON cb.idEstudioeco = m.old_id
LEFT JOIN (
  SELECT idEstudioeco,
         GROUP_CONCAT(
           CASE
             WHEN comentario IS NOT NULL AND comentario <> '' AND valor IS NOT NULL AND valor <> '' AND valor REGEXP '[A-Za-z]'
               THEN CONCAT(valor, ' ', comentario)
             WHEN comentario IS NOT NULL AND comentario <> ''
               THEN comentario
             WHEN valor IS NOT NULL AND valor <> '' AND valor REGEXP '[A-Za-z]'
               THEN valor
             ELSE NULL
           END
           ORDER BY orden SEPARATOR '\n'
         ) AS conc
  FROM cardioprieto_old.eco_conclusiones
  WHERE (comentario IS NOT NULL AND comentario <> '')
     OR (valor IS NOT NULL AND valor <> '' AND valor REGEXP '[A-Za-z]')
  GROUP BY idEstudioeco
) ec ON ec.idEstudioeco = m.old_id
ON DUPLICATE KEY UPDATE
  conclusion_texto=VALUES(conclusion_texto), comentario_final=VALUES(comentario_final);

SET FOREIGN_KEY_CHECKS=1;
