# Perfil profesional privado de QBI2

Cada instalación debe proporcionar un `profile.yaml` externo. El archivo no se
versiona: se toma `profile.example.yaml` como plantilla y su ruta puede cambiarse
con `QBI2_PROFILE_YAML_PATH`.

El YAML reúne los datos del médico, las matrículas, el sello, el consultorio y
las rutas de los activos que el servidor incorpora al payload de receta:

- `firma_omar.png`: firma rasterizada, PNG transparente, lienzo 300 × 300.
- `logo_omar.png`: marca profesional panorámica, PNG transparente, 640 × 190.

Las rutas relativas se resuelven desde el directorio del propio YAML. Los PNG
están excluidos por `.gitignore` y no deben publicarse mediante `static/`,
guardarse en logs ni incluirse en respuestas de diagnóstico sin redacción.
