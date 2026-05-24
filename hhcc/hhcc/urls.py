"""
URL configuration for hhcc project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, include
from Qbi2 import views as qbi2_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('vademecum/', login_required(qbi2_views.vademecum_page), name='vademecum'),
    path('receta-poc/', login_required(qbi2_views.receta_poc_page), name='receta_poc'),
    path('receta-poc/solicitudes/', login_required(qbi2_views.solicitudes_receta_page), name='receta_poc_solicitudes'),
    path('poc-recetas/', login_required(qbi2_views.receta_poc_page), name='poc_recetas'),
    path('poc-recetas/solicitudes/', login_required(qbi2_views.solicitudes_receta_page), name='poc_recetas_solicitudes'),
    path('PoC-pacientes-portal/', qbi2_views.pacientes_portal_page, name='poc_pacientes_portal'),
    path('', include('main.urls')),
    path('ecocardiograma/', include('ecocardiograma.urls')),
    path('carotidas/', include('carotidas.urls')),
    path('ecostress/', include('ecostress.urls')),
    path('mmii/', include('mmii.urls')),
    path('qbi2/', include('Qbi2.urls')),
]
