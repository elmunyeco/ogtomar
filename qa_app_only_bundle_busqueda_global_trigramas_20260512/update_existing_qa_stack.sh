#!/usr/bin/env bash
set -euo pipefail

STACK_DIR="/root/deploy"
APP_TAR="hhcc_app_latest.tar.gz"
APP_IMAGE="hhcc_app:latest"
APP_CONTAINER="hhcc_app"
BACKUP_TAG="hhcc_app:qa_backup_$(date +%Y%m%d_%H%M%S)"

if [ ! -f "$APP_TAR" ]; then
  echo "Falta $APP_TAR en $(pwd)" >&2
  exit 1
fi

if [ ! -f "$STACK_DIR/docker-compose.yml" ]; then
  echo "No existe $STACK_DIR/docker-compose.yml" >&2
  exit 1
fi

if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  COMPOSE="docker compose"
fi

echo "==> Validando tar de imagen"
gzip -t "$APP_TAR"

if docker image inspect "$APP_IMAGE" >/dev/null 2>&1; then
  echo "==> Guardando backup local de imagen actual: $BACKUP_TAG"
  docker tag "$APP_IMAGE" "$BACKUP_TAG"
else
  echo "==> No existe $APP_IMAGE previa; se continua sin backup de imagen"
fi

echo "==> Cargando nueva imagen de app"
docker load -i "$APP_TAR"

echo "==> Recreando app y nginx sobre el stack existente de QA"
cd "$STACK_DIR"
$COMPOSE up -d --force-recreate app nginx

echo "==> Esperando app"
for i in $(seq 1 60); do
  if docker exec "$APP_CONTAINER" python3 manage.py check >/dev/null 2>&1; then
    break
  fi
  sleep 2
  if [ "$i" -eq 60 ]; then
    echo "La app no respondio a manage.py check dentro del tiempo esperado" >&2
    $COMPOSE logs --tail=80 app || true
    exit 1
  fi
done

echo "==> Ejecutando migraciones"
docker exec "$APP_CONTAINER" python3 manage.py migrate --noinput

echo "==> Reconstruyendo indice global de busqueda"
docker exec "$APP_CONTAINER" python3 manage.py rebuild_global_search_index

echo "==> Logs recientes de app"
$COMPOSE logs --tail=50 app || true

echo "==> Logs recientes de nginx"
$COMPOSE logs --tail=20 nginx || true

echo "==> Health check local"
curl -I --max-time 10 http://127.0.0.1/ || true
curl -I --max-time 10 http://127.0.0.1/login/ || true
curl -I --max-time 10 http://127.0.0.1/docs/busqueda-trigramas/ || true

if docker image inspect "$BACKUP_TAG" >/dev/null 2>&1; then
  echo ""
  echo "Backup disponible para rollback: $BACKUP_TAG"
  echo "Rollback:"
  echo "  docker tag $BACKUP_TAG $APP_IMAGE"
  echo "  cd $STACK_DIR && $COMPOSE up -d --force-recreate app nginx"
fi
