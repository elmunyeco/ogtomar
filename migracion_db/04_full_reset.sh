#!/usr/bin/env bash
set -euo pipefail

DB_HOST=${DB_HOST:-127.0.0.1}
DB_PORT=${DB_PORT:-3307}
DB_USER=${DB_USER:-root}
DB_PASS=${DB_PASS:-Corbis5}
DB_OLD=${DB_OLD:-cardioprieto_old}
DB_NEW=${DB_NEW:-cardioprieto}

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCHEMA_FILE="$ROOT_DIR/new_schema.sql"
MIGR_02="$ROOT_DIR/02_migrar.sql"
MIGR_03="$ROOT_DIR/03_migrar_pendientes.sql"
MANAGE_PY="$ROOT_DIR/../hhcc/manage.py"
APP_DIR="$(cd "$ROOT_DIR/../hhcc" && pwd)"

APP_USER_1="${APP_USER_1:-eze}"
APP_PASS_1="${APP_PASS_1:-Furosemida}"
APP_USER_2="${APP_USER_2:-omar}"
APP_PASS_2="${APP_PASS_2:-Corbis5}"

mariadb_cmd=(mariadb -h "$DB_HOST" -P "$DB_PORT" -u"$DB_USER" -p"$DB_PASS")

if ! command -v mariadb >/dev/null 2>&1; then
  echo "ERROR: mariadb client no encontrado en PATH" >&2
  exit 1
fi

if [[ ! -f "$SCHEMA_FILE" ]]; then
  echo "ERROR: no existe $SCHEMA_FILE" >&2
  exit 1
fi

if [[ ! -f "$MIGR_02" || ! -f "$MIGR_03" ]]; then
  echo "ERROR: faltan scripts de migracion (02/03)" >&2
  exit 1
fi

if [[ ! -f "$MANAGE_PY" ]]; then
  echo "ERROR: no existe $MANAGE_PY" >&2
  exit 1
fi

# Verificar DB old
OLD_EXISTS="$(${mariadb_cmd[@]} -N -e "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME='${DB_OLD}';")"
if [[ -z "$OLD_EXISTS" ]]; then
  echo "ERROR: no existe ${DB_OLD}. Ejecuta 00_dump_old.sh + 01_load_old.sh" >&2
  exit 1
fi

# Drop/create DB new
${mariadb_cmd[@]} -e "DROP DATABASE IF EXISTS ${DB_NEW}; CREATE DATABASE ${DB_NEW} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Cargar esquema limpio
${mariadb_cmd[@]} ${DB_NEW} < "$SCHEMA_FILE"

# Migrar datos
${mariadb_cmd[@]} < "$MIGR_02"
${mariadb_cmd[@]} < "$MIGR_03"

# Reponer usuarios operativos del sistema nuevo
(
  cd "$APP_DIR"
  DB_ENGINE=django.db.backends.mysql \
  DB_NAME="$DB_NEW" \
  DB_HOST="$DB_HOST" \
  DB_PORT="$DB_PORT" \
  DB_USER="$DB_USER" \
  DB_PASSWORD="$DB_PASS" \
  python3 manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
users = [
    ('${APP_USER_1}', '${APP_PASS_1}'),
    ('${APP_USER_2}', '${APP_PASS_2}'),
]
for username, password in users:
    user, _ = User.objects.get_or_create(username=username)
    user.is_active = True
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
print('OK: usuarios operativos recreados')
"
)

echo "OK: ${DB_NEW} recreada y migrada desde ${DB_OLD}"
