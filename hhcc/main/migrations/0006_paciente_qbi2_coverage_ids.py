from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("main", "0005_global_search_trigrams")]

    operations = [
        migrations.AddField(
            model_name="paciente",
            name="qbi2_financiador_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="paciente",
            name="qbi2_plan_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
