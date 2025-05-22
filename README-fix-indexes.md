# Fix para Índices de Django - Migración 0003

## Problema

Al ejecutar `python manage.py migrate` se produce el siguiente error:

```
MySQLdb.OperationalError: (1176, "Key 'indicacione_idHisto_248eeb_idx' doesn't exist in table 'indicaciones_visitas'")
```

Este error ocurre porque existe una desincronización entre los índices que Django espera y los que realmente existen en la base de datos MySQL/MariaDB.

## Causa

El problema surge cuando:
- Se usa la misma base de datos en múltiples entornos de desarrollo
- Los índices fueron creados manualmente o con nombres diferentes
- Las migraciones no se aplicaron en el mismo orden en todos los entornos

## Verificación del Problema

Antes de aplicar el fix, verifica el estado actual de los índices:

```sql
SHOW INDEXES FROM indicaciones_visitas;
```

**Estado problemático típico:**
- Solo existe el índice `idHC` en lugar de los índices que Django espera
- Faltan los índices: `indicacione_fecha_b762b7_idx`, `indicacione_histori_e75187_idx`, `indicacione_histori_4b9d3d_idx`

## Solución Paso a Paso

### 1. Marcar la migración problemática como "fake"

```bash
python manage.py migrate --fake main 0003_conclusiónecocardiograma_estudioecocardiograma_and_more
```

Este comando le dice a Django que la migración se aplicó correctamente sin ejecutar las operaciones SQL problemáticas.

### 2. Crear migración para arreglar índices

```bash
python manage.py makemigrations main --empty --name fix_indices_only
```

### 3. Editar la migración generada

Abre el archivo `main/migrations/000X_fix_indices_only.py` y reemplaza el contenido por:

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('main', '0003_conclusiónecocardiograma_estudioecocardiograma_and_more'),
    ]

    operations = [
        # Eliminar índice existente problemático
        migrations.RunSQL(
            "DROP INDEX IF EXISTS idHC ON indicaciones_visitas;",
            reverse_sql="CREATE INDEX idHC ON indicaciones_visitas (historia_clinica_id);"
        ),
        
        # Crear índices que Django espera
        migrations.AddIndex(
            model_name="indicacionesvisitas",
            index=models.Index(fields=["fecha"], name="indicacione_fecha_b762b7_idx"),
        ),
        migrations.AddIndex(
            model_name="indicacionesvisitas", 
            index=models.Index(fields=["historia_clinica"], name="indicacione_histori_e75187_idx"),
        ),
        migrations.AddIndex(
            model_name="indicacionesvisitas",
            index=models.Index(fields=["historia_clinica", "fecha"], name="indicacione_histori_4b9d3d_idx"),
        ),
    ]
```

### 4. Aplicar la migración de corrección

```bash
python manage.py migrate
```

### 5. Verificar la solución

```sql
SHOW INDEXES FROM indicaciones_visitas;
```

**Estado correcto esperado:**
```
| Table                | Key_name                       | Column_name         |
|----------------------|--------------------------------|---------------------|
| indicaciones_visitas | PRIMARY                        | id                  |
| indicaciones_visitas | indicacione_fecha_b762b7_idx   | fecha               |
| indicaciones_visitas | indicacione_histori_e75187_idx | historia_clinica_id |
| indicaciones_visitas | indicacione_histori_4b9d3d_idx | historia_clinica_id |
| indicaciones_visitas | indicacione_histori_4b9d3d_idx | fecha               |
```

## Para Nuevos Entornos

### Si es un entorno completamente nuevo:
```bash
python manage.py migrate
```
(Debería funcionar sin problemas)

### Si es un entorno existente con el mismo problema:
Sigue todos los pasos de la "Solución Paso a Paso" descritos arriba.

## Prevención Futura

Para evitar este problema en el futuro:

1. **Siempre compartir archivos de migración** entre todos los entornos
2. **Usar control de versiones** para los archivos `migrations/`
3. **Aplicar migraciones en el mismo orden** en todos los entornos
4. **Considerar usar Docker** para entornos de desarrollo idénticos
5. **No modificar la base de datos manualmente** sin crear migraciones correspondientes

## Troubleshooting

### Error: "Table already exists"
Si aparece este error, significa que las tablas ya fueron creadas. Usa `--fake` para marcar esa migración como aplicada.

### Error: "Circular dependency"
Verifica que las dependencias en el archivo de migración sean correctas y no referencien la misma migración.

### Error: "models is not defined"
Asegúrate de que el archivo de migración incluya la importación:
```python
from django.db import migrations, models
```

## Archivos Modificados

- `main/migrations/000X_fix_indices_only.py` (nuevo archivo de migración)
- Base de datos: tabla `indicaciones_visitas` (índices actualizados)

---

**Nota:** Este fix es específico para el problema de índices en la tabla `indicaciones_visitas`. Las nuevas tablas de ecocardiograma se crean correctamente con la migración fake.
