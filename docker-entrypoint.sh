#!/bin/bash
set -euo pipefail

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-3306}"
DB_NAME="${DB_NAME:-cardioprieto}"
RUN_MIGRATIONS_ON_STARTUP="${RUN_MIGRATIONS_ON_STARTUP:-1}"

/app/wait-for-mysql.sh "$DB_HOST" "$DB_PORT" echo "Base de datos lista"

if ! mariadb -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME};" >/dev/null 2>&1; then
  echo "WARN: no se pudo crear/verificar la base de datos"
fi

if [ "$RUN_MIGRATIONS_ON_STARTUP" != "0" ]; then
  if ! python3 manage.py migrate --noinput; then
    echo "WARN: migrate failed, retrying with --fake-initial"
    python3 manage.py migrate --noinput --fake-initial || true
  fi
else
  echo "INFO: skipping migrations because RUN_MIGRATIONS_ON_STARTUP=0"
fi

exec python3 manage.py runserver 0.0.0.0:8000
