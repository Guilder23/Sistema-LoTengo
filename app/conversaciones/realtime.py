import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


logger = logging.getLogger(__name__)


def publicar_confirmacion_lectura(conversacion_id, lector_id, mensaje_ids):
    if not mensaje_ids:
        return

    canal = get_channel_layer()
    if canal is None:
        logger.error(
            "No se publicaron confirmaciones de lectura para la conversación %s: "
            "no hay una capa de canales configurada.",
            conversacion_id,
        )
        return

    try:
        async_to_sync(canal.group_send)(
            f"conversacion_{conversacion_id}",
            {
                "type": "chat.lectura",
                "usuario_id": lector_id,
                "mensaje_ids": list(mensaje_ids),
            },
        )
    except Exception:
        logger.exception(
            "No se publicaron confirmaciones de lectura para la conversación %s.",
            conversacion_id,
        )
