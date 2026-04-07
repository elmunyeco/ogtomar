#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Stopping and cleaning containers"
docker-compose down || true

docker rm -f hhcc_app hhcc_nginx nuevo_cardioprieto >/dev/null 2>&1 || true

docker rmi -f hhcc_app:latest >/dev/null 2>&1 || true

docker rmi -f nuevo_cardioprieto:latest >/dev/null 2>&1 || true


echo "==> Loading images"
docker load -i hhcc_app_latest.tar.gz

docker load -i nuevo_cardioprieto_latest.tar.gz


echo "==> Starting stack"
docker-compose up -d db

if [ -f "$SCRIPT_DIR/cardioprieto_dump.sql" ]; then
  echo "==> Restoring database from cardioprieto_dump.sql"
  docker-compose exec -T db /bin/sh -lc "mariadb -uroot -pCorbis5 -e \"CREATE DATABASE IF NOT EXISTS cardioprieto;\""
  docker-compose exec -T db /bin/sh -lc "mariadb -uroot -pCorbis5 cardioprieto" < "$SCRIPT_DIR/cardioprieto_dump.sql"
else
  echo "==> No dump found, skipping restore"
fi

docker-compose up -d app nginx

echo "==> Verifying env"
docker exec -it hhcc_app env | grep ^DB_ || true

echo "==> Done"
