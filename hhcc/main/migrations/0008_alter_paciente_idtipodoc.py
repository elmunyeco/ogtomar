# Generated by Django 5.1.1 on 2024-10-10 20:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_alter_paciente_idtipodoc'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paciente',
            name='idTipoDoc',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to='main.tipodocumento'),
        ),
    ]