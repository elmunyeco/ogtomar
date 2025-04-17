#!/bin/bash
# Script para actualizar todos los templates

# Asegurarse de que el directorio static/css existe
mkdir -p hhcc/main/templates

# Copiar los templates refactorizados
echo "Copiando templates refactorizados..."
cp -r refactored_templates/* hhcc/main/templates/

# Asegurarse de que el directorio static/css existe
mkdir -p hhcc/main/static/css

# Copiar el archivo CSS centralizado
echo "Copiando archivo CSS centralizado..."
cp static/css/style.css hhcc/main/static/css/

echo "¡Actualización completada!"
