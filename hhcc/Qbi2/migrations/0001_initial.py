from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Qbi2CacheEntry",
            fields=[
                ("key_hash", models.CharField(max_length=64, primary_key=True, serialize=False)),
                ("cache_key", models.TextField()),
                ("namespace", models.CharField(default="vademecum", max_length=80)),
                ("provider", models.CharField(default="qbi2", max_length=40)),
                ("endpoint", models.CharField(default="", max_length=120)),
                ("cliente_app_id", models.CharField(blank=True, default="", max_length=80)),
                ("normalized_query", models.CharField(blank=True, default="", max_length=255)),
                ("page", models.PositiveIntegerField(default=1)),
                ("params_hash", models.CharField(blank=True, default="", max_length=64)),
                ("schema_version", models.PositiveIntegerField(default=1)),
                ("status", models.CharField(default="ok", max_length=40)),
                ("value", models.JSONField()),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("fetched_at", models.DateTimeField()),
                ("fresh_until", models.DateTimeField()),
                ("stale_until", models.DateTimeField()),
                ("refresh_locked_until", models.DateTimeField(blank=True, null=True)),
                ("refresh_token", models.CharField(blank=True, max_length=64, null=True)),
                ("refresh_started_at", models.DateTimeField(blank=True, null=True)),
                ("last_refresh_error", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "qbi2_cache_entries",
            },
        ),
        migrations.AddIndex(
            model_name="qbi2cacheentry",
            index=models.Index(fields=["namespace", "provider"], name="qbi2_cache_ns_provider_idx"),
        ),
        migrations.AddIndex(
            model_name="qbi2cacheentry",
            index=models.Index(fields=["normalized_query"], name="qbi2_cache_query_idx"),
        ),
        migrations.AddIndex(
            model_name="qbi2cacheentry",
            index=models.Index(fields=["fresh_until"], name="qbi2_cache_fresh_idx"),
        ),
        migrations.AddIndex(
            model_name="qbi2cacheentry",
            index=models.Index(fields=["stale_until"], name="qbi2_cache_stale_idx"),
        ),
        migrations.AddIndex(
            model_name="qbi2cacheentry",
            index=models.Index(fields=["refresh_locked_until"], name="qbi2_cache_lock_idx"),
        ),
    ]

