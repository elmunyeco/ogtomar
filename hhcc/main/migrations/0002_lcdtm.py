from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comentariosvisitas',
            name='fecha',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
