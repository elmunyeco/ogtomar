find . -path "*/migrations/*.py"
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
find . -name "*.pyc" -delete
find . -name "*__pycache__" -delete
