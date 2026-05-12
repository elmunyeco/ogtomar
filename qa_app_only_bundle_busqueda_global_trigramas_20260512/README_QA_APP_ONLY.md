# QA app-only bundle - busqueda global por trigramas

Fecha: 2026-05-12

Este paquete actualiza solo la imagen de la aplicacion `hhcc_app:latest` en el stack existente de QA. No restaura base de datos, no toca volumenes y no modifica el `docker-compose.yml`.

## Contenido

- `hhcc_app_latest.tar.gz`: imagen Docker de la aplicacion.
- `update_existing_qa_stack.sh`: script para cargar la imagen, recrear `app` + `nginx`, ejecutar migraciones y reconstruir el indice de busqueda global.

## Pasos para pasar a QA

1. Copiar `qa_app_only_bundle_busqueda_global_trigramas_20260512.tar.gz` al servidor de QA.

2. Descomprimir el paquete:

   ```bash
   tar -xzf qa_app_only_bundle_busqueda_global_trigramas_20260512.tar.gz
   cd qa_app_only_bundle_busqueda_global_trigramas_20260512
   ```

3. Ejecutar el update:

   ```bash
   chmod +x update_existing_qa_stack.sh
   ./update_existing_qa_stack.sh
   ```

4. Verificar en navegador:

   - `/`: debe mostrar el nuevo buscador global.
   - Buscar `quiel`: debe encontrar pacientes con Ezequiel y permitir paginar.
   - Buscar `231010`: debe encontrar el documento `23101065`.
   - Buscar `101`: debe paginar y permitir llegar a Bergonzi.
   - Buscar `ab`: debe mostrar el aviso de minimo 3 caracteres.
   - El link `leer doc de trigramas` debe abrir un PDF.

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
- La aplicacion ejecuta migraciones al iniciar. El script tambien ejecuta `python3 manage.py migrate --noinput` dentro del contenedor para dejar el estado explicito.
- El script ejecuta `python3 manage.py rebuild_global_search_index` dentro del contenedor. Este paso crea/rellena el indice materializado de trigramas.
