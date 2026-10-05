# Configuración privada de RCTA

La rama de producción no adopta el servidor de homologación por defecto. Cada
instalación debe definir explícitamente `QBI2_BASE_URL` y las credenciales que
correspondan al entorno. Si falta la URL, el cliente falla antes de intentar una
emisión.

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

La política del portal también vive en ese único YAML. El campo
`portal_pacientes.antiguedad_maxima_atencion_anios` define cuántos años pueden
transcurrir desde la última actividad clínica antes de impedir un nuevo pedido.

Las únicas pantallas públicas de este módulo son el ingreso y el pedido del
paciente bajo `/recetas/paciente/`. Para el médico, el menú expone solamente
`Gestión` y `Emisión`.
