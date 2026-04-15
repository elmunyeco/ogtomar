# Sistema de Ecocardiograma - Documentación Completa

## Descripción General

Este es un sistema moderno para la gestión de estudios de ecocardiograma desarrollado con Django, Alpine.js y Tailwind CSS. El sistema permite crear, editar y visualizar estudios de ecocardiograma con funcionalidades avanzadas como:

- Auto-guardado en tiempo real
- Visualización interactiva de segmentos cardíacos
- Cálculos automáticos de métricas
- Interfaz responsiva y moderna
- Generación de informes para impresión

## Arquitectura del Sistema

### Backend (Django)
- **Modelos**: Definición de estructuras de datos para pacientes, estudios y conclusiones
- **Vistas**: Lógica de negocio y endpoints AJAX
- **Validadores**: Validación de datos médicos y coherencia
- **Utilidades**: Funciones helper y cálculos automáticos

### Frontend
- **Alpine.js**: Reactividad y manejo de estado
- **Tailwind CSS**: Estilos y diseño responsivo
- **JavaScript nativo**: Componentes específicos como el manejo de segmentos

## Instalación y Configuración

### 1. Configuración de Archivos

#### Estructura de Directorios
```
ecocardiograma/
├── static/
│   └── ecocardiograma/
│       ├── css/
│       │   └── ecocardiograma-responsive.css
│       ├── js/
│       │   └── segmentos-cardiacos.js
│       └── images/
│           └── segmentos.png
├── templates/
│   └── ecocardiograma/
│       ├── eco_form_optimizado.html
│       ├── imprimir_estudio.html
│       └── partials/
│           ├── valor_con_unidad.html
│           ├── campo_calculado.html
│           └── [otros parciales]
├── templatetags/
│   ├── __init__.py
│   └── ecocardiograma_tags.py
├── models.py
├── views.py
├── urls.py
├── forms.py
├── config.py
├── validators.py
└── utils.py
```

### 2. Configuración de Django

#### settings.py
```python
INSTALLED_APPS = [
    # ... otras apps
    'ecocardiograma',
]

# Configuración de archivos estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Configuración de media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

#### URLs principales
```python
# cardioprieto/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('eco/', include('ecocardiograma.urls')),
    # ... otras URLs
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

### 3. Migraciones de Base de Datos

```bash
# Crear migraciones
python manage.py makemigrations ecocardiograma

# Aplicar migraciones
python manage.py migrate

# Crear superusuario (si es necesario)
python manage.py createsuperuser
```

### 4. Archivos Estáticos

Asegúrate de tener la imagen de segmentos cardíacos:
- Ubicación: `ecocardiograma/static/ecocardiograma/images/segmentos.png`
- La imagen debe contener las cuatro vistas del corazón con los 16 segmentos marcados

## Uso del Sistema

### 1. Creación de un Nuevo Estudio

1. **Acceso**: Navegar a `/eco/nuevo/{historia_id}/`
2. **Datos del Paciente**: Se cargan automáticamente desde la historia clínica
3. **Datos Físicos**: Ingresar peso, talla y presión arterial
4. **Auto-guardado**: Los cambios se guardan automáticamente cada 2 segundos

### 2. Análisis Bidimensional

- **Campos disponibles**: 12 mediciones ecocardiográficas
- **Cálculos automáticos**: 
  - BMI (peso/talla²)
  - Fracción de acortamiento
- **Validaciones**: Rangos normales para cada medición

### 3. Análisis Doppler

- **Velocidades**: Medición de velocidades en válvulas
- **Gradientes**: Cálculo automático usando la ecuación de Bernoulli (4V²)
- **Ondas E y A**: Para válvulas mitral y tricuspídea

### 4. Motilidad Segmentaria

#### Funcionalidades:
- **16 segmentos**: Basado en el modelo estándar de la AHA
- **Estados**: No evaluado, Normal, Hipoquinético, Aquinético, Disquinético
- **Visualización**: Coloreado en tiempo real sobre imagen del corazón
- **Interacción**: Click en segmentos para cambiar estado

#### Colores de Segmentos:
- **Blanco**: No evaluado
- **Amarillo**: Normal
- **Naranja**: Hipoquinético
- **Rojo**: Aquinético
- **Azul**: Disquinético

### 5. Conclusiones

#### Tipos de Conclusiones:
- **Selección múltiple**: Aurícula izquierda, Ventrículo izquierdo
- **Selección única**: Función sistólica, Función diastólica
- **Con comentarios**: Campos que permiten texto adicional

#### Conclusión B y Comentario Final:
- **Texto libre**: Hasta 1500 caracteres para Conclusión B
- **Comentario Final**: Hasta 700 caracteres
- **Contador**: Muestra caracteres restantes en tiempo real

### 6. Guardado e Impresión

- **Auto-guardado**: Automático cada 2 segundos
- **Guardado manual**: Botón "Guardar e Imprimir"
- **Impresión**: Abre nueva ventana con formato optimizado para impresión

## Componentes Técnicos

### 1. Sistema de Auto-guardado

```javascript
// Configuración del debounce
debouncedSave() {
    clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(() => {
        this.autoGuardar();
    }, 2000);
}
```

### 2. Manejo de Segmentos

```javascript
// Clase especializada para segmentos
const segmentos = new SegmentosCardiacos(
    containerRef, 
    canvasRef, 
    imagenRef
);

// Establecer estado de segmento
segmentos.establecerSegmento(numero, estado);

// Obtener todos los valores
const valores = segmentos.obtenerValores();
```

### 3. Validaciones del Backend

```python
from .validators import validar_coherencia_estudio

def guardar_estudio(datos):
    # Validar datos
    es_valido, errores = validar_datos_estudio(datos)
    if not es_valido:
        return JsonResponse({'success': False, 'errors': errores})
    
    # Procesar y guardar...
```

### 4. Cálculos Automáticos

```python
from .utils import calcular_metricas_estudio

# Calcular métricas derivadas
metricas = calcular_metricas_estudio(estudio)
# Retorna: BMI, fracción de acortamiento, gradientes, etc.
```

## Personalización

### 1. Colores de Segmentos

Modificar en `segmentos-cardiacos.js`:

```javascript
this.estados = {
    '0': { nombre: 'No evaluado', color: '#FFFFFF' },
    '1': { nombre: 'Normal', color: '#FFFF00' },
    // ... personalizar colores
};
```

### 2. Valores de Referencia

Modificar en `config.py`:

```python
VALORES_NORMALES = {
    'fraccion_eyeccion': {
        'normal': (55, 100),
        'levemente_reducida': (45, 54),
        # ... personalizar rangos
    }
}
```

### 3. Campos del Formulario

Agregar campos en `models.py` y actualizar:
- `forms.py`: Agregar al formulario
- `views.py`: Incluir en procesamiento
- `templates`: Agregar campo al HTML

### 4. Estilos Personalizados

Modificar variables CSS en `ecocardiograma-responsive.css`:

```css
:root {
    --primary-color: #3b82f6;  /* Cambiar color primario */
    --success-color: #10b981;  /* Cambiar color de éxito */
    /* ... otras variables */
}
```

## API y Endpoints

### Endpoints Principales

- `GET /eco/nuevo/{historia_id}/`: Formulario principal
- `POST /eco/guardar_todo_ajax/{historia_id}/`: Guardado AJAX
- `GET /eco/imprimir_estudio/{estudio_id}/`: Vista de impresión

### Formato de Datos AJAX

```json
{
    "historia_id": 123,
    "estudio": {
        "peso": 70.5,
        "talla": 1.75,
        "presion_sistolica": 120,
        // ... otros campos
    },
    "conclusiones": {
        "auricula_izq": "1,2",
        "funcion_sistolica": "1",
        // ... otros campos
    },
    "segmentos": {
        "1": "1",
        "2": "2",
        // ... 16 segmentos
    }
}
```

## Troubleshooting

### Problemas Comunes

1. **Error de CSRF**: Verificar que el token CSRF esté incluido
2. **Imagen de segmentos no aparece**: Verificar ruta de archivo estático
3. **Auto-guardado no funciona**: Revisar configuración de AJAX y URLs
4. **Cálculos incorrectos**: Validar datos de entrada y fórmulas

### Debug

```javascript
// Activar modo debug en Alpine.js
Alpine.start();
window.Alpine = Alpine;

// Ver estado actual
console.log(this.estudio);
console.log(this.segmentos);
```

### Logs del Servidor

```python
import logging
logger = logging.getLogger(__name__)

def mi_vista(request):
    logger.debug('Estado actual del estudio')
    # ... código
```

## Seguridad

### Validaciones Frontend
- Tipos de datos numéricos
- Rangos de valores médicos
- Límites de caracteres en textos

### Validaciones Backend
- Coherencia de datos médicos
- Rangos de valores normales
- Sanitización de entrada

### Permisos
- Autenticación requerida (`@login_required`)
- Validación de acceso a historias clínicas
- Protección CSRF en formularios AJAX

## Performance

### Optimizaciones Frontend
- Debounce en auto-guardado (2 segundos)
- Lazy loading de componentes pesados
- Cache de cálculos complejos

### Optimizaciones Backend
- Índices en base de datos
- Queries optimizadas
- Paginación cuando corresponde

## Mantenimiento

### Actualizaciones
1. **Base de datos**: Crear migraciones para cambios de modelo
2. **Frontend**: Actualizar versiones de Alpine.js y Tailwind
3. **Valores de referencia**: Revisar periodicamente en `config.py`

### Backup
- Backup regular de base de datos
- Backup de archivos estáticos (especialmente imágenes)
- Versionado de código en Git

### Monitoreo
- Logs de errores en producción
- Métricas de uso del sistema
- Performance de consultas de base de datos

## Contribución

### Estándares de Código
- Python: PEP 8
- JavaScript: ESLint con configuración estándar
- CSS: BEM methodology para clases personalizadas

### Testing
```bash
# Tests de Django
python manage.py test ecocardiograma

# Tests de JavaScript (si implementados)
npm test
```

### Documentación
- Documentar nuevas funcionalidades
- Actualizar este README para cambios importantes
- Comentarios en código para lógica compleja

---

## Contacto y Soporte

Para preguntas técnicas o reportes de bugs, contactar al equipo de desarrollo.

**Versión del Sistema**: 1.0.0
**Última Actualización**: Mayo 2025