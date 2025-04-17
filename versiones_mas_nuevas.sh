#!/bin/bash
# Script para comparar archivos entre dos ramas e indicar cuál es más reciente

RAMA_A=$1
RAMA_B=$2

# Obtener lista de archivos diferentes
ARCHIVOS_DIFERENTES=$(git diff --name-only $RAMA_A $RAMA_B)

for archivo in $ARCHIVOS_DIFERENTES; do
  # Obtener la fecha del último commit para cada archivo en cada rama
  FECHA_A=$(git log -1 --format="%at" $RAMA_A -- $archivo 2>/dev/null)
  FECHA_B=$(git log -1 --format="%at" $RAMA_B -- $archivo 2>/dev/null)
  
  if [ -z "$FECHA_A" ]; then
    echo "$archivo --> más nuevo de la rama $RAMA_B"
  elif [ -z "$FECHA_B" ]; then
    echo "$archivo --> más nuevo de la rama $RAMA_A"
  elif [ -z "$(git diff $RAMA_A $RAMA_B -- $archivo)" ]; then
    echo "$archivo --> versión idéntica en ambas ramas"
  elif [ $FECHA_A -gt $FECHA_B ]; then
    echo "$archivo --> más nuevo de la rama $RAMA_A"
  else
    echo "$archivo --> más nuevo de la rama $RAMA_B"
  fi

done
