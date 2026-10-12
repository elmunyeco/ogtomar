from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("qbi2", "0007_solicitudreceta_hidden_from_history_at")]
    operations = [
        migrations.CreateModel(
            name="MedicamentoHabitualOculto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reg_no", models.CharField(max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("paciente", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="main.paciente")),
            ],
            options={"constraints": [models.UniqueConstraint(fields=("paciente", "reg_no"), name="qbi2_habitual_oculto_unique")]},
        ),
    ]
