from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("qbi2", "0001_squashed_0004_emisionsolicitudreceta"),
    ]

    operations = [
        migrations.AddField(
            model_name="solicitudreceta",
            name="client_request_id",
            field=models.CharField(
                blank=True,
                help_text="Clave de idempotencia enviada por el cliente médico.",
                max_length=64,
                null=True,
                unique=True,
            ),
        ),
    ]
