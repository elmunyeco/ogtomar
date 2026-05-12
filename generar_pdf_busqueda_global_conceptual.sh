#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MD_FILE="$BASE_DIR/BUSQUEDA_GLOBAL_TRIGRAMAS_CONCEPTUAL.md"
CSS_FILE="$BASE_DIR/BUSQUEDA_GLOBAL_TRIGRAMAS_CONCEPTUAL_PDF.css"
HTML_FILE="$(mktemp --suffix=.html)"
PDF_FILE="$BASE_DIR/BUSQUEDA_GLOBAL_TRIGRAMAS_CONCEPTUAL.pdf"

cleanup() {
  rm -f "$HTML_FILE"
}
trap cleanup EXIT

if ! command -v pandoc >/dev/null 2>&1; then
  echo "Falta pandoc." >&2
  exit 1
fi

if ! command -v weasyprint >/dev/null 2>&1; then
  echo "Falta weasyprint." >&2
  exit 1
fi

pandoc "$MD_FILE" \
  --standalone \
  --metadata lang=es \
  --css "$CSS_FILE" \
  --output "$HTML_FILE"

weasyprint "$HTML_FILE" "$PDF_FILE"

echo "PDF generado: $PDF_FILE"
