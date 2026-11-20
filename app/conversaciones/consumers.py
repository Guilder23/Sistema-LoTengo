import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.db.models import Q

from .models import Conversacion
from .services import ErrorMensaje, crear_mensaje, marcar_mensajes_leidos


logger = logging.getLogger(__name__)


@database_sync_to_async
def _es_participante(conversacion_id, usuario_id):
    return Conversacion.objects.filter(pk=conversacion_id).filter(
        Q(interesado_id=usuario_id) | Q(publicacion__usuario_id=usuario_id)
    ).exists()


@database_sync_to_async
def _crear_mensaje(conversacion_id, usuario, contenido):
    return crear_mensaje(conversacion_id, usuario, contenido)


@database_sync_to_async
def _marcar_leido(conversacion_id, usuario_id):
    marcar_mensajes_leidos(conversacion_id, usuario_id)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        usuario = self.scope["user"]
        if not usuario.is_authenticated:
            await self.close(code=4401)
            return

        self.conversacion_id = int(
            self.scope["url_route"]["kwargs"]["conversation_id"]
        )
        if not await _es_participante(self.conversacion_id, usuario.pk):
            await self.close(code=4403)
            return

        self.group_name = f"conversacion_{self.conversacion_id}"
        await _marcar_leido(self.conversacion_id, usuario.pk)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"tipo": "conexion", "estado": "conectada"})

    async def disconnect(self, close_code):
        logger.debug("WebSocket de conversación cerrado con código %s.", close_code)
        group_name = getattr(self, "group_name", None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive_json(self, content):
        if not isinstance(content, dict) or content.get("tipo") != "mensaje":
            await self.send_json(
                {"tipo": "error", "mensaje": "Tipo de mensaje no admitido."}
            )
            return

        id_cliente = content.get("id_cliente", "")
        if not isinstance(id_cliente, str) or len(id_cliente) > 64:
            id_cliente = ""
        try:
            mensaje = await _crear_mensaje(
                self.conversacion_id,
                self.scope["user"],
                content.get("contenido", ""),
            )
        except ErrorMensaje as error:
            await self.send_json(
                {
                    "tipo": "error",
                    "mensaje": str(error),
                    "id_cliente": id_cliente,
                }
            )
            return
        except Conversacion.DoesNotExist:
            await self.close(code=4404)
            return

        mensaje["id_cliente"] = id_cliente
        await self._publicar(mensaje)

    async def _publicar(self, mensaje):
        try:
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "chat.mensaje", "mensaje": mensaje},
            )
        except Exception:
            logger.exception(
                "No se pudo transmitir el mensaje %s por WebSocket.",
                mensaje.get("id"),
            )
            await self.send_json(
                {
                    "tipo": "error",
                    "mensaje": (
                        "El mensaje se guardó, pero no se pudo actualizar el chat "
                        "en tiempo real. Recarga la conversación."
                    ),
                }
            )

    async def chat_mensaje(self, evento):
        mensaje = evento["mensaje"]
        usuario = self.scope["user"]
        if mensaje["remitente_id"] != usuario.pk:
            await _marcar_leido(self.conversacion_id, usuario.pk)
        await self.send_json({"tipo": "mensaje", "mensaje": mensaje})
