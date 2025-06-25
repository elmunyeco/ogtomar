# migrations/0002_fix_indexes_and_sexo.py
# MIGRACIÓN LIMPIA - Solo cambios necesarios

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_recreate_clean'),
    ]

    operations = [
        # ✅ SOLO EL CAMBIO DEL SEXO (esto SÍ es necesario)
        migrations.AlterField(
            model_name='paciente',
            name='sexo',
            field=models.CharField(
                choices=[('H', 'Hombre'), ('M', 'Mujer')], 
                max_length=1, 
                verbose_name='Sexo'
            ),
        ),
        
        # ✅ SOLO LOS ÍNDICES PROBLEMÁTICOS (si no existen)
        # Verificar primero en la base si estos índices YA EXISTEN
        
        # Este índice es el que causaba el error de nombre largo
        migrations.RunSQL(
            # Crear solo si no existe
            "CREATE INDEX IF NOT EXISTS ind_hist_fecha_idx ON indicaciones_visitas (historia_clinica_id, fecha);",
            reverse_sql="DROP INDEX IF EXISTS ind_hist_fecha_idx;"
        ),
        
        #  REMOVER TODO LO DEMÁS QUE PUEDE CAUSAR PROBLEMAS:
        # - No cambiar idTipoDoc (puede romper relaciones)
        # - No renombrar índices existentes
        # - No agregar índices que ya existen
    ]
