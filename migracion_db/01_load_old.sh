#!/usr/bin/env bash
set -euo pipefail

DUMP="${1:-cardioprieto_old.sql}"
DB_OLD="${2:-cardioprieto_old}"

mariadb -h 127.0.0.1 -P 3307 -uroot -pCorbis5 -e "DROP DATABASE IF EXISTS ${DB_OLD}; CREATE DATABASE ${DB_OLD};"

mariadb -h 127.0.0.1 -P 3307 -uroot -pCorbis5 ${DB_OLD} < "$DUMP"

echo "Cargado $DUMP en ${DB_OLD} (3307)"
