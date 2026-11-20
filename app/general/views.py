from django.shortcuts import render

from app.categorias.models import Categoria
from app.geografia.models import Departamento
from app.publicaciones.models import Publicacion


def inicio(request):
    publicaciones_recientes = (
        Publicacion.objects.filter(estado=Publicacion.Estado.PUBLICADA)
        .select_related(
            "categoria",
            "ubicacion",
            "ubicacion__departamento",
            "ubicacion__municipio",
        )
        .prefetch_related("imagenes")
        .order_by("-creada_en")[:12]
    )
    return render(
        request,
        "general/inicio.html",
        {
            "publicaciones_recientes": publicaciones_recientes,
            "categorias": Categoria.objects.filter(activa=True),
            "departamentos": Departamento.objects.all(),
        },
    )
