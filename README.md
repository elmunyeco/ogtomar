# Reorganización de CSS

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
