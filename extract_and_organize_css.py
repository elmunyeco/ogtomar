#!/usr/bin/env python3
import os
import re
import subprocess
from pathlib import Path
import shutil

def process_html_files():
    print("=== Iniciando proceso de extracción y reorganización de CSS ===")
    
    # Directorio base para los templates refactorizados
    refactored_base = "refactored_templates"
    
    # Directorio base para los estilos CSS
    css_dir = "static/main/css"
    os.makedirs(css_dir, exist_ok=True)
    
    # Archivo de salida para el CSS
    output_css_file = os.path.join(css_dir, "style.css")
    
    # Obtener todos los archivos HTML
    find_command = "find hhcc/main/templates -name '*.html'"
    html_files = subprocess.check_output(find_command, shell=True).decode().strip().split('\n')
    
    # Eliminar archivos vacíos o inexistentes
    html_files = [f for f in html_files if f and os.path.exists(f)]
    
    # Primero, identifiquemos la plantilla base.html que contiene la estructura principal
    base_template = None
    for html_path in html_files:
        if os.path.basename(html_path) == "base.html":
            base_template = html_path
            break
    
    if not base_template:
        print("Advertencia: No se encontró un archivo base.html. La estructura de herencia podría no mantenerse correctamente.")
    
    # Regex para encontrar etiquetas style completas
    style_tag_pattern = re.compile(r'(<style[^>]*>.*?</style>)', re.DOTALL)
    
    # Regex para encontrar la etiqueta head
    head_pattern = re.compile(r'<head>(.*?)</head>', re.DOTALL)
    
    # Regex para encontrar patrones de extensión de Django
    extends_pattern = re.compile(r'{%\s*extends\s+[\'"](.+?)[\'"]\s*%}')
    
    # Regex para encontrar bloques de contenido
    block_pattern = re.compile(r'{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}', re.DOTALL)
    
    processed_files = []
    template_hierarchy = {}
    
    # Primer paso: Extraer todos los estilos CSS
    print("Fase 1: Extrayendo estilos CSS...")
    with open(output_css_file, 'w', encoding='utf-8') as css_file:
        css_file.write("/* Archivo CSS centralizado generado automáticamente */\n\n")
        
        for html_path in html_files:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraer todas las etiquetas style completas
            style_tags = style_tag_pattern.findall(content)
            
            if style_tags:
                css_file.write(f"/* ===== Estilos extraídos de {html_path} ===== */\n")
                
                for style_tag in style_tags:
                    # Extraer el contenido CSS de la etiqueta
                    css_content = re.search(r'<style[^>]*>(.*?)</style>', style_tag, re.DOTALL).group(1)
                    css_file.write(f"{css_content.strip()}\n\n")
                
                processed_files.append(html_path)
    
    print(f"Estilos extraídos de {len(processed_files)} archivos y guardados en {output_css_file}")
    
    # Segundo paso: Analizar la jerarquía de plantillas
    print("Fase 2: Analizando la estructura de herencia de plantillas...")
    for html_path in html_files:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar si esta plantilla extiende otra
        extends_match = extends_pattern.search(content)
        if extends_match:
            parent_template = extends_match.group(1)
            template_hierarchy[html_path] = parent_template
    
    # Tercer paso: Reorganizar los templates refactorizados
    print("Fase 3: Reorganizando y modificando plantillas...")
    for html_path in html_files:
        relative_path = html_path.split("templates/")[-1]
        refactored_path = os.path.join(refactored_base, relative_path)
        
        # Crear directorio de destino si no existe
        os.makedirs(os.path.dirname(refactored_path), exist_ok=True)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Eliminar todas las etiquetas style
        modified_content = style_tag_pattern.sub('', content)
        
        # Verificar si tiene encabezado <head>
        head_match = head_pattern.search(modified_content)
        
        if head_match:
            head_content = head_match.group(1)
            
            # Agregar {% load static %} si no existe
            if "{% load static %}" not in head_content:
                static_tag = "{% load static %}\n    "
                new_head = static_tag + head_content
            else:
                new_head = head_content
            
            # Agregar el enlace al CSS centralizado si no existe
            css_link = '<link rel="stylesheet" href="{% static \'css/style.css\' %}">'
            if css_link not in new_head:
                new_head += f"\n    <!-- Enlace al CSS centralizado -->\n    {css_link}"
            
            # Reemplazar el contenido del head
            modified_content = modified_content.replace(head_match.group(1), new_head)
        
        # Guardar el archivo modificado
        with open(refactored_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
    
    # Cuarto paso: Crear un archivo de configuración para TailwindCSS si es necesario
    print("Fase 4: Configurando TailwindCSS...")
    tailwind_config = """module.exports = {
  content: [
    './hhcc/main/templates/**/*.html',
    './static/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        'brand-primary': '#9a4035',
        'brand-secondary': '#7a332b',
      },
    },
  },
  plugins: [],
}
"""
    with open("tailwind.config.js", 'w', encoding='utf-8') as f:
        f.write(tailwind_config)
    
    # Quinto paso: Crear un script de ayuda para actualizar todos los templates
    update_script = """#!/bin/bash
# Script para actualizar todos los templates

# Copiar los templates refactorizados
echo "Copiando templates refactorizados..."
cp -r refactored_templates/* hhcc/main/templates/

# Asegurarse de que el directorio static/css existe
mkdir -p hhcc/main/static/css

# Copiar el archivo CSS centralizado
echo "Copiando archivo CSS centralizado..."
cp static/css/style.css hhcc/main/static/css/

echo "¡Actualización completada!"
"""
    with open("update_templates.sh", 'w', encoding='utf-8') as f:
        f.write(update_script)
    
    os.chmod("update_templates.sh", 0o755)  # Hacer el script ejecutable
    
    # Sexto paso: Crear un README con instrucciones
    readme = """# Reorganización de CSS

Este directorio contiene los templates refactorizados con CSS centralizado.

## Estructura

- `refactored_templates/`: Contiene todos los templates HTML con los estilos extraídos
- `static/css/style.css`: Contiene todos los estilos CSS centralizados
- `update_templates.sh`: Script para actualizar los templates en el proyecto

## Instrucciones para aplicar los cambios

1. Revisa los templates refactorizados para asegurarte de que todo está correcto
2. Ejecuta el script de actualización:
   ```
   ./update_templates.sh
   ```
3. Reinicia tu servidor Django
4. Verifica que todo funcione correctamente

## Solución de problemas

Si alguna página no se ve correctamente, sigue estos pasos:

1. Verifica que la página incluye la etiqueta `{% load static %}` en el encabezado
2. Asegúrate de que el enlace al CSS está presente: `<link rel="stylesheet" href="{% static 'css/style.css' %}">`
3. Confirma que la estructura de herencia de plantillas se mantiene correctamente
"""
    with open("README.md", 'w', encoding='utf-8') as f:
        f.write(readme)
    
    # Información final
    print("\n=== Proceso completado con éxito ===")
    print(f"- Estilos extraídos: {len(processed_files)} archivos")
    print(f"- CSS centralizado: {output_css_file}")
    print(f"- Templates refactorizados: {refactored_base}/")
    print("\nPara aplicar los cambios, revisa los archivos y luego ejecuta: ./update_templates.sh")

if __name__ == "__main__":
    process_html_files()
