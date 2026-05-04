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
-- Una sola pasada sobre el join evita repetir 16 veces el mismo plan.
INSERT IGNORE INTO cardioprieto.segmentos_ecocardiograma (numero_segmento, estado, estudio_id)
SELECT
  n.numero_segmento,
  CASE
    WHEN s.all_zero = 1 THEN 1
    WHEN n.numero_segmento = 1 THEN s.s1
    WHEN n.numero_segmento = 2 THEN s.s2
    WHEN n.numero_segmento = 3 THEN s.s3
    WHEN n.numero_segmento = 4 THEN s.s4
    WHEN n.numero_segmento = 5 THEN s.s5
    WHEN n.numero_segmento = 6 THEN s.s6
    WHEN n.numero_segmento = 7 THEN s.s7
    WHEN n.numero_segmento = 8 THEN s.s8
    WHEN n.numero_segmento = 9 THEN s.s9
    WHEN n.numero_segmento = 10 THEN s.s10
    WHEN n.numero_segmento = 11 THEN s.s11
    WHEN n.numero_segmento = 12 THEN s.s12
    WHEN n.numero_segmento = 13 THEN s.s13
    WHEN n.numero_segmento = 14 THEN s.s14
    WHEN n.numero_segmento = 15 THEN s.s15
    WHEN n.numero_segmento = 16 THEN s.s16
  END AS estado,
  m.new_id
FROM tmp_eco_segmentos s
JOIN tmp_ecos_map m ON m.old_id = s.idEstudioeco
JOIN (
  SELECT 1 AS numero_segmento UNION ALL
  SELECT 2 UNION ALL
  SELECT 3 UNION ALL
  SELECT 4 UNION ALL
  SELECT 5 UNION ALL
  SELECT 6 UNION ALL
  SELECT 7 UNION ALL
  SELECT 8 UNION ALL
  SELECT 9 UNION ALL
  SELECT 10 UNION ALL
  SELECT 11 UNION ALL
  SELECT 12 UNION ALL
  SELECT 13 UNION ALL
  SELECT 14 UNION ALL
  SELECT 15 UNION ALL
  SELECT 16
) n
WHERE s.all_zero = 1
   OR (n.numero_segmento = 1 AND s.s1 IS NOT NULL)
   OR (n.numero_segmento = 2 AND s.s2 IS NOT NULL)
   OR (n.numero_segmento = 3 AND s.s3 IS NOT NULL)
   OR (n.numero_segmento = 4 AND s.s4 IS NOT NULL)
   OR (n.numero_segmento = 5 AND s.s5 IS NOT NULL)
   OR (n.numero_segmento = 6 AND s.s6 IS NOT NULL)
   OR (n.numero_segmento = 7 AND s.s7 IS NOT NULL)
   OR (n.numero_segmento = 8 AND s.s8 IS NOT NULL)
   OR (n.numero_segmento = 9 AND s.s9 IS NOT NULL)
   OR (n.numero_segmento = 10 AND s.s10 IS NOT NULL)
   OR (n.numero_segmento = 11 AND s.s11 IS NOT NULL)
   OR (n.numero_segmento = 12 AND s.s12 IS NOT NULL)
   OR (n.numero_segmento = 13 AND s.s13 IS NOT NULL)
   OR (n.numero_segmento = 14 AND s.s14 IS NOT NULL)
   OR (n.numero_segmento = 15 AND s.s15 IS NOT NULL)
   OR (n.numero_segmento = 16 AND s.s16 IS NOT NULL);

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
