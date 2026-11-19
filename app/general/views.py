from django.shortcuts import render

from app.publicaciones.models import Publicacion


def inicio(request):
    publicaciones_recientes = (
        Publicacion.objects.filter(estado=Publicacion.Estado.PUBLICADA)
        .select_related("categoria", "ubicacion")
        .prefetch_related("imagenes")
        .order_by("-creada_en")[:6]
    )
    return render(
        request,
        "general/inicio.html",
        {"publicaciones_recientes": publicaciones_recientes},
    )
