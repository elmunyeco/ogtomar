from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("qbi2", "0005_solicitudreceta_client_request_id")]

    operations = [
        migrations.CreateModel(
            name="PatientLoginThrottle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("document_hash", models.CharField(max_length=64, unique=True)),
                ("failed_attempts", models.PositiveSmallIntegerField(default=0)),
                ("blocked_until", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "qbi2_patient_login_throttle"},
        )
    ]
