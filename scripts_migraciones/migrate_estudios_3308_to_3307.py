#!/usr/bin/env python3
import MySQLdb
from MySQLdb.cursors import DictCursor
from datetime import date

SRC = dict(host="127.0.0.1", user="root", passwd="Corbis5", db="cardioprieto", port=3308, charset="latin1")
DST = dict(host="127.0.0.1", user="root", passwd="Corbis5", db="cardioprieto", port=3307, charset="utf8mb4")


def connect(cfg):
    return MySQLdb.connect(**cfg)


def to_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def clamp_decimal(val, max_abs):
    if val is None:
        return None
    try:
        v = float(val)
    except (TypeError, ValueError):
        return None
    if v > max_abs:
        return max_abs
    if v < -max_abs:
        return -max_abs
    return v


def normalize_text(value):
    if value is None:
        return None
    text = str(value)
    text = text.replace("<br/>", "\n").replace("<br />", "\n").replace("<br>", "\n")
    return text


def main():
    src = connect(SRC)
    dst = connect(DST)

    src_cur = src.cursor(DictCursor)
    dst_cur = dst.cursor(DictCursor)

    # Historias validas en destino
    dst_cur.execute("SELECT id FROM historias_clinicas")
    historia_ids = {row["id"] for row in dst_cur.fetchall()}

    today = date.today()

    # 1) CAROTIDAS
    src_cur.execute("SELECT * FROM carotidas")
    carotidas_rows = src_cur.fetchall()
    inserted_carotidas = 0
    for r in carotidas_rows:
        hid = r["idHC"]
        if hid not in historia_ids:
            continue
        dst_cur.execute(
            """
            REPLACE INTO carotidas (
                id, historia_id, com_derecha, int_derecha, ext_derecha,
                com_izquierda, int_izquierda, ext_izquierda, art_vertebrales,
                sugerencias, id_com_der, id_com_izq, esp_int_med_der,
                esp_int_med_izq, fecha_estudio
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                r["id"], hid, r.get("comDerecha"), r.get("intDerecha"), r.get("extDerecha"),
                r.get("comIzquierda"), r.get("intIzquierda"), r.get("extIzquierda"),
                normalize_text(r.get("artVertebrales")),
                normalize_text(r.get("sugerencias")),
                r.get("idComDer"),
                r.get("idComIzq"), r.get("espIntMedDer"), r.get("espIntMedIzq"), today
            ),
        )
        inserted_carotidas += 1

    # 2) STRESS (ECOSTRESS)
    src_cur.execute("SELECT * FROM stress")
    stress_rows = src_cur.fetchall()
    inserted_stress = 0
    for r in stress_rows:
        hid = r["idHC"]
        if hid not in historia_ids:
            continue
        dst_cur.execute(
            """
            REPLACE INTO stress (
                idStress, indicacionEstudio, tipoApremio, medicacionMomentoEstudio,
                medicoSolicitante, frecuenciaCardiacaBasal, frecuenciaCardiacaMaxima,
                presionArterialBasalInicial, presionArterialBasalFinal,
                presionArterialMaximaInicial, presionArterialMaximaFinal,
                informeErgometria, datosEcocardiograficosBasales,
                datosEcocardiograficosPostEsfuerzoInmediato, conclusion, idHC,
                fecha_estudio
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                r["idStress"], r.get("indicacionEstudio"), r.get("tipoApremio"),
                normalize_text(r.get("medicacionMomentoEstudio")),
                normalize_text(r.get("medicoSolicitante")),
                r.get("frecuenciaCardiacaBasal"), r.get("frecuenciaCardiacaMaxima"),
                r.get("presionArterialBasalInicial"), r.get("presionArterialBasalFinal"),
                r.get("presionArterialMaximaInicial"), r.get("presionArterialMaximaFinal"),
                normalize_text(r.get("informeErgometria")),
                normalize_text(r.get("datosEcocardiograficosBasales")),
                normalize_text(r.get("datosEcocardiograficosPostEsfuerzoInmediato")),
                normalize_text(r.get("conclusion")),
                hid, today
            ),
        )
        inserted_stress += 1

    # 3) DOPPLER -> MMII
    src_cur.execute("SELECT * FROM doppler")
    doppler_rows = src_cur.fetchall()
    inserted_mmii = 0
    for r in doppler_rows:
        hid = r["idHC"]
        if hid not in historia_ids:
            continue
        dst_cur.execute(
            """
            REPLACE INTO mmii (
                idMMII, artFemComunDerecha, artFemSuperficialDerecha, artFemProfundaDerecha,
                artPopliteaDerecha, artInfrapatelaresDerecha, artFemComunIzquierda,
                artFemSuperficialIzquierda, artFemProfundaIzquierda, artPopliteaIzquierda,
                artInfrapatelaresIzquierda, conclusion, idHC, fecha_estudio
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                r["idDoppler"], r.get("artFemComunDerecha"), r.get("artFemSuperficialDerecha"),
                r.get("artFemProfundaDerecha"), r.get("artPopliteaDerecha"),
                r.get("artInfrapatelaresDerecha"), r.get("artFemComunIzquierda"),
                r.get("artFemSuperficialIzquierda"), r.get("artFemProfundaIzquierda"),
                r.get("artPopliteaIzquierda"), r.get("artInfrapatelaresIzquierda"),
                normalize_text(r.get("conclusion")), hid, today
            ),
        )
        inserted_mmii += 1

    # 4) ECOCARDIOGRAMA + ANALISIS + SEGMENTOS + CONCLUSIONES
    src_cur.execute("SELECT * FROM eco_analisisbidimensional")
    bid_rows = {r["idEstudioeco"]: r for r in src_cur.fetchall()}

    src_cur.execute("SELECT * FROM eco_analisisdoppler")
    dop_rows = {r["idEstudioeco"]: r for r in src_cur.fetchall()}

    src_cur.execute("SELECT * FROM eco_segmentos")
    seg_rows = {r["idEstudioeco"]: r for r in src_cur.fetchall()}

    src_cur.execute("SELECT * FROM eco_conclusionB")
    concl_b_rows = {r["idEstudioeco"]: r for r in src_cur.fetchall()}

    src_cur.execute("SELECT * FROM eco_conclusiones")
    concl_items = {}
    for r in src_cur.fetchall():
        concl_items.setdefault(r["idEstudioeco"], []).append(r)

    src_cur.execute("SELECT * FROM ecocardiograma")
    eco_rows = src_cur.fetchall()
    inserted_eco = 0
    inserted_seg = 0
    inserted_conc = 0

    for e in eco_rows:
        hid = e["idHC"]
        if hid not in historia_ids:
            continue
        bid = bid_rows.get(e["id"], {})
        dop = dop_rows.get(e["id"], {})

        dst_cur.execute(
            """
            REPLACE INTO estudios_ecocardiograma (
                id, fecha, peso, talla, presion_sistolica, presion_diastolica,
                auricula_izq_diametro, area_auricula_izq, plano_valvular_aortico,
                septum_diastole, pared_diastole, vent_izq_diastolico, vent_izq_sistolico,
                diametro_tsvi, fraccion_simpson, fraccion_acortamiento, tapse, vent_derecho,
                valvula_pulmonar, valvula_aortica, tracto_vent_izq, onda_e_mitral, onda_a_mitral,
                onda_e_tricuspidea, onda_a_tricuspidea, strain_longitudinal, historia_id
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                e["id"],
                e.get("fecha"),
                clamp_decimal(e.get("peso"), 999.99),
                clamp_decimal(e.get("talla"), 9.99),
                e.get("pas"),
                e.get("pad"),
                clamp_decimal(bid.get("campo1"), 999.99),
                clamp_decimal(bid.get("campo2"), 999.99),
                clamp_decimal(bid.get("campo3"), 999.99),
                clamp_decimal(bid.get("campo4"), 999.99),
                clamp_decimal(bid.get("campo5"), 999.99),
                clamp_decimal(bid.get("campo6"), 999.99),
                clamp_decimal(bid.get("campo7"), 999.99),
                clamp_decimal(bid.get("campo8"), 999.99),
                clamp_decimal(bid.get("campo9"), 999.99),
                clamp_decimal(bid.get("campo10"), 999.99),
                clamp_decimal(bid.get("campo11"), 999.99),
                clamp_decimal(bid.get("campo12"), 999.99),
                clamp_decimal(dop.get("vPulmonar"), 999.99),
                clamp_decimal(dop.get("vAortica"), 999.99),
                clamp_decimal(dop.get("vIzquierdo"), 999.99),
                clamp_decimal(dop.get("vMitralE"), 999.99),
                clamp_decimal(dop.get("vMitralA"), 999.99),
                clamp_decimal(dop.get("vTricuspideaE"), 999.99),
                clamp_decimal(dop.get("vTricuspideaA"), 999.99),
                clamp_decimal(dop.get("strainGlobal"), 999.99),
                hid
            ),
        )
        inserted_eco += 1

        seg = seg_rows.get(e["id"])
        if seg:
            for i in range(1, 17):
                estado = seg.get(f"s{i}")
                if estado is None:
                    estado = 1
                dst_cur.execute(
                    """
                    REPLACE INTO segmentos_ecocardiograma (estudio_id, numero_segmento, estado)
                    VALUES (%s,%s,%s)
                    """,
                    (e["id"], i, estado),
                )
                inserted_seg += 1

        items = concl_items.get(e["id"], [])
        if items or e.get("comFinal") or concl_b_rows.get(e["id"]):
            data = {
                "auricula_izq": "",
                "ventriculo_izq": "",
                "funcion_sistolica": None,
                "funcion_diastolica": None,
                "motilidad_segmentaria": None,
                "comentario_motilidad": None,
                "valvula_aortica": "",
                "comentario_valvula_aortica": None,
                "valvula_mitral": "",
                "comentario_valvula_mitral": None,
                "valvula_tricuspide": "",
                "comentario_valvula_tricuspide": None,
                "valvula_pulmonar": "",
                "comentario_valvula_pulmonar": None,
                "pericardio": None,
                "comentario_pericardio": None,
                "defectos_congenitos": None,
                "comentario_defectos": None,
                "situs": None,
                "comentario_situs": None,
                "vasos_normoimplantados": None,
                "comentario_vasos": None,
                "concordancia_atrioventricular": None,
                "comentario_concordancia": None,
                "conclusion_texto": "",
                "comentario_final": normalize_text(e.get("comFinal")) or "",
            }

            for it in items:
                orden = it.get("orden")
                valor = it.get("valor")
                comentario = it.get("comentario")
                if orden == 1:
                    data["auricula_izq"] = valor or ""
                elif orden == 2:
                    data["ventriculo_izq"] = valor or ""
                elif orden == 3:
                    data["funcion_sistolica"] = to_int(valor)
                elif orden == 4:
                    data["funcion_diastolica"] = to_int(valor)
                elif orden == 5:
                    data["motilidad_segmentaria"] = to_int(valor)
                    data["comentario_motilidad"] = normalize_text(comentario)
                elif orden == 6:
                    data["valvula_aortica"] = valor or ""
                    data["comentario_valvula_aortica"] = normalize_text(comentario)
                elif orden == 7:
                    data["valvula_mitral"] = valor or ""
                    data["comentario_valvula_mitral"] = normalize_text(comentario)
                elif orden == 8:
                    data["valvula_tricuspide"] = valor or ""
                    data["comentario_valvula_tricuspide"] = normalize_text(comentario)
                elif orden == 9:
                    data["valvula_pulmonar"] = valor or ""
                    data["comentario_valvula_pulmonar"] = normalize_text(comentario)
                elif orden == 10:
                    data["pericardio"] = to_int(valor)
                    data["comentario_pericardio"] = normalize_text(comentario)
                elif orden == 11:
                    data["defectos_congenitos"] = to_int(valor)
                    data["comentario_defectos"] = normalize_text(comentario)
                elif orden == 12:
                    data["situs"] = to_int(valor)
                    data["comentario_situs"] = normalize_text(comentario)
                elif orden == 13:
                    data["vasos_normoimplantados"] = to_int(valor)
                    data["comentario_vasos"] = normalize_text(comentario)
                elif orden == 14:
                    data["concordancia_atrioventricular"] = to_int(valor)
                    data["comentario_concordancia"] = normalize_text(comentario)

            cb = concl_b_rows.get(e["id"]) or {}
            if cb.get("conclusionB"):
                data["conclusion_texto"] = normalize_text(cb.get("conclusionB")) or ""

            dst_cur.execute(
                """
                REPLACE INTO conclusiones_ecocardiograma (
                    estudio_id, situs, comentario_situs, vasos_normoimplantados,
                    comentario_vasos, concordancia_atrioventricular, comentario_concordancia,
                    auricula_izq, ventriculo_izq, funcion_sistolica, funcion_diastolica,
                    motilidad_segmentaria, comentario_motilidad, valvula_aortica,
                    comentario_valvula_aortica, valvula_mitral, comentario_valvula_mitral,
                    valvula_tricuspide, comentario_valvula_tricuspide, valvula_pulmonar,
                    comentario_valvula_pulmonar, pericardio, comentario_pericardio,
                    defectos_congenitos, comentario_defectos, conclusion_texto, comentario_final
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    e["id"], data["situs"], data["comentario_situs"], data["vasos_normoimplantados"],
                    data["comentario_vasos"], data["concordancia_atrioventricular"], data["comentario_concordancia"],
                    data["auricula_izq"], data["ventriculo_izq"], data["funcion_sistolica"], data["funcion_diastolica"],
                    data["motilidad_segmentaria"], data["comentario_motilidad"], data["valvula_aortica"],
                    data["comentario_valvula_aortica"], data["valvula_mitral"], data["comentario_valvula_mitral"],
                    data["valvula_tricuspide"], data["comentario_valvula_tricuspide"], data["valvula_pulmonar"],
                    data["comentario_valvula_pulmonar"], data["pericardio"], data["comentario_pericardio"],
                    data["defectos_congenitos"], data["comentario_defectos"], data["conclusion_texto"], data["comentario_final"],
                ),
            )
            inserted_conc += 1

    dst.commit()

    print("carotidas", inserted_carotidas)
    print("stress", inserted_stress)
    print("mmii", inserted_mmii)
    print("ecocardiograma", inserted_eco)
    print("segmentos", inserted_seg)
    print("conclusiones", inserted_conc)

    src.close()
    dst.close()


if __name__ == "__main__":
    main()
