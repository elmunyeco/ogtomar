#!/usr/bin/env bash
set -euo pipefail

STACK_DIR="/root/deploy"
APP_TAR="hhcc_app_latest.tar.gz"
APP_IMAGE="hhcc_app:latest"
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

echo "==> Logs recientes de app"
$COMPOSE logs --tail=50 app || true

echo "==> Logs recientes de nginx"
$COMPOSE logs --tail=20 nginx || true

echo "==> Health check local"
curl -I --max-time 10 http://127.0.0.1/ || true
curl -I --max-time 10 http://127.0.0.1/login/ || true

if docker image inspect "$BACKUP_TAG" >/dev/null 2>&1; then
  echo ""
  echo "Backup disponible para rollback: $BACKUP_TAG"
  echo "Rollback:"
  echo "  docker tag $BACKUP_TAG $APP_IMAGE"
  echo "  cd $STACK_DIR && $COMPOSE up -d --force-recreate app nginx"
fi
