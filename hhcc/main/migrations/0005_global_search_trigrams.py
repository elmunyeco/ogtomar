# Generated manually for global identificatory search.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0004_index_state_alignment"),
    ]

    operations = [
        migrations.CreateModel(
            name="GlobalSearchDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("document_key", models.CharField(max_length=80, unique=True)),
                ("title", models.CharField(max_length=255)),
                ("subtitle", models.CharField(blank=True, max_length=255, null=True)),
                ("search_text_normalized", models.TextField()),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "historia",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="global_search_documents",
                        to="main.historiaclinica",
                    ),
                ),
                (
                    "paciente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="global_search_documents",
                        to="main.paciente",
                    ),
                ),
            ],
            options={
                "db_table": "global_search_documents",
            },
        ),
        migrations.CreateModel(
            name="GlobalSearchGram",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("gram", models.CharField(max_length=3)),
                ("weight", models.PositiveSmallIntegerField(default=1)),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="grams",
                        to="main.globalsearchdocument",
                    ),
                ),
            ],
            options={
                "db_table": "global_search_grams",
                "unique_together": {("document", "gram")},
            },
        ),
        migrations.AddIndex(
            model_name="globalsearchdocument",
            index=models.Index(fields=["paciente"], name="global_search_doc_paciente_idx"),
        ),
        migrations.AddIndex(
            model_name="globalsearchdocument",
            index=models.Index(fields=["historia"], name="global_search_doc_historia_idx"),
        ),
        migrations.AddIndex(
            model_name="globalsearchgram",
            index=models.Index(fields=["gram"], name="global_search_gram_idx"),
        ),
    ]
