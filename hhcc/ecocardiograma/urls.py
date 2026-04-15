from django.urls import path
from . import views

app_name = 'ecocardiograma'

urlpatterns = [
    # Mostrar formulario
    path('<int:historia_id>/', views.nuevo_estudio, name='nuevo_estudio_form'),
    path('<int:historia_id>/estudios/', views.listar_estudios, name='listar_estudios'),
    path('<int:historia_id>/nuevo/', views.nuevo_estudio, name='nuevo_estudio'),
    
    # Guardar todo via AJAX (Alpine.js)
    path('guardar_todo_ajax/<int:historia_id>/', views.guardar_todo_ajax, name='guardar_todo_ajax'),

    # Endpoints legacy
    path('guardarPaciente', views.guardar_paciente, name='guardar_paciente'),
    path('guardarBidimensional', views.guardar_bidimensional, name='guardar_bidimensional'),
    path('guardarCoppler', views.guardar_coppler, name='guardar_coppler'),
    path('guardarSegmentos', views.guardar_segmentos, name='guardar_segmentos'),
    path('guardarConclusiones', views.guardar_conclusiones, name='guardar_conclusiones'),
    path('guardarConclusionB', views.guardar_conclusion_b, name='guardar_conclusion_b'),
    path('guardarComentarioFinal', views.guardar_comentario_final, name='guardar_comentario_final'),
    
    # Imprimir estudio  
    path('imprimir_estudio/<int:estudio_id>/', views.imprimir_estudio, name='imprimir_estudio'),
]
