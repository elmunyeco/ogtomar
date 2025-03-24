# Estructura de directorios principal (sin carpetas __pycache__, migrations, env)
find . -type d -not -path "*/\.*" -not -path "*/__pycache__*" -not -path "*/venv*" -not -path "*/migrations*"

# Archivos Python principales
find . -name "*.py" -not -path "*/venv/*" -not -path "*/__pycache__/*" -not -path "*/migrations/*"

# Archivos de configuración importantes
find . -name "settings.py" -o -name "urls.py" -o -name "wsgi.py" -o -name "asgi.py"

# Listado de apps instaladas (buscar en settings.py)
grep "INSTALLED_APPS" */settings.py

# Modelos definidos
find . -name "models.py" -exec echo "=== {} ===" \; -exec cat {} \;

# Formularios definidos
find . -name "forms.py" -exec echo "=== {} ===" \; -exec cat {} \;
