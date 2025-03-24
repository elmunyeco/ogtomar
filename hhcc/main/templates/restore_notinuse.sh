for file in ./*.notinuse; do
    if [ -f "$file" ]; then
        original="${file%.notinuse}"
        mv "$file" "$original"
        echo "Restaurado: $file -> $original"
    fi
done
