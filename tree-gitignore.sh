#!/bin/bash
# Git tree - Muestra archivos de git como árbol

# Verificar que es repo git
[[ ! -d ".git" ]] && { echo "❌ No es repositorio git"; exit 1; }

# Obtener archivos y simular estructura tree
git ls-files | sort | awk -F/ '
{
    for(i=1; i<NF; i++) {
        path=""
        for(j=1; j<=i; j++) {
            path = path $j "/"
        }
        if(!(path in seen)) {
            seen[path] = 1
            indent = ""
            for(k=1; k<i; k++) indent = indent "│   "
            print indent "├── " $i "/"
        }
    }
    # Imprimir archivo
    indent = ""
    for(i=1; i<NF; i++) indent = indent "│   "
    print indent "├── " $NF
}'
