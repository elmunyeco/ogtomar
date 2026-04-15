from django.urls import path
from . import views

app_name = 'ecocardiograma'

urlpatterns = [
    # Mostrar formulario
    path('nuevo/<int:historia_id>/', views.nuevo_estudio, name='nuevo_estudio'),
    
    # Guardar todo via AJAX (Alpine.js)
    path('guardar_todo_ajax/<int:historia_id>/', views.guardar_todo_ajax, name='guardar_todo_ajax'),
    
    # Imprimir estudio  
    path('imprimir_estudio/<int:estudio_id>/', views.imprimir_estudio, name='imprimir_estudio'),
]
