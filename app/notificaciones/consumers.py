from django.db.models import Q

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from app.conversaciones.models import Conversacion
from app.conversaciones.presencia import (
    actualizar_latido_presencia,
    cerrar_conexion_presencia,
    obtener_estados_presencia,
    registrar_conexion_presencia,
)

from .realtime import obtener_contadores_usuario


@database_sync_to_async
def _obtener_contadores(usuario_id):
    return obtener_contadores_usuario(usuario_id)


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
def _obtener_contactos(usuario_id, usuarios_ids):
    relaciones = Conversacion.objects.filter(
        Q(
            interesado_id=usuario_id,
            publicacion__usuario_id__in=usuarios_ids,
        )
        | Q(
            publicacion__usuario_id=usuario_id,
            interesado_id__in=usuarios_ids,
        )
    ).values_list("interesado_id", "publicacion__usuario_id")
    return {
        publicador_id if interesado_id == usuario_id else interesado_id
        for interesado_id, publicador_id in relaciones
    }


@database_sync_to_async
def _obtener_estados_presencia(usuarios_ids):
    return obtener_estados_presencia(usuarios_ids)


def _normalizar_usuarios_ids(valores):
    if not isinstance(valores, list) or len(valores) > 100:
        return None

    usuarios_ids = set()
    for valor in valores:
        if isinstance(valor, bool):
            continue
        if isinstance(valor, int):
            usuario_id = valor
        elif isinstance(valor, str) and valor.isdecimal() and len(valor) <= 20:
            usuario_id = int(valor)
        else:
            continue
        if usuario_id > 0:
            usuarios_ids.add(usuario_id)
    return usuarios_ids


class ContadoresConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        usuario = self.scope["user"]
        if not usuario.is_authenticated:
            await self.close(code=4401)
            return

        self.usuario_id = usuario.pk
        self.group_name = f"usuario_{usuario.pk}"
        self.presencia_usuario_ids = set()
        self.presencia_groups = set()
        await self.accept()
        await self.channel_layer.group_add(self.group_name, self.channel_name)
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
        await self.enviar_contadores()

    async def disconnect(self, close_code):
        group_name = getattr(self, "group_name", None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)
            estado = await _cerrar_presencia(self.channel_name)
            if estado and not estado["en_linea"]:
                await self._publicar_presencia(estado)
        for group in self.presencia_groups:
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive_json(self, content):
        if not isinstance(content, dict):
            return
        if content.get("tipo") == "ping":
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
            await self.send_json({"tipo": "pong"})
        elif content.get("tipo") == "presencia_suscribir":
            await self._suscribir_presencia(content.get("usuarios"))

    async def _suscribir_presencia(self, valores):
        usuarios_ids = _normalizar_usuarios_ids(valores)
        if usuarios_ids is None:
            return

        usuarios_ids.discard(self.usuario_id)
        permitidos = await _obtener_contactos(self.usuario_id, usuarios_ids)
        for group in self.presencia_groups:
            await self.channel_layer.group_discard(group, self.channel_name)

        self.presencia_usuario_ids = permitidos
        self.presencia_groups = {
            f"presencia_usuario_{usuario_id}" for usuario_id in permitidos
        }
        for group in self.presencia_groups:
            await self.channel_layer.group_add(group, self.channel_name)

        estados = await _obtener_estados_presencia(permitidos)
        for usuario_id in sorted(estados):
            await self.send_json({"tipo": "presencia", **estados[usuario_id]})

    async def _publicar_presencia(self, estado):
        await self.channel_layer.group_send(
            f"presencia_usuario_{estado['usuario_id']}",
            {"type": "presencia.actualizar", **estado},
        )

    async def presencia_actualizar(self, evento):
        if evento["usuario_id"] not in self.presencia_usuario_ids:
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

    async def contadores_actualizar(self, evento):
        await self.enviar_contadores()

    async def enviar_contadores(self):
        usuario_id = self.scope["user"].pk
        contadores = await _obtener_contadores(usuario_id)
        await self.send_json({"tipo": "contadores", **contadores})
