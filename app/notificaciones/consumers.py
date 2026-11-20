from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .realtime import obtener_contadores_usuario


@database_sync_to_async
def _obtener_contadores(usuario_id):
    return obtener_contadores_usuario(usuario_id)


class ContadoresConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        usuario = self.scope["user"]
        if not usuario.is_authenticated:
            await self.close(code=4401)
            return

        self.group_name = f"usuario_{usuario.pk}"
        await self.accept()
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.enviar_contadores()

    async def disconnect(self, close_code):
        group_name = getattr(self, "group_name", None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive_json(self, content):
        if isinstance(content, dict) and content.get("tipo") == "ping":
            await self.send_json({"tipo": "pong"})

    async def contadores_actualizar(self, evento):
        await self.enviar_contadores()

    async def enviar_contadores(self):
        usuario_id = self.scope["user"].pk
        contadores = await _obtener_contadores(usuario_id)
        await self.send_json({"tipo": "contadores", **contadores})
