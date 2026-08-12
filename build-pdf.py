#!/usr/bin/env python3
"""build-pdf.py
Genera API_ENTITIES.pdf a partir de API_ENTITIES.md con estilo de
informe tecnico mecanografiado.

Inserta el .md dentro de un <pre> (preserva la alineacion ASCII de
diagramas y tablas) y aplica estilo-informe.css. Render con WeasyPrint.

Uso:
    python3 build-pdf.py [entrada.md] [salida.pdf] [estilo.css]
"""
import html
import pathlib
import sys

from weasyprint import HTML

md_path  = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "PLAN_INTEGRACION_QBI2_HISTORIAS.md")
pdf_path = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "PLAN_INTEGRACION_QBI2_HISTORIAS.pdf")
css_path = pathlib.Path(sys.argv[3] if len(sys.argv) > 3 else "estilo-informe.css")

body = html.escape(md_path.read_text(encoding="utf-8"))
css  = css_path.read_text(encoding="utf-8")

doc = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><style>{css}</style></head>
<body><pre>{body}</pre></body></html>"""

HTML(string=doc).write_pdf(str(pdf_path))
print(f"PDF generado: {pdf_path}")
