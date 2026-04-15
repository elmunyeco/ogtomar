#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_SRC="/home/eze/omar"

cd "$APP_SRC"

echo "==> Building app image"
docker build -t hhcc_app:latest .

echo "==> Saving app image"
docker save hhcc_app:latest | gzip > "$SCRIPT_DIR/hhcc_app_latest.tar.gz"

echo "==> Saving db image"
docker save nuevo_cardioprieto:latest | gzip > "$SCRIPT_DIR/nuevo_cardioprieto_latest.tar.gz"

echo "==> Dumping database"
docker exec nuevo_cardioprieto mariadb-dump -uroot -p'Corbis5' --single-transaction --routines --triggers --events --databases cardioprieto > "$SCRIPT_DIR/cardioprieto_dump.sql"

echo "==> Done"
