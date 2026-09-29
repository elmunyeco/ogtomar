from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("qbi2", "0002_solicitud_receta"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Qbi2CacheEntry",
        ),
    ]
