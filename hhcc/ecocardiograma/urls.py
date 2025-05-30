# Archivo: ecocardiograma/urls.py

from django.urls import path
from . import views

app_name = 'ecocardiograma'

urlpatterns = [
    # Vista principal para crear o editar estudio
    path('nuevo/<int:historia_id>/', views.nuevo_estudio, name='nuevo_estudio'),
    
    # URLs para guardar secciones individuales (para peticiones AJAX del sistema anterior)
    path('guardar_paciente/', views.guardar_paciente, name='guardar_paciente'),
    path('guardar_bidimensional/', views.guardar_bidimensional, name='guardar_bidimensional'),
    path('guardar_doppler/', views.guardar_doppler, name='guardar_doppler'),
    path('guardar_segmentos/', views.guardar_segmentos, name='guardar_segmentos'),
    path('guardar_conclusiones/', views.guardar_conclusiones, name='guardar_conclusiones'),
    path('guardar_conclusion_b/', views.guardar_conclusion_b, name='guardar_conclusion_b'),
    path('guardar_comentario_final/', views.guardar_comentario_final, name='guardar_comentario_final'),
    
    # Nueva URL para guardado completo AJAX
    path('guardar_todo_ajax/<int:historia_id>/', views.guardar_todo_ajax, name='guardar_todo_ajax'),
    
    # URL para guardar todo a la vez (sistema anterior)
    path('guardar_todo/<int:historia_id>/', views.guardar_todo, name='guardar_todo'),
    
    # URL para imprimir estudio
    path('imprimir_estudio/<int:estudio_id>/', views.imprimir_estudio, name='imprimir_estudio'),
    path('imprimir_estudio/<int:estudio_id>/<int:historia_id>/', views.imprimir_estudio, name='imprimir_estudio_con_historia'),
]