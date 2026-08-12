# Modos de deploy

Fecha de referencia: 2026-06-05.

Este repositorio convive con varios modos de despliegue. No son equivalentes y conviene elegirlos deliberadamente.

## Regla para QA

En el servidor de QA `129.212.132.248` no dejar procesos directos tipo `python manage.py runserver`, `node src/server.js` o servicios systemd ad hoc para aplicaciones. QA debe correr con Docker.

Si por error se levanta algo directo, limpiarlo: detener el servicio/proceso, borrar directorios temporales creados para eso, borrar bases temporales si fueron creadas, y verificar que no queden puertos extra escuchando.

## 1. Desarrollo local

Uso: probar rapido en la maquina de desarrollo.

Ejemplos:

```bash
python manage.py runserver 127.0.0.1:8011
docker compose up
```

No usar este modo para dejar algo atendiendo en QA.

## 2. Deploy completo del stack HHCC

Uso: reemplazar o reconstruir el stack principal de Historias Clinicas.

Artefactos habituales:

- `deploy/docker-compose.yml`
- `deploy/nginx/default.conf`
- `deploy/hhcc_app_latest.tar.gz`
- `deploy/nuevo_cardioprieto_latest.tar.gz`
- `deploy/cardioprieto_dump.sql`
- `deploy/start_fresh.sh`

Este modo puede tocar `hhcc_app`, `hhcc_nginx` y `nuevo_cardioprieto`. Es el modo de mayor impacto.

## 3. Update app-only del stack existente

Uso: actualizar solo la imagen de la app Django sobre el stack QA ya existente.

Patron usado por paquetes como:

- `qa_app_only_bundle_qbi2_vademecum_*`
- `qa_app_only_bundle_qbi2_receta_poc_*`
- `qa_app_only_bundle_qbi2_portal_recetas_*`

Hace normalmente:

- cargar una nueva imagen `hhcc_app:latest`;
- hacer backup local del tag anterior;
- fusionar variables de entorno necesarias en `/root/deploy/.env.docker`;
- recrear `app` y `nginx`;
- correr migraciones.

No restaura la base completa y no deberia borrar volumenes.

## 4. Servicio Docker paralelo detras del nginx existente

Uso: publicar una aplicacion independiente sin pisar Historias Clinicas, bajo un prefijo del mismo host.

Ejemplo actual: Holter bajo:

```text
http://129.212.132.248/holter/
```

Patron:

- crear contenedores propios, por ejemplo `holter_app` y `holter_db`;
- conectar la app a la red Docker del stack principal (`deploy_default`) para que `hhcc_nginx` pueda resolverla;
- agregar en `/root/deploy/nginx/default.conf` un `location /prefijo/`;
- validar con `docker exec hhcc_nginx nginx -t`;
- recargar nginx con `docker exec hhcc_nginx nginx -s reload`.

No publicar un puerto publico extra si la intencion es vivir detras de `/prefijo/`.

Antes de cambiar nginx, hacer backup:

```bash
cp /root/deploy/nginx/default.conf /root/deploy/nginx/default.conf.bak_<motivo>_$(date +%Y%m%d_%H%M%S)
```

## Estado Holter QA

Deploy actual:

- codigo remoto: `/root/deploy/holter/`;
- contenedores: `holter_app`, `holter_db`;
- URL publica: `/holter/`;
- nginx actual fue recargado, no reemplazado;
- backup del nginx previo: `/root/deploy/nginx/default.conf.bak_holter_20260604_235529`.

La app Holter fue ajustada para detectar el prefijo `/holter/` y llamar APIs como `/holter/api/...`.

Almacenamiento actual de Holter:

- `STORAGE_PROVIDER=local`;
- volumen Docker: `holter_holter_uploads`;
- ruta host aproximada: `/var/lib/docker/volumes/holter_holter_uploads/_data/uploads`.

Para usar Google Drive:

- cambiar a `STORAGE_PROVIDER=drive`;
- configurar `GOOGLE_SERVICE_ACCOUNT_KEY` o `GOOGLE_APPLICATION_CREDENTIALS`;
- cargar los IDs de carpetas de Drive para subidos e informados en la configuracion de la app.

## Comandos de inspeccion QA

```bash
docker ps
docker logs --tail=80 holter_app
docker logs --tail=80 hhcc_app
docker exec hhcc_nginx nginx -t
curl -I http://127.0.0.1/login/
curl -I http://127.0.0.1/holter/
curl http://127.0.0.1/holter/api/health
```
