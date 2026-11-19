from django.db import migrations


CATEGORIAS_INICIALES = [
    ("documentos-personales", "Documentos personales"),
    ("carnets-tarjetas", "Carnets y tarjetas"),
    ("celulares-dispositivos-electronicos", "Celulares y dispositivos electrónicos"),
    ("mochilas-bolsos", "Mochilas y bolsos"),
    ("llaves", "Llaves"),
    ("ropa-accesorios", "Ropa y accesorios"),
    ("dinero-billeteras", "Dinero y billeteras"),
    ("mascotas", "Mascotas"),
    ("otros-objetos", "Otros objetos"),
]


def cargar_categorias(apps, schema_editor):
    Categoria = apps.get_model("categorias", "Categoria")
    for orden, (slug, nombre) in enumerate(CATEGORIAS_INICIALES, start=1):
        Categoria.objects.update_or_create(
            slug=slug,
            defaults={"nombre": nombre, "activa": True, "orden": orden},
        )


def eliminar_categorias(apps, schema_editor):
    Categoria = apps.get_model("categorias", "Categoria")
    Categoria.objects.filter(
        slug__in=[slug for slug, _ in CATEGORIAS_INICIALES]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("categorias", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(cargar_categorias, eliminar_categorias),
    ]
