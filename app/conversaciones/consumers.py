import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.db.models import Q

from .models import Conversacion
from .presencia import (
    actualizar_latido_presencia,
    cerrar_conexion_presencia,
    obtener_estado_presencia,
    registrar_conexion_presencia,
)
from .services import ErrorMensaje, crear_mensaje, marcar_mensajes_leidos


logger = logging.getLogger(__name__)


@database_sync_to_async
def _es_participante(conversacion_id, usuario_id):
    return Conversacion.objects.filter(pk=conversacion_id).filter(
        Q(interesado_id=usuario_id) | Q(publicacion__usuario_id=usuario_id)
    ).exists()


@database_sync_to_async
def _obtener_contacto_id(conversacion_id, usuario_id):
    conversacion = (
        Conversacion.objects.filter(pk=conversacion_id)
        .values("interesado_id", "publicacion__usuario_id")
        .first()
    )
    if conversacion is None:
        return None
    if conversacion["interesado_id"] == usuario_id:
        return conversacion["publicacion__usuario_id"]
    return conversacion["interesado_id"]


@database_sync_to_async
def _crear_mensaje(conversacion_id, usuario, contenido):
    return crear_mensaje(conversacion_id, usuario, contenido)


@database_sync_to_async
def _marcar_leido(conversacion_id, usuario_id):
    marcar_mensajes_leidos(conversacion_id, usuario_id)


@database_sync_to_async
def _registrar_presencia(usuario_id, canal):
    return registrar_conexion_presencia(usuario_id, canal)


@database_sync_to_async
def _actualizar_latido(usuario_id, canal):
    return actualizar_latido_presencia(usuario_id, canal)


@database_sync_to_async
def _cerrar_presencia(canal):
    return cerrar_conexion_presencia(canal)


@database_sync_to_async
def _obtener_presencia(usuario_id):
    return obtener_estado_presencia(usuario_id)


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

        self.usuario_id = usuario.pk
        self.contacto_id = await _obtener_contacto_id(
            self.conversacion_id,
            self.usuario_id,
        )
        if self.contacto_id is None:
            await self.close(code=4403)
            return

        self.group_name = f"conversacion_{self.conversacion_id}"
        self.presencia_groups = {
            f"presencia_usuario_{self.usuario_id}",
            f"presencia_usuario_{self.contacto_id}",
        }
        self.escribiendo = False
        await _marcar_leido(self.conversacion_id, usuario.pk)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        for group in self.presencia_groups:
            await self.channel_layer.group_add(group, self.channel_name)
        await self.accept()

        expirados = await _registrar_presencia(self.usuario_id, self.channel_name)
        for estado in expirados:
            await self._publicar_presencia(estado)
        await self._publicar_presencia(
            {
                "usuario_id": self.usuario_id,
                "en_linea": True,
                "ultima_vez": "",
                "segundos_desde_ultima_vez": None,
            }
        )
        await self.send_json(
            {
                "tipo": "presencia",
                **await _obtener_presencia(self.contacto_id),
            }
        )

    async def disconnect(self, close_code):
        logger.debug("WebSocket de conversación cerrado con código %s.", close_code)
        group_name = getattr(self, "group_name", None)
        if group_name:
            if getattr(self, "escribiendo", False):
                await self.channel_layer.group_send(
                    group_name,
                    {
                        "type": "chat.escribiendo",
                        "usuario_id": self.usuario_id,
                        "escribiendo": False,
                    },
                )
            await self.channel_layer.group_discard(group_name, self.channel_name)
        if getattr(self, "presencia_groups", None):
            estado = await _cerrar_presencia(self.channel_name)
            if estado and not estado["en_linea"]:
                await self._publicar_presencia(estado)
            for presence_group in self.presencia_groups:
                await self.channel_layer.group_discard(
                    presence_group,
                    self.channel_name,
                )

    async def receive_json(self, content):
        if not isinstance(content, dict):
            await self.send_json(
                {"tipo": "error", "mensaje": "Tipo de mensaje no admitido."}
            )
            return

        tipo = content.get("tipo")
        if tipo == "ping":
            actualizada = await _actualizar_latido(
                self.usuario_id,
                self.channel_name,
            )
            if not actualizada:
                expirados = await _registrar_presencia(
                    self.usuario_id,
                    self.channel_name,
                )
                for estado in expirados:
                    await self._publicar_presencia(estado)
                await self._publicar_presencia(
                    {
                        "usuario_id": self.usuario_id,
                        "en_linea": True,
                        "ultima_vez": "",
                        "segundos_desde_ultima_vez": None,
                    }
                )
            return

        if tipo == "escribiendo":
            escribiendo = content.get("escribiendo")
            if not isinstance(escribiendo, bool) or escribiendo == self.escribiendo:
                return
            self.escribiendo = escribiendo
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "chat.escribiendo",
                    "usuario_id": self.usuario_id,
                    "escribiendo": escribiendo,
                },
            )
            return

        if tipo != "mensaje":
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

    async def _publicar_presencia(self, estado):
        await self.channel_layer.group_send(
            f"presencia_usuario_{estado['usuario_id']}",
            {"type": "presencia.actualizar", **estado},
        )

    async def presencia_actualizar(self, evento):
        if evento["usuario_id"] == self.scope["user"].pk:
            return
        await self.send_json(
            {
                "tipo": "presencia",
                "usuario_id": evento["usuario_id"],
                "en_linea": evento["en_linea"],
                "ultima_vez": evento["ultima_vez"],
                "segundos_desde_ultima_vez": evento[
                    "segundos_desde_ultima_vez"
                ],
            }
        )

    async def chat_escribiendo(self, evento):
        await self.send_json(
            {
                "tipo": "escribiendo",
                "usuario_id": evento["usuario_id"],
                "escribiendo": evento["escribiendo"],
            }
        )

    async def chat_mensaje(self, evento):
        mensaje = evento["mensaje"]
        usuario = self.scope["user"]
        if mensaje["remitente_id"] != usuario.pk:
            await _marcar_leido(self.conversacion_id, usuario.pk)
        await self.send_json({"tipo": "mensaje", "mensaje": mensaje})
