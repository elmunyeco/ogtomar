# 🏥 INTEGRACIÓN ECOCARDIOGRAMA EN PROYECTO HHCC

## 📁 ESTRUCTURA ACTUAL DETECTADA

```
hhcc/                                    # ✅ Proyecto Django principal
├── hhcc/                               # ✅ Configuración del proyecto
│   ├── settings.py                     # ✅ Configuración principal
│   ├── urls.py                         # ✅ URLs principales
│   └── wsgi.py
├── main/                               # ✅ App principal existente
│   ├── models.py                       # ✅ Modelos de pacientes, historias
│   ├── views.py                        # ✅ Vistas principales
│   ├── templates/                      # ✅ Templates base existentes
│   │   ├── base.html                   # ✅ Template base a reutilizar
│   │   └── components/
│   │       └── header.html             # ✅ Header existente
│   └── static/main/                    # ✅ Archivos estáticos
│       ├── css/style.css               # ✅ CSS principal
│       ├── images/logo.png             # ✅ Logo existente
│       └── js/components/header.js     # ✅ JS existente
└── manage.py                           # ✅ Comando Django
```

---

## 🚀 PLAN DE INTEGRACIÓN

### **Opción Recomendada: Nueva App `ecocardiograma`**

Crear `ecocardiograma` como app separada pero integrada con `main`.

---

## 📂 UBICACIÓN EXACTA DE ARCHIVOS

### **1. CREAR NUEVA APP ECOCARDIOGRAMA**

```bash
cd hhcc
python manage.py startapp ecocardiograma
```

### **2. ESTRUCTURA DE ARCHIVOS A CREAR**

```
hhcc/
├── ecocardiograma/                      # 🆕 Nueva app
│   ├── __init__.py                      # ✅ Creado por startapp
│   ├── admin.py                         # ✅ Creado por startapp
│   ├── apps.py                          # ✅ Creado por startapp
│   ├── models.py                        # ✏️ REEMPLAZAR con nuestros modelos
│   ├── views.py                         # ✏️ REEMPLAZAR con nuestras vistas
│   ├── urls.py                          # 🆕 CREAR
│   ├── forms.py                         # 🆕 CREAR
│   ├── config.py                        # 🆕 CREAR
│   ├── validators.py                    # 🆕 CREAR
│   ├── utils.py                         # 🆕 CREAR
│   ├── migrations/                      # ✅ Creado por startapp
│   │   └── __init__.py
│   ├── templatetags/                    # 🆕 CREAR DIRECTORIO
│   │   ├── __init__.py                  # 🆕 CREAR
│   │   └── ecocardiograma_tags.py       # 🆕 CREAR
│   ├── templates/                       # 🆕 CREAR DIRECTORIO
│   │   └── ecocardiograma/              # 🆕 CREAR DIRECTORIO
│   │       ├── eco_form_optimizado.html # 🆕 CREAR
│   │       ├── imprimir_estudio.html    # 🆕 CREAR
│   │       └── partials/                # 🆕 CREAR DIRECTORIO
│   │           ├── valor_con_unidad.html
│   │           ├── campo_calculado.html
│   │           └── [otros 8 parciales]
│   └── static/                          # 🆕 CREAR DIRECTORIO
│       └── ecocardiograma/              # 🆕 CREAR DIRECTORIO
│           ├── css/                     # 🆕 CREAR DIRECTORIO
│           │   └── ecocardiograma-responsive.css
│           ├── js/                      # 🆕 CREAR DIRECTORIO
│           │   └── segmentos-cardiacos.js
│           └── images/                  # 🆕 CREAR DIRECTORIO
│               └── segmentos.png        # 🆕 AGREGAR IMAGEN
```

---

## ⚙️ ARCHIVOS A MODIFICAR

### **1. hhcc/hhcc/settings.py**

```python
# UBICACIÓN: hhcc/hhcc/settings.py
# MODIFICAR: Agregar ecocardiograma a INSTALLED_APPS

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',                    # ✅ App principal existente
    'ecocardiograma',          # 🆕 AGREGAR ESTA LÍNEA
]
```

### **2. hhcc/hhcc/urls.py**

```python
# UBICACIÓN: hhcc/hhcc/urls.py
# MODIFICAR: Agregar include para ecocardiograma

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),           # ✅ URLs principales existentes
    path('ecocardiograma/', include('ecocardiograma.urls')),  # 🆕 AGREGAR ESTA LÍNEA
]
```

### **3. hhcc/main/templates/base.html**

```html
<!-- UBICACIÓN: hhcc/main/templates/base.html -->
<!-- MODIFICAR: Agregar CSS de ecocardiograma en el head -->

{% load static %}
<!DOCTYPE html>
<html lang="es">
<head>
    <!-- ... head existente ... -->
    
    <!-- CSS existente -->
    <link rel="stylesheet" href="{% static 'main/css/style.css' %}">
    
    <!-- 🆕 AGREGAR: CSS específico de ecocardiograma -->
    {% block extra_css %}{% endblock %}
    
    <!-- Alpine.js para ecocardiograma -->
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <!-- ... body existente ... -->
    
    <!-- JS existente -->
    <script src="{% static 'main/js/components/header.js' %}"></script>
    
    <!-- 🆕 AGREGAR: JS específico de cada página -->
    {% block extra_js %}{% endblock %}
</body>
</html>
```

---

## 🆕 ARCHIVOS NUEVOS A CREAR

### **hhcc/ecocardiograma/urls.py**
```python
# UBICACIÓN: hhcc/ecocardiograma/urls.py
# CREAR NUEVO ARCHIVO

from django.urls import path
from . import views

app_name = 'ecocardiograma'

urlpatterns = [
    # Vista principal
    path('nuevo/<int:historia_id>/', views.nuevo_estudio, name='nuevo_estudio'),
    
    # Vista AJAX para guardado
    path('guardar_todo_ajax/<int:historia_id>/', views.guardar_todo_ajax, name='guardar_todo_ajax'),
    
    # Vista de impresión
    path('imprimir_estudio/<int:estudio_id>/', views.imprimir_estudio, name='imprimir_estudio'),
]
```

### **hhcc/ecocardiograma/models.py**
```python
# UBICACIÓN: hhcc/ecocardiograma/models.py
# REEMPLAZAR CONTENIDO COMPLETO

from django.db import models
from django.utils import timezone
from main.models import HistoriaClinica  # 🔗 Importar de la app main

class EstudioEcocardiograma(models.Model):
    # Relación con historia clínica de la app main
    historia = models.ForeignKey(HistoriaClinica, on_delete=models.CASCADE)
    fecha = models.DateField(default=timezone.now)
    
    # Datos físicos básicos
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    talla = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    presion_sistolica = models.IntegerField(null=True, blank=True)
    presion_diastolica = models.IntegerField(null=True, blank=True)
    
    # [resto del modelo como en el artifact anterior]
    
    def __str__(self):
        return f"Ecocardiograma {self.id} - {self.historia.paciente}"

# [resto de modelos: SegmentoEcocardiograma, ConclusiónEcocardiograma]
```

### **Estructura de Directorios a Crear**
```bash
# EJECUTAR ESTOS COMANDOS EN hhcc/

# Crear directorios de templates
mkdir -p ecocardiograma/templates/ecocardiograma/partials

# Crear directorios de static files
mkdir -p ecocardiograma/static/ecocardiograma/css
mkdir -p ecocardiograma/static/ecocardiograma/js
mkdir -p ecocardiograma/static/ecocardiograma/images

# Crear directorio de templatetags
mkdir -p ecocardiograma/templatetags

# Crear archivos __init__.py necesarios
touch ecocardiograma/templatetags/__init__.py
```

---

## 🔗 INTEGRACIÓN CON SISTEMA EXISTENTE

### **1. Modelo de Relación**
```python
# El ecocardiograma se relaciona con HistoriaClinica existente
historia = models.ForeignKey('main.HistoriaClinica', on_delete=models.CASCADE)
```

### **2. URLs en el Header**
```html
<!-- UBICACIÓN: hhcc/main/templates/components/header.html -->
<!-- AGREGAR en el menú de navegación -->

<li class="menu-item">
    <a href="{% url 'ecocardiograma:nuevo_estudio' historia.id %}" class="menu-link">
        Ecocardiograma
    </a>
</li>
```

### **3. Template Base**
```html
<!-- UBICACIÓN: hhcc/ecocardiograma/templates/ecocardiograma/eco_form_optimizado.html -->
<!-- PRIMERA LÍNEA del template -->

{% extends 'base.html' %}  {# 🔗 Extiende el base.html de main #}
{% load static %}
{% load ecocardiograma_tags %}

{% block title %}Sistema de Ecocardiograma{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'ecocardiograma/css/ecocardiograma-responsive.css' %}">
{% endblock %}

<!-- ... resto del contenido ... -->

{% block extra_js %}
<script src="{% static 'ecocardiograma/js/segmentos-cardiacos.js' %}"></script>
<!-- Script de Alpine.js como en el artifact anterior -->
{% endblock %}
```

---

## 🚀 COMANDOS DE INSTALACIÓN

### **1. Crear la App**
```bash
cd hhcc
python manage.py startapp ecocardiograma
```

### **2. Crear Estructura de Directorios**
```bash
# Desde hhcc/
mkdir -p ecocardiograma/templates/ecocardiograma/partials
mkdir -p ecocardiograma/static/ecocardiograma/{css,js,images}
mkdir -p ecocardiograma/templatetags
touch ecocardiograma/templatetags/__init__.py
```

### **3. Copiar Archivos**
```bash
# Copiar todos los archivos de los artifacts a sus ubicaciones respectivas
# Ejemplo:
# - eco_form_optimizado.html → hhcc/ecocardiograma/templates/ecocardiograma/
# - ecocardiograma-responsive.css → hhcc/ecocardiograma/static/ecocardiograma/css/
# - segmentos-cardiacos.js → hhcc/ecocardiograma/static/ecocardiograma/js/
```

### **4. Aplicar Migraciones**
```bash
cd hhcc
python manage.py makemigrations ecocardiograma
python manage.py migrate
```

### **5. Probar el Sistema**
```bash
cd hhcc
python manage.py runserver
# Navegar a: http://localhost:8000/ecocardiograma/nuevo/1/
```

---

## 🎯 PUNTOS DE INTEGRACIÓN CLAVE

### **1. Reutilización de Pacientes**
- ✅ **Usa `main.models.HistoriaClinica`** existente
- ✅ **Se integra con el sistema de pacientes** actual
- ✅ **Mantiene la estructura de navegación** existente

### **2. Templates Coherentes**
- ✅ **Extiende `base.html`** de main
- ✅ **Usa el header existente** con navegación
- ✅ **Mantiene el look & feel** del sistema

### **3. Static Files Organizados**
- ✅ **CSS específico** en `ecocardiograma/static/`
- ✅ **JS específico** en `ecocardiograma/static/`
- ✅ **No interfiere** con archivos existentes

### **4. URLs Organizadas**
- ✅ **Namespace propio**: `ecocardiograma:`
- ✅ **No conflictos** con URLs existentes
- ✅ **Fácil integración** en menús

---

## ✅ CHECKLIST DE VERIFICACIÓN

- [ ] **App creada**: `python manage.py startapp ecocardiograma`
- [ ] **INSTALLED_APPS**: Agregado en `settings.py`
- [ ] **URLs**: Include agregado en `urls.py` principal
- [ ] **Directorios**: Templates y static creados
- [ ] **Modelos**: Archivo `models.py` actualizado
- [ ] **Vistas**: Archivo `views.py` con funciones AJAX
- [ ] **Templates**: Base extendido correctamente
- [ ] **Static Files**: CSS y JS en ubicación correcta
- [ ] **Migraciones**: Ejecutadas correctamente
- [ ] **Imagen**: `segmentos.png` agregada
- [ ] **Navegación**: Links agregados al header

---

## 🔧 MODIFICACIONES ESPECÍFICAS PARA TU PROYECTO

### **Diferencias con el código original:**
1. **Import de modelos**: `from main.models import HistoriaClinica`
2. **Template base**: `{% extends 'base.html' %}` (no path específico)
3. **Static URLs**: `ecocardiograma/static/ecocardiograma/`
4. **Namespace**: `ecocardiograma:` en todas las URLs

### **Ventajas de esta integración:**
- ✅ **No modifica** tu código existente
- ✅ **Reutiliza** infraestructura de main
- ✅ **Mantiene** separación de responsabilidades
- ✅ **Fácil mantenimiento** independiente
- ✅ **Escalable** para futuros módulos médicos

¿Procedo a darte los archivos específicos con las rutas exactas para tu proyecto?