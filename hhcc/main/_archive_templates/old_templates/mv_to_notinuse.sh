for file in \
    ./detalle_historia_t.html \
    ./detalle_historia_t.back \
    ./detalle_historia_t2.html \
    ./detalle_historia_t3.html \
    ./detalle_historia_t4.html \
    ./detalle_bueno.html \
    ./detalle_historia_mock.html \
    ./historia-clinica-combined.html \
    ./historia-clinica-final.html \
    ./test_ultimo_comentario_indicaciones.html \
    ./simple_dropdown_menu.html \
    ./paciente-editar.html \
    ./paciente-borrar.html \
    ./cargar_paciente.html \
    ./indicaciones.html
do
    if [ -f "$file" ]; then
        mv "$file" "${file}.notinuse"
        echo "Renombrado: $file -> ${file}.notinuse"
    else
        echo "Archivo no encontrado: $file"
    fi
done
