-- Migracion de cardioprieto_old -> cardioprieto
-- Ejecutar en instancia nueva (3307) una vez cargado cardioprieto_old

SET FOREIGN_KEY_CHECKS=0;
USE cardioprieto;

-- Tipos de documento
INSERT INTO cardioprieto.tipos_documentos (id, nombre, descripcion)
SELECT id, nombre, descripcion
FROM cardioprieto_old.tipodocumento
ON DUPLICATE KEY UPDATE nombre=VALUES(nombre), descripcion=VALUES(descripcion);

-- Pacientes
INSERT INTO cardioprieto.pacientes (
  id, numDoc, nombre, apellido, fechaNac, sexo, mail, direccion, localidad,
  obraSocial, plan, afiliado, telefono, celular, profesion, referente,
  fechaAlta, deBaja, idTipoDoc_id
)
SELECT
  p.id,
  CAST(p.numDoc AS CHAR),
  p.nombre, p.apellido, p.fechaNac, p.sexo, p.mail, p.direccion, p.localidad,
  p.obraSocial, p.plan, p.afiliado, p.telefono, p.celular, p.profesion, p.referente,
  p.fechaAlta, p.deBaja, p.idTipoDoc
FROM cardioprieto_old.pacientes p
ON DUPLICATE KEY UPDATE
  numDoc=VALUES(numDoc), nombre=VALUES(nombre), apellido=VALUES(apellido), fechaNac=VALUES(fechaNac),
  sexo=VALUES(sexo), mail=VALUES(mail), direccion=VALUES(direccion), localidad=VALUES(localidad),
  obraSocial=VALUES(obraSocial), plan=VALUES(plan), afiliado=VALUES(afiliado), telefono=VALUES(telefono),
  celular=VALUES(celular), profesion=VALUES(profesion), referente=VALUES(referente),
  fechaAlta=VALUES(fechaAlta), deBaja=VALUES(deBaja), idTipoDoc_id=VALUES(idTipoDoc_id);

-- Historias clinicas
INSERT INTO cardioprieto.historias_clinicas (id, fechaAlta, paciente_id)
SELECT id, fechaAlta, idPaciente
FROM cardioprieto_old.historiaclinica
ON DUPLICATE KEY UPDATE fechaAlta=VALUES(fechaAlta), paciente_id=VALUES(paciente_id);

-- Condiciones medicas (enfermedades)
INSERT INTO cardioprieto.condiciones_medicas (id, nombre, orden)
SELECT id, nombre, orden
FROM cardioprieto_old.enfermedades
ON DUPLICATE KEY UPDATE nombre=VALUES(nombre), orden=VALUES(orden);

-- Condiciones medicas por historia
INSERT IGNORE INTO cardioprieto.condiciones_medicas_historias (historia_id, condicion_id)
SELECT idHC, idEnfermedad
FROM cardioprieto_old.hclinica_enfermedades;

-- Indicaciones
INSERT INTO cardioprieto.indicaciones_visitas (
  id, historia_clinica_id, medicamento, ochoHoras, doceHoras, dieciochoHoras, veintiunaHoras, fecha, eliminado
)
SELECT
  i.id, i.idHC, i.medicamento, i.ochoHoras, i.doceHoras, i.dieciochoHoras, i.veintiunaHoras, i.fecha,
  IFNULL(i.eliminado, 0)
FROM cardioprieto_old.indicaciones i
ON DUPLICATE KEY UPDATE
  historia_clinica_id=VALUES(historia_clinica_id), medicamento=VALUES(medicamento), ochoHoras=VALUES(ochoHoras),
  doceHoras=VALUES(doceHoras), dieciochoHoras=VALUES(dieciochoHoras), veintiunaHoras=VALUES(veintiunaHoras),
  fecha=VALUES(fecha), eliminado=VALUES(eliminado);

-- Signos vitales
INSERT INTO cardioprieto.signos_vitales (
  fecha, presion_sistolica, presion_diastolica, peso, glucemia, colesterol, historia_id
)
SELECT
  s.fecha,
  s.presionSistolica,
  s.presionDiastolica,
  CASE
    WHEN s.peso IS NULL THEN NULL
    WHEN s.peso < 0 THEN NULL
    WHEN s.peso > 999.99 THEN NULL
    ELSE s.peso
  END,
  ROUND(s.glucemia),
  ROUND(s.colesterol),
  s.idHC
FROM cardioprieto_old.signosvitales s
ON DUPLICATE KEY UPDATE
  presion_sistolica=VALUES(presion_sistolica), presion_diastolica=VALUES(presion_diastolica),
  peso=VALUES(peso), glucemia=VALUES(glucemia), colesterol=VALUES(colesterol), historia_id=VALUES(historia_id);

-- Comentarios (concatenados por historia y tipo)
INSERT INTO cardioprieto.comentarios_visitas (fecha, comentarios, idHistoriaClinica, tipo)
SELECT
  CAST(CONCAT(MAX(c.fecha), ' 00:00:00') AS DATETIME),
  GROUP_CONCAT(c.comentario ORDER BY c.id SEPARATOR '\n'),
  c.idHistoriaClinica,
  CASE tc.descripcion
    WHEN 'Indicaciones' THEN 'INDIC'
    ELSE 'EVOL'
  END AS tipo
FROM cardioprieto_old.comentarios c
JOIN cardioprieto_old.tipocomentario tc ON tc.id = c.idTipoComentario
WHERE c.eliminado IS NULL OR c.eliminado = 0
GROUP BY c.idHistoriaClinica, c.idTipoComentario
ON DUPLICATE KEY UPDATE
  comentarios=VALUES(comentarios), fecha=VALUES(fecha);

-- Stress
INSERT INTO cardioprieto.stress (
  idStress, idHC, indicacionEstudio, tipoApremio, medicacionMomentoEstudio, medicoSolicitante,
  frecuenciaCardiacaBasal, frecuenciaCardiacaMaxima, presionArterialBasalInicial, presionArterialBasalFinal,
  presionArterialMaximaInicial, presionArterialMaximaFinal, informeErgometria,
  datosEcocardiograficosBasales, datosEcocardiograficosPostEsfuerzoInmediato, conclusion, fecha_estudio
)
SELECT
  s.idStress, s.idHC, s.indicacionEstudio, s.tipoApremio, s.medicacionMomentoEstudio, s.medicoSolicitante,
  s.frecuenciaCardiacaBasal, s.frecuenciaCardiacaMaxima, s.presionArterialBasalInicial, s.presionArterialBasalFinal,
  s.presionArterialMaximaInicial, s.presionArterialMaximaFinal, s.informeErgometria,
  s.datosEcocardiograficosBasales, s.datosEcocardiograficosPostEsfuerzoInmediato, s.conclusion, NULL
FROM cardioprieto_old.stress s
ON DUPLICATE KEY UPDATE
  indicacionEstudio=VALUES(indicacionEstudio), tipoApremio=VALUES(tipoApremio), medicacionMomentoEstudio=VALUES(medicacionMomentoEstudio),
  medicoSolicitante=VALUES(medicoSolicitante), frecuenciaCardiacaBasal=VALUES(frecuenciaCardiacaBasal),
  frecuenciaCardiacaMaxima=VALUES(frecuenciaCardiacaMaxima), presionArterialBasalInicial=VALUES(presionArterialBasalInicial),
  presionArterialBasalFinal=VALUES(presionArterialBasalFinal), presionArterialMaximaInicial=VALUES(presionArterialMaximaInicial),
  presionArterialMaximaFinal=VALUES(presionArterialMaximaFinal), informeErgometria=VALUES(informeErgometria),
  datosEcocardiograficosBasales=VALUES(datosEcocardiograficosBasales), datosEcocardiograficosPostEsfuerzoInmediato=VALUES(datosEcocardiograficosPostEsfuerzoInmediato),
  conclusion=VALUES(conclusion), fecha_estudio=VALUES(fecha_estudio);

-- Carotidas (usa fechaAlta de la historia si no hay fecha)
INSERT INTO cardioprieto.carotidas (
  id, com_derecha, int_derecha, ext_derecha, com_izquierda, int_izquierda, ext_izquierda,
  art_vertebrales, sugerencias, id_com_der, id_com_izq, esp_int_med_der, esp_int_med_izq,
  historia_id, fecha_estudio
)
SELECT
  c.id, c.comDerecha, c.intDerecha, c.extDerecha, c.comIzquierda, c.intIzquierda, c.extIzquierda,
  c.artVertebrales, c.sugerencias, c.idComDer, c.idComIzq, c.espIntMedDer, c.espIntMedIzq,
  c.idHC,
  COALESCE(h.fechaAlta, CURDATE())
FROM cardioprieto_old.carotidas c
LEFT JOIN cardioprieto_old.historiaclinica h ON h.id = c.idHC
ON DUPLICATE KEY UPDATE
  com_derecha=VALUES(com_derecha), int_derecha=VALUES(int_derecha), ext_derecha=VALUES(ext_derecha),
  com_izquierda=VALUES(com_izquierda), int_izquierda=VALUES(int_izquierda), ext_izquierda=VALUES(ext_izquierda),
  art_vertebrales=VALUES(art_vertebrales), sugerencias=VALUES(sugerencias), id_com_der=VALUES(id_com_der), id_com_izq=VALUES(id_com_izq),
  esp_int_med_der=VALUES(esp_int_med_der), esp_int_med_izq=VALUES(esp_int_med_izq), historia_id=VALUES(historia_id), fecha_estudio=VALUES(fecha_estudio);

-- Ecocardiograma -> estudios_ecocardiograma (mapeo parcial)
INSERT INTO cardioprieto.estudios_ecocardiograma (
  id, fecha, peso, talla, presion_sistolica, presion_diastolica, historia_id,
  auricula_izq_diametro, area_auricula_izq, plano_valvular_aortico, septum_diastole,
  pared_diastole, vent_izq_diastolico, vent_izq_sistolico, diametro_tsvi,
  fraccion_simpson, fraccion_acortamiento, tapse, vent_derecho
)
SELECT
  e.id,
  e.fecha,
  CASE
    WHEN e.peso IS NULL THEN NULL
    WHEN e.peso < 0 THEN NULL
    WHEN e.peso > 999.99 THEN NULL
    ELSE e.peso
  END,
  CASE
    WHEN e.talla IS NULL THEN NULL
    WHEN e.talla < 0 THEN NULL
    WHEN e.talla > 10 THEN e.talla / 100
    WHEN e.talla > 9.99 THEN NULL
    ELSE e.talla
  END,
  e.pas,
  e.pad,
  e.idHC,
  CASE WHEN ab.campo1 IS NULL OR ab.campo1 < 0 OR ab.campo1 > 999.99 THEN NULL ELSE ab.campo1 END,
  CASE WHEN ab.campo2 IS NULL OR ab.campo2 < 0 OR ab.campo2 > 999.99 THEN NULL ELSE ab.campo2 END,
  CASE WHEN ab.campo3 IS NULL OR ab.campo3 < 0 OR ab.campo3 > 999.99 THEN NULL ELSE ab.campo3 END,
  CASE WHEN ab.campo4 IS NULL OR ab.campo4 < 0 OR ab.campo4 > 999.99 THEN NULL ELSE ab.campo4 END,
  CASE WHEN ab.campo5 IS NULL OR ab.campo5 < 0 OR ab.campo5 > 999.99 THEN NULL ELSE ab.campo5 END,
  CASE WHEN ab.campo6 IS NULL OR ab.campo6 < 0 OR ab.campo6 > 999.99 THEN NULL ELSE ab.campo6 END,
  CASE WHEN ab.campo7 IS NULL OR ab.campo7 < 0 OR ab.campo7 > 999.99 THEN NULL ELSE ab.campo7 END,
  CASE WHEN ab.campo8 IS NULL OR ab.campo8 < 0 OR ab.campo8 > 999.99 THEN NULL ELSE ab.campo8 END,
  CASE WHEN ab.campo9 IS NULL OR ab.campo9 < 0 OR ab.campo9 > 999.99 THEN NULL ELSE ab.campo9 END,
  CASE WHEN ab.campo10 IS NULL OR ab.campo10 < 0 OR ab.campo10 > 999.99 THEN NULL ELSE ab.campo10 END,
  CASE WHEN ab.campo11 IS NULL OR ab.campo11 < 0 OR ab.campo11 > 999.99 THEN NULL ELSE ab.campo11 END,
  CASE WHEN ab.campo12 IS NULL OR ab.campo12 < 0 OR ab.campo12 > 999.99 THEN NULL ELSE ab.campo12 END
FROM cardioprieto_old.ecocardiograma e
LEFT JOIN cardioprieto_old.eco_analisisbidimensional ab ON ab.idEstudioeco = e.id
ON DUPLICATE KEY UPDATE
  fecha=VALUES(fecha), peso=VALUES(peso), talla=VALUES(talla), presion_sistolica=VALUES(presion_sistolica),
  presion_diastolica=VALUES(presion_diastolica), historia_id=VALUES(historia_id),
  auricula_izq_diametro=VALUES(auricula_izq_diametro), area_auricula_izq=VALUES(area_auricula_izq),
  plano_valvular_aortico=VALUES(plano_valvular_aortico), septum_diastole=VALUES(septum_diastole),
  pared_diastole=VALUES(pared_diastole), vent_izq_diastolico=VALUES(vent_izq_diastolico),
  vent_izq_sistolico=VALUES(vent_izq_sistolico), diametro_tsvi=VALUES(diametro_tsvi),
  fraccion_simpson=VALUES(fraccion_simpson), fraccion_acortamiento=VALUES(fraccion_acortamiento),
  tapse=VALUES(tapse), vent_derecho=VALUES(vent_derecho);

-- Doppler -> MMII (usa fechaAlta de la historia si no hay fecha)
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

-- Mapa de ecocardiogramas (old idEstudioeco -> new estudios_ecocardiograma.id)
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

-- Segmentos ecocardiograma (eco_segmentos -> segmentos_ecocardiograma)
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

-- Conclusiones ecocardiograma (eco_* -> conclusiones_ecocardiograma)
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
