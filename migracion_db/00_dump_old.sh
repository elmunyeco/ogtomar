#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-cardioprieto_old.sql}"

mariadb-dump \
  -h 127.0.0.1 -P 3308 -uroot -pCorbis5 \
  --skip-lock-tables --skip-triggers \
  cardioprieto > "$OUT"

echo "Dump generado: $OUT"
