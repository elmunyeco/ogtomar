from django.db import migrations


def forwards(apps, schema_editor):
    table_names = {name.lower() for name in schema_editor.connection.introspection.table_names()}
    if "doppler" not in table_names:
        return
    if "mmii" not in table_names:
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(1) FROM mmii")
        mmii_count = cursor.fetchone()[0]
        if mmii_count:
            # Avoid duplicating if mmii already has data.
            cursor.execute("DROP TABLE doppler")
            return
        cursor.execute(
            """
            INSERT INTO mmii (
                idMMII,
                idHC,
                artFemComunDerecha,
                artFemSuperficialDerecha,
                artFemProfundaDerecha,
                artPopliteaDerecha,
                artInfrapatelaresDerecha,
                artFemComunIzquierda,
                artFemSuperficialIzquierda,
                artFemProfundaIzquierda,
                artPopliteaIzquierda,
                artInfrapatelaresIzquierda,
                conclusion
            )
            SELECT
                idDoppler,
                idHC,
                artFemComunDerecha,
                artFemSuperficialDerecha,
                artFemProfundaDerecha,
                artPopliteaDerecha,
                artInfrapatelaresDerecha,
                artFemComunIzquierda,
                artFemSuperficialIzquierda,
                artFemProfundaIzquierda,
                artPopliteaIzquierda,
                artInfrapatelaresIzquierda,
                conclusion
            FROM doppler
            """
        )
        cursor.execute("DROP TABLE doppler")


class Migration(migrations.Migration):

    dependencies = [
        ("mmii", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
