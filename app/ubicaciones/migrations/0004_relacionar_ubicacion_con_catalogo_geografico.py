import django.db.models.deletion
from django.db import migrations, models


def relacionar_ubicaciones(apps, schema_editor):
    Departamento = apps.get_model("geografia", "Departamento")
    Municipio = apps.get_model("geografia", "Municipio")
    Ubicacion = apps.get_model("ubicaciones", "Ubicacion")
    alias = schema_editor.connection.alias

    for ubicacion in Ubicacion.objects.using(alias).all().iterator():
        departamento = Departamento.objects.using(alias).get(
            codigo=ubicacion.departamento
        )
        municipio, _ = Municipio.objects.using(alias).get_or_create(
            departamento_id=departamento.pk,
            nombre=ubicacion.municipio,
        )
        ubicacion.departamento_ref_id = departamento.pk
        ubicacion.municipio_ref_id = municipio.pk
        ubicacion.save(
            using=alias,
            update_fields=["departamento_ref", "municipio_ref"],
        )


def restaurar_ubicaciones(apps, schema_editor):
    Ubicacion = apps.get_model("ubicaciones", "Ubicacion")
    alias = schema_editor.connection.alias
    for ubicacion in Ubicacion.objects.using(alias).select_related(
        "departamento_ref",
        "municipio_ref",
    ):
        ubicacion.departamento = ubicacion.departamento_ref.codigo
        ubicacion.municipio = ubicacion.municipio_ref.nombre
        ubicacion.save(
            using=alias,
            update_fields=["departamento", "municipio"],
        )


class Migration(migrations.Migration):

    dependencies = [
        ("geografia", "0001_initial"),
        ("ubicaciones", "0003_delete_municipio_alter_ubicacion_departamento"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ubicacion",
            name="departamento",
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name="ubicacion",
            name="municipio",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="ubicacion",
            name="departamento_ref",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="ubicaciones",
                to="geografia.departamento",
            ),
        ),
        migrations.AddField(
            model_name="ubicacion",
            name="municipio_ref",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="ubicaciones",
                to="geografia.municipio",
            ),
        ),
        migrations.RunPython(relacionar_ubicaciones, restaurar_ubicaciones),
        migrations.RemoveField(
            model_name="ubicacion",
            name="departamento",
        ),
        migrations.RemoveField(
            model_name="ubicacion",
            name="municipio",
        ),
        migrations.RenameField(
            model_name="ubicacion",
            old_name="departamento_ref",
            new_name="departamento",
        ),
        migrations.RenameField(
            model_name="ubicacion",
            old_name="municipio_ref",
            new_name="municipio",
        ),
        migrations.AlterField(
            model_name="ubicacion",
            name="departamento",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="ubicaciones",
                to="geografia.departamento",
            ),
        ),
        migrations.AlterField(
            model_name="ubicacion",
            name="municipio",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="ubicaciones",
                to="geografia.municipio",
            ),
        ),
        migrations.AlterModelOptions(
            name="ubicacion",
            options={
                "ordering": ["departamento__nombre", "municipio__nombre", "zona"],
                "verbose_name": "ubicación",
                "verbose_name_plural": "ubicaciones",
            },
        ),
    ]
