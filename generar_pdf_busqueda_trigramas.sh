#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MD_FILE="$BASE_DIR/BUSQUEDA_IDENTIFICATORIA_TRIGRAMAS.md"
CSS_FILE="$BASE_DIR/BUSQUEDA_IDENTIFICATORIA_TRIGRAMAS_PDF.css"
HTML_FILE="$(mktemp --suffix=.html)"
PDF_FILE="$BASE_DIR/BUSQUEDA_IDENTIFICATORIA_TRIGRAMAS.pdf"

cleanup() {
  rm -f "$HTML_FILE"
}
trap cleanup EXIT

if ! command -v pandoc >/dev/null 2>&1; then
  echo "Falta pandoc. Instalar pandoc para generar el HTML intermedio." >&2
  exit 1
fi

if ! command -v weasyprint >/dev/null 2>&1; then
  echo "Falta weasyprint. Instalar weasyprint para generar el PDF." >&2
  exit 1
fi

if [ ! -f "$MD_FILE" ]; then
  echo "No existe $MD_FILE" >&2
  exit 1
fi

if [ ! -f "$CSS_FILE" ]; then
  echo "No existe $CSS_FILE" >&2
  exit 1
fi

pandoc "$MD_FILE" \
  --standalone \
  --metadata lang=es \
  --css "$CSS_FILE" \
  --output "$HTML_FILE"

weasyprint "$HTML_FILE" "$PDF_FILE"

echo "PDF generado: $PDF_FILE"
