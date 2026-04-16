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

echo "==> Waiting for database readiness"
docker-compose exec -T db /bin/sh -lc '
  until mariadb-admin --protocol=tcp -h127.0.0.1 -P3306 -uroot -pCorbis5 ping --silent; do
    sleep 1
  done
'

if [ -f "$SCRIPT_DIR/cardioprieto_dump.sql" ]; then
  echo "==> Restoring database from cardioprieto_dump.sql"
  docker-compose exec -T db /bin/sh -lc "mariadb --protocol=tcp -h127.0.0.1 -P3306 -uroot -pCorbis5 -e \"CREATE DATABASE IF NOT EXISTS cardioprieto;\""
  docker-compose exec -T db /bin/sh -lc "mariadb --protocol=tcp -h127.0.0.1 -P3306 -uroot -pCorbis5 cardioprieto" < "$SCRIPT_DIR/cardioprieto_dump.sql"
  echo "==> Starting app/nginx without startup migrations"
  RUN_MIGRATIONS_ON_STARTUP=0 docker-compose up -d app nginx
else
  echo "==> No dump found, skipping restore"
  echo "==> Starting app/nginx with normal startup migrations"
  docker-compose up -d app nginx
fi

echo "==> Verifying env"
docker exec hhcc_app env | grep ^DB_ || true

echo "==> Waiting for app readiness"
for _ in $(seq 1 60); do
  if curl -fsS http://127.0.0.1/login/ >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "==> Recent app logs"
docker logs --tail 40 hhcc_app || true

echo "==> Recent db logs"
docker logs --tail 40 nuevo_cardioprieto || true

echo "==> Done"
