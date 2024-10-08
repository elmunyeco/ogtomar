# Generated by Django 5.1.1 on 2024-10-09 23:42

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoDocumento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50)),
                ('descripcion', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Paciente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numDoc', models.CharField(max_length=50)),
                ('nombre', models.CharField(max_length=50)),
                ('apellido', models.CharField(max_length=50)),
                ('fechaNac', models.DateField()),
                ('sexo', models.CharField(choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')], max_length=1)),
                ('mail', models.EmailField(blank=True, max_length=50, null=True)),
                ('direccion', models.CharField(blank=True, max_length=100, null=True)),
                ('localidad', models.CharField(blank=True, max_length=60, null=True)),
                ('obraSocial', models.CharField(max_length=50)),
                ('plan', models.CharField(blank=True, max_length=50, null=True)),
                ('afiliado', models.CharField(max_length=50)),
                ('telefono', models.CharField(max_length=50)),
                ('celular', models.CharField(max_length=50)),
                ('profesion', models.CharField(max_length=50)),
                ('referente', models.CharField(blank=True, max_length=50, null=True)),
                ('fechaAlta', models.DateField(default=django.utils.timezone.now)),
                ('deBaja', models.BooleanField(default=False)),
                ('idTipoDoc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.tipodocumento')),
            ],
            options={
                'db_table': 'pacientes',
            },
        ),
        migrations.CreateModel(
            name='Identificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=20)),
                ('tipo_documento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.tipodocumento')),
            ],
        ),
        migrations.CreateModel(
            name='HistoriaClinica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fechaAlta', models.DateField(default=django.utils.timezone.now)),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='historias_clinicas', to='main.paciente')),
            ],
            options={
                'db_table': 'historias_clinicas',
                'indexes': [models.Index(fields=['fechaAlta'], name='historia_fechaAlta_idx'), models.Index(fields=['paciente'], name='idPaciente_idx')],
            },
        ),
        migrations.AddIndex(
            model_name='paciente',
            index=models.Index(fields=['nombre'], name='nombre_idx'),
        ),
        migrations.AddIndex(
            model_name='paciente',
            index=models.Index(fields=['apellido'], name='apellido_idx'),
        ),
        migrations.AddIndex(
            model_name='paciente',
            index=models.Index(fields=['fechaAlta'], name='paciente_fechaAlta_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='paciente',
            unique_together={('idTipoDoc_id', 'numDoc')},
        ),
    ]
