import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Count, Q

from app.conversaciones.models import Mensaje

from .models import Notificacion


logger = logging.getLogger(__name__)


def obtener_contadores_usuario(usuario_id):
    mensajes_pendientes = (
        Mensaje.objects.filter(
            Q(conversacion__interesado_id=usuario_id)
            | Q(conversacion__publicacion__usuario_id=usuario_id),
            leida_en__isnull=True,
        )
        .exclude(remitente_id=usuario_id)
    )
    mensajes_por_conversacion = dict(
        mensajes_pendientes.values("conversacion_id")
        .annotate(cantidad=Count("pk"))
        .values_list("conversacion_id", "cantidad")
    )
    mensajes_sin_leer = sum(mensajes_por_conversacion.values())
    notificaciones_sin_leer = Notificacion.objects.filter(
        usuario_id=usuario_id,
        tipo=Notificacion.Tipo.NUEVA_PUBLICACION,
        leida_en__isnull=True,
    ).count()
    return {
        "chats_sin_leer": mensajes_sin_leer,
        "mensajes_por_conversacion": mensajes_por_conversacion,
        "notificaciones_sin_leer": notificaciones_sin_leer,
    }


def publicar_actualizacion_contadores(usuario_id):
    canal = get_channel_layer()
    if canal is None:
        logger.error(
            "No se actualizaron los contadores en vivo del usuario %s: "
            "no hay una capa de canales configurada.",
            usuario_id,
        )
        return

    try:
        async_to_sync(canal.group_send)(
            f"usuario_{usuario_id}",
            {"type": "contadores.actualizar"},
        )
    except Exception:
        logger.exception(
            "No se pudieron actualizar en vivo los contadores del usuario %s.",
            usuario_id,
        )
