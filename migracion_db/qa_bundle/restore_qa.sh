#!/usr/bin/env bash
set -euo pipefail

DB_CONTAINER=${DB_CONTAINER:-nuevo_cardioprieto}
DB_USER=${DB_USER:-root}
DB_PASS=${DB_PASS:-Corbis5}
DB_NAME=${DB_NAME:-cardioprieto}

HERE="$(cd "$(dirname "$0")" && pwd)"

if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
  echo "ERROR: contenedor ${DB_CONTAINER} no esta corriendo" >&2
  exit 1
fi

# Drop + create

docker exec -i "$DB_CONTAINER" mariadb -u"$DB_USER" -p"$DB_PASS" -e "DROP DATABASE IF EXISTS ${DB_NAME}; CREATE DATABASE ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Schema + data + auth

docker exec -i "$DB_CONTAINER" mariadb -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$HERE/cardioprieto_schema.sql"
docker exec -i "$DB_CONTAINER" mariadb -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$HERE/cardioprieto_data.sql"
docker exec -i "$DB_CONTAINER" mariadb -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$HERE/auth_dump.sql"

echo "OK: restore completo en ${DB_CONTAINER}:${DB_NAME}"
