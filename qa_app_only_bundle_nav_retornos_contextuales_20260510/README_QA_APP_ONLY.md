# QA app-only bundle - navegacion contextual

Fecha: 2026-05-10

Este paquete actualiza solo la imagen de la aplicacion `hhcc_app:latest` en el stack existente de QA. No restaura base de datos, no toca volumenes y no modifica el `docker-compose.yml`.

## Contenido

- `hhcc_app_latest.tar.gz`: imagen Docker de la aplicacion.
- `update_existing_qa_stack.sh`: script para cargar la imagen y recrear `app` + `nginx`.

## Pasos para pasar a QA

1. Copiar `qa_app_only_bundle_nav_retornos_contextuales_20260510.tar.gz` al servidor de QA.

2. Descomprimir el paquete:

   ```bash
   tar -xzf qa_app_only_bundle_nav_retornos_contextuales_20260510.tar.gz
   cd qa_app_only_bundle_nav_retornos_contextuales_20260510
   ```

3. Ejecutar el update:

   ```bash
   chmod +x update_existing_qa_stack.sh
   ./update_existing_qa_stack.sh
   ```

4. Verificar en navegador:

   - `/pacientes/`: abrir una historia desde el listado de pacientes y confirmar que el retorno diga `Pacientes`.
   - `/historias/`: abrir una historia desde el listado de historias y confirmar que el retorno diga `Historias`.
   - En pantallas de carga o edicion, confirmar la barra fija inferior con retorno corto a la izquierda y accion principal a la derecha.
   - En listados y selectores, confirmar el retorno corto arriba cuando corresponda.

5. Si algo falla, hacer rollback con el tag que imprime el script al final. Ejemplo:

   ```bash
   docker tag hhcc_app:qa_backup_YYYYMMDD_HHMMSS hhcc_app:latest
   cd /root/deploy
   docker-compose up -d --force-recreate app nginx
   ```

   Si el servidor usa Compose v2:

   ```bash
   docker compose up -d --force-recreate app nginx
   ```

## Notas

- El script espera que el stack existente este en `/root/deploy`.
- El script valida el `.tar.gz` antes de cargar la imagen.
- Antes de cargar la nueva imagen, si existe `hhcc_app:latest`, crea un backup local con formato `hhcc_app:qa_backup_YYYYMMDD_HHMMSS`.
- La actualizacion es reversible porque no toca datos ni configuracion del stack.
