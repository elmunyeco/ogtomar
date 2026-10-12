from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("qbi2", "0006_patientloginthrottle")]

    operations = [
        migrations.AddField(
            model_name="solicitudreceta",
            name="hidden_from_history_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
