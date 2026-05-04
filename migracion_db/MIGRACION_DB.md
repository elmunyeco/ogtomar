# Migracion viejo_cardioprieto -> nuevo_cardioprieto

## Contexto
- Origen: `cardioprieto` en 3308 (instancia vieja).
- Destino: `cardioprieto` en 3307 (instancia nueva con schema Django).
- Estrategia: dump de la base vieja, cargarla en el mismo servidor nuevo como `cardioprieto_old` y migrar con SQL.

## Archivos
- `00_dump_old.sh`: genera dump desde 3308.
- `01_load_old.sh`: carga dump en 3307 como `cardioprieto_old`.
- `02_migrar.sql`: inserta datos en `cardioprieto` (nuevo schema).

## Ubicacion recomendada del dump legacy
- Guardar el `.sql` de origen en `migracion_db/data/`.
- Naming sugerido: `migracion_db/data/cardioprieto_old_YYYYMMDD.sql`.
- Si se quiere mantener una referencia estable para los scripts/manuales, usar o regenerar `migracion_db/data/cardioprieto_old.sql`.
- Evitar dejar dumps sueltos en la raiz del repo o mezclados con artefactos de deploy.

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

## Comentarios multiples
En el schema viejo, `comentarios` tiene multiples filas por visita:
- `comentarios.idHistoriaClinica`
- `comentarios.fecha`
- `comentarios.idTipoComentario` (1=Visita, 2=Indicaciones)

El error que habia en la migracion era asumir que `comentarios_visitas` debia quedar
consolidada por historia+tipo. Eso estaba mal y terminaba fusionando visitas distintas
de una misma historia en un solo bloque.

La regla correcta es:
- migrar **una fila nueva por cada visita**;
- agrupar por `fecha + idHistoriaClinica + idTipoComentario`;
- mapear `idTipoComentario=1` a `EVOL`;
- mapear `idTipoComentario=2` a `INDIC`;
- usar `fecha 00:00:00` como `datetime` de destino;
- concatenar las filas del grupo con `\n` usando `GROUP_CONCAT(... ORDER BY id SEPARATOR '\n')`;
- normalizar saltos HTML del legacy: `<br>`, `<br/>` y `<br />` deben migrarse como `\n`;
- **no** usar `MAX(fecha)`;
- **no** agrupar solo por `idHistoriaClinica` ni solo por tipo.

Si se agrupa, se destruye la granularidad original y aparecen bloques unificados
como el caso de HC `10254`, donde varias visitas distintas terminan en una
sola fila de `comentarios_visitas` cuando deberian ser `5` bloques, uno por fecha.

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
- `comentarios_visitas` debe bajar respecto de `comentarios` porque varios comentarios
  de una misma visita se concatenan en un solo bloque. Pero no debe bajar hasta
  `1` fila por historia+tipo.
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
- Carga final definitiva ejecutada desde `migracion_db/data/cardioprieto_old_20260415.sql` sobre la instancia `3307`.
- En esa carga final se preservo el circuito `auth_*` / `django_*` del sistema nuevo y solo se reseteo el bloque de datos de negocio migrables.

## Notas operativas
- Para repetir la migracion desde cero, limpiar `cardioprieto` y volver a ejecutar `02_migrar.sql`.
- Si se re-ejecuta la migracion sin limpiar, `signos_vitales` puede duplicar (sin UNIQUE).

## Regla de reseteo previo a una nueva migracion
- Antes de migrar nuevamente datos legacy al sistema nuevo, borrar o recrear **solo los datos de negocio migrables**.
- El circuito de usuarios/permisos/configuracion del sistema nuevo **no debe migrarse desde legacy**.
- La fuente de verdad para usuarios en el sistema actual es el circuito Django/auth del proyecto nuevo, no las tablas legacy `usuarios`/`roles`.
- En consecuencia:
  - si se hace una limpieza selectiva, preservar `auth_*`, `django_*` y cualquier tabla/configuracion propia del sistema nuevo ligada a autenticacion o administracion;
  - si se usa un reset total de `cardioprieto`, asumir que el circuito de usuarios se repone desde el entorno nuevo y **nunca** desde el dump legacy.
- `04_full_reset.sh` sirve para reconstruccion integral de la base objetivo, pero no cambia esta regla: el legacy no manda sobre usuarios.

## Usuarios operativos fijos
- Despues de cada `full reset`, el sistema debe recrear estos usuarios locales del entorno nuevo:
- `eze` / `Furosemida`
- `omar` / `Corbis5`
- Las passwords son case sensitive.
- No deben migrarse desde legacy ni quedar sujetas al contenido de `cardioprieto_old`.


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
comentarios -> comentarios_visitas	comentarios	79468	comentarios_visitas	8266	1 fila nueva por visita (fecha+historia+tipo), concatenada con \n
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
comentarios -> comentarios_visitas	comentarios	79468	comentarios_visitas	8266	1 fila nueva por visita (fecha+historia+tipo), concatenada con \n
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
comentarios -> comentarios_visitas	comentarios	79468	comentarios_visitas	8266	1 fila nueva por visita (fecha+historia+tipo), concatenada con \n
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
