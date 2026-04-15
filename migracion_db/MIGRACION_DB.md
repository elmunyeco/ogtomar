# Migracion viejo_cardioprieto -> nuevo_cardioprieto

## Contexto
- Origen: `cardioprieto` en 3308 (instancia vieja).
- Destino: `cardioprieto` en 3307 (instancia nueva con schema Django).
- Estrategia: dump de la base vieja, cargarla en el mismo servidor nuevo como `cardioprieto_old` y migrar con SQL.

## Archivos
- `00_dump_old.sh`: genera dump desde 3308.
- `01_load_old.sh`: carga dump en 3307 como `cardioprieto_old`.
- `02_migrar.sql`: inserta datos en `cardioprieto` (nuevo schema).

## Pasos
1. Dump desde la instancia vieja:
   ```sh
   ./00_dump_old.sh cardioprieto_old.sql
   ```
2. Cargar dump en la instancia nueva (3307):
   ```sh
   ./01_load_old.sh cardioprieto_old.sql cardioprieto_old
   ```
3. Ejecutar la migracion SQL en la instancia nueva:
   ```sh
   mariadb -h 127.0.0.1 -P 3307 -uroot -pCorbis5 < 02_migrar.sql
   ```

## Cambios de esquema (resumen)
- `tipodocumento` -> `tipos_documentos`
- `pacientes.idTipoDoc` -> `pacientes.idTipoDoc_id`
- `historiaclinica` -> `historias_clinicas`
- `enfermedades` + `hclinica_enfermedades` -> `condiciones_medicas` + `condiciones_medicas_historias`
- `indicaciones` -> `indicaciones_visitas`
- `signosvitales` -> `signos_vitales`
- `comentarios` + `tipocomentario` -> `comentarios_visitas`
- `carotidas` agrega `fecha_estudio`
- `stress` agrega `fecha_estudio`
- `ecocardiograma` -> `estudios_ecocardiograma` (mapeo parcial)

## Comentarios multiples (concatenacion)
En el schema viejo, `comentarios` tiene multiples filas por historia y tipo:
- `comentarios.idHistoriaClinica`
- `comentarios.idTipoComentario` (1=Visita, 2=Indicaciones)

En el schema nuevo, `comentarios_visitas` espera un solo campo `comentarios` por historia+tipo.
La migracion concatena los comentarios con `\n`, usando `GROUP_CONCAT` ordenado por `id`:
- Tipo `Visita` -> `EVOL`
- Tipo `Indicaciones` -> `INDIC`

La fecha se toma como `MAX(fecha)` del grupo.

## Advertencias / TODO
- `eco_conclusiones`, `eco_conclusionB`, `eco_analisis*`, `eco_segmentos` requieren mapeo detallado.
  En `02_migrar.sql` solo se migra lo basico de `ecocardiograma`.
- `doppler` -> `mmii`: pendiente de mapeo (schema distinto).
- Validar que las FK en nuevas tablas no rompan la carga (hay `FOREIGN_KEY_CHECKS=0`).

## Verificacion rapida
```sql
SELECT COUNT(*) FROM cardioprieto_old.pacientes;
SELECT COUNT(*) FROM cardioprieto.pacientes;
SELECT COUNT(*) FROM cardioprieto_old.comentarios;
SELECT COUNT(*) FROM cardioprieto.comentarios_visitas;
```

## Verificacion de volumen (post-migracion)
Resultado de conteos (old vs new):

```
old_pacientes          11564
new_pacientes          11564
old_historias          11564
new_historias          11564
old_comentarios        79468
new_comentarios_visitas 16532
old_indicaciones       17908
new_indicaciones       17908
old_signosvitales      11921
new_signos_vitales     23842
old_carotidas          3968
new_carotidas          3968
old_stress             107
new_stress             107
old_ecocardiograma     12592
new_ecocardiograma     12592
```

Notas:
- `comentarios_visitas` baja por consolidacion (1 fila por historia+tipo).
- `signos_vitales` duplico vs old porque la tabla nueva no tiene restriccion de unicidad por (`historia_id`, `fecha`). Si se necesita 1 registro por historia+fecha, agregar unique o deduplicar.

## Signos vitales: comportamiento actual de UI y riesgo de duplicados
- La DB nueva permite multiples filas por (`historia_id`, `fecha`) porque no hay UNIQUE.
- La UI **no muestra multiples entradas del mismo dia**: toma la primera.
  - `detalle_historia` / `detalle_historia_con_historial`: `filter(fecha=fecha).first()`.
  - `get_historia_data`: `.latest("fecha")`.
- Implicancia: si hay mas de un registro en un mismo dia, **solo se ve uno** en la vista.
- Recomendacion futura: si aparecen multiples mediciones en un mismo dia, ajustar UI para listar todas o usar timestamp real (si alguna vez se captura).

## Estado de migracion
- Dump viejo generado en `migracion_db/data/cardioprieto_old.sql`.
- Cargado como `cardioprieto_old` en 3307.
- Migracion `02_migrar.sql` ejecutada OK.
- Ajustes de rango aplicados:
  - `signos_vitales.peso` limita valores fuera de rango (>999.99 o negativos) a NULL.
  - `estudios_ecocardiograma.peso` idem.
  - `estudios_ecocardiograma.talla`: si viene en cm (>10) se divide por 100; fuera de rango se setea NULL.

## Notas operativas
- Para repetir la migracion desde cero, limpiar `cardioprieto` y volver a ejecutar `02_migrar.sql`.
- Si se re-ejecuta la migracion sin limpiar, `signos_vitales` puede duplicar (sin UNIQUE).


## Diff inteligente (conteos)

```tsv
map	old_table	old_count	new_table	new_count	nota
tipodocumento -> tipos_documentos	tipodocumento	4	tipos_documentos	4	
pacientes -> pacientes	pacientes	11564	pacientes	11564	
historiaclinica -> historias_clinicas	historiaclinica	11564	historias_clinicas	11564	
enfermedades -> condiciones_medicas	enfermedades	25	condiciones_medicas	25	
hclinica_enfermedades -> condiciones_medicas_historias	hclinica_enfermedades	645	condiciones_medicas_historias	645	
indicaciones -> indicaciones_visitas	indicaciones	17908	indicaciones_visitas	17908	
signosvitales -> signos_vitales	signosvitales	11921	signos_vitales	11921	
comentarios -> comentarios_visitas	comentarios	79468	comentarios_visitas	8266	concat por historia+tipo; MAX(fecha), GROUP_CONCAT
carotidas -> carotidas	carotidas	3968	carotidas	3968	
stress -> stress	stress	107	stress	107	
ecocardiograma -> estudios_ecocardiograma	ecocardiograma	12592	estudios_ecocardiograma	12592	
estudios -> estudios_* (sum)	estudios	16731	estudios_ecocardiograma+stress+carotidas+mmii	16667	sumatoria
doppler -> mmii	doppler	65	mmii	0	PENDIENTE migracion
eco_analisisbidimensional -> conclusiones_ecocardiograma	eco_analisisbidimensional	12558	conclusiones_ecocardiograma	0	PENDIENTE
eco_analisisdoppler -> conclusiones_ecocardiograma	eco_analisisdoppler	12558	conclusiones_ecocardiograma	0	PENDIENTE
eco_conclusionB -> conclusiones_ecocardiograma	eco_conclusionB	10194	conclusiones_ecocardiograma	0	PENDIENTE
eco_conclusiones -> conclusiones_ecocardiograma	eco_conclusiones	175861	conclusiones_ecocardiograma	0	PENDIENTE
eco_segmentos -> segmentos_ecocardiograma	eco_segmentos	12557	segmentos_ecocardiograma	0	PENDIENTE
estudios_comentarios -> comentarios_visitas	estudios_comentarios	29	comentarios_visitas	8266	NO migrado
tipo_estudios -> N/A	tipo_estudios	4	N/A		NO migrado
tipocomentario -> N/A	tipocomentario	2	N/A		NO migrado
roles -> N/A	roles	2	N/A		NO migrado
usuarios -> N/A	usuarios	6	N/A		NO migrado (reemplazado por auth_user)
```


## Migraciones completadas ahora (pendientes resueltas)

- `doppler -> mmii`: se migra a `mmii` usando `idDoppler` como PK (`idMMII`) y `fecha_estudio` desde `historiaclinica.fechaAlta`.
- `eco_segmentos -> segmentos_ecocardiograma`: se desnormaliza en filas por segmento (1..16) con `estado`.
- `eco_conclusionB`, `eco_conclusiones`, `eco_analisisbidimensional`, `eco_analisisdoppler` -> `conclusiones_ecocardiograma`:
  - Se crea un mapeo `old ecocardiograma` -> `new estudios_ecocardiograma` usando `ROW_NUMBER()` por `(historia_id, fecha)`.
  - `conclusion_texto` toma `eco_conclusionB.conclusionB`.
  - `comentario_final` concatena `eco_conclusiones` (orden+valor+comentario) + analisis bidimensional + analisis doppler.
  - Campos de texto obligatorios se dejan en `''` si no hay dato equivalente.


### Script adicional

- `03_migrar_pendientes.sql`: permite ejecutar solo las partes nuevas (doppler/mmii y eco_*).


## Diff inteligente (conteos, actualizado)

```tsv
map	old_table	old_count	new_table	new_count	nota
tipodocumento -> tipos_documentos	tipodocumento	4	tipos_documentos	4	
pacientes -> pacientes	pacientes	11564	pacientes	11564	
historiaclinica -> historias_clinicas	historiaclinica	11564	historias_clinicas	11564	
enfermedades -> condiciones_medicas	enfermedades	25	condiciones_medicas	25	
hclinica_enfermedades -> condiciones_medicas_historias	hclinica_enfermedades	645	condiciones_medicas_historias	645	
indicaciones -> indicaciones_visitas	indicaciones	17908	indicaciones_visitas	17908	
signosvitales -> signos_vitales	signosvitales	11921	signos_vitales	11921	
comentarios -> comentarios_visitas	comentarios	79468	comentarios_visitas	8266	concat por historia+tipo; MAX(fecha), GROUP_CONCAT
carotidas -> carotidas	carotidas	3968	carotidas	3968	
stress -> stress	stress	107	stress	107	
ecocardiograma -> estudios_ecocardiograma	ecocardiograma	12592	estudios_ecocardiograma	12592	
doppler -> mmii	doppler	65	mmii	65	
eco_segmentos -> segmentos_ecocardiograma	eco_segmentos	12557	segmentos_ecocardiograma	200912	
eco_conclusionB -> conclusiones_ecocardiograma	eco_conclusionB	10194	conclusiones_ecocardiograma	12592	
estudios -> estudios_* (sum)	estudios	16731	estudios_ecocardiograma+stress+carotidas+mmii	16732	sumatoria
eco_analisisbidimensional -> conclusiones_ecocardiograma	eco_analisisbidimensional	12558	conclusiones_ecocardiograma	12592	migrado a comentario_final
eco_analisisdoppler -> conclusiones_ecocardiograma	eco_analisisdoppler	12558	conclusiones_ecocardiograma	12592	migrado a comentario_final
eco_conclusiones -> conclusiones_ecocardiograma	eco_conclusiones	175861	conclusiones_ecocardiograma	12592	migrado a comentario_final
estudios_comentarios -> comentarios_visitas	estudios_comentarios	29	comentarios_visitas	8266	NO migrado
tipo_estudios -> N/A	tipo_estudios	4	N/A		NO migrado
tipocomentario -> N/A	tipocomentario	2	N/A		NO migrado
roles -> N/A	roles	2	N/A		NO migrado
usuarios -> N/A	usuarios	6	N/A		NO migrado (reemplazado por auth_user)
```


## Full reset (idempotente)

Script: `04_full_reset.sh`

- Drop + create `cardioprieto`
- Carga `new_schema.sql`
- Ejecuta `02_migrar.sql` + `03_migrar_pendientes.sql`
- Chequea existencia de `cardioprieto_old`

`03_migrar_pendientes.sql` usa `INSERT IGNORE` en segmentos para re-ejecucion segura.


## Diff inteligente (conteos, post-reset)

```tsv
map	old_table	old_count	new_table	new_count	nota
tipodocumento -> tipos_documentos	tipodocumento	4	tipos_documentos	4	
pacientes -> pacientes	pacientes	11564	pacientes	11564	
historiaclinica -> historias_clinicas	historiaclinica	11564	historias_clinicas	11564	
enfermedades -> condiciones_medicas	enfermedades	25	condiciones_medicas	25	
hclinica_enfermedades -> condiciones_medicas_historias	hclinica_enfermedades	645	condiciones_medicas_historias	645	
indicaciones -> indicaciones_visitas	indicaciones	17908	indicaciones_visitas	17908	
signosvitales -> signos_vitales	signosvitales	11921	signos_vitales	11921	
comentarios -> comentarios_visitas	comentarios	79468	comentarios_visitas	8266	concat por historia+tipo; MAX(fecha), GROUP_CONCAT
carotidas -> carotidas	carotidas	3968	carotidas	3968	
stress -> stress	stress	107	stress	107	
ecocardiograma -> estudios_ecocardiograma	ecocardiograma	12592	estudios_ecocardiograma	12592	
doppler -> mmii	doppler	65	mmii	65	
eco_segmentos -> segmentos_ecocardiograma	eco_segmentos	12557	segmentos_ecocardiograma	200912	
eco_conclusionB -> conclusiones_ecocardiograma	eco_conclusionB	10194	conclusiones_ecocardiograma	12592	
estudios -> estudios_* (sum)	estudios	16731	estudios_ecocardiograma+stress+carotidas+mmii	16732	sumatoria
eco_analisisbidimensional -> conclusiones_ecocardiograma	eco_analisisbidimensional	12558	conclusiones_ecocardiograma	12592	migrado a comentario_final
eco_analisisdoppler -> conclusiones_ecocardiograma	eco_analisisdoppler	12558	conclusiones_ecocardiograma	12592	migrado a comentario_final
eco_conclusiones -> conclusiones_ecocardiograma	eco_conclusiones	175861	conclusiones_ecocardiograma	12592	migrado a comentario_final
estudios_comentarios -> comentarios_visitas	estudios_comentarios	29	comentarios_visitas	8266	NO migrado
tipo_estudios -> N/A	tipo_estudios	4	N/A		NO migrado
tipocomentario -> N/A	tipocomentario	2	N/A		NO migrado
roles -> N/A	roles	2	N/A		NO migrado
usuarios -> N/A	usuarios	6	N/A		NO migrado (reemplazado por auth_user)
```


## Fix login (QA)

Si hay usuarios pero no loguea, el hash puede haber quedado mal por ejecuciones con saltos/indent en `manage.py shell -c`.

Comando correcto (una sola linea):

```bash
docker exec -i hhcc_app python3 manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); u=User.objects.get(username='eze'); u.set_password('Furosemida'); u.save(); u=User.objects.get(username='omar'); u.set_password('Corbis5'); u.save(); print('ok')"
```
