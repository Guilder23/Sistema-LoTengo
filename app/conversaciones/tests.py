from datetime import datetime, timedelta, timezone as datetime_timezone
from io import BytesIO
import json
from tempfile import TemporaryDirectory

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from unittest.mock import AsyncMock, patch

from app.categorias.models import Categoria
from app.geografia.models import Departamento, Municipio
from app.notificaciones.models import Notificacion, SuscripcionPush
from app.notificaciones.routing import websocket_urlpatterns as notificaciones_websocket_urlpatterns
from app.publicaciones.models import Publicacion
from app.ubicaciones.models import Ubicacion

from .models import Conversacion, Mensaje
from .routing import websocket_urlpatterns
from .services import crear_mensaje, marcar_mensajes_leidos, serializar_mensaje


class DatosConversaciones:
    @classmethod
    def setUpTestData(cls):
        usuario = get_user_model()
        cls.publicador = usuario.objects.create_user(
            email="publicador@example.com",
            password="Secure-test-password-872!",
            first_name="Ana",
            last_name="Publicadora",
            telefono="+591 70000020",
            correo_verificado=True,
        )
        cls.interesado = usuario.objects.create_user(
            email="interesado@example.com",
            password="Secure-test-password-873!",
            first_name="Luis",
            last_name="Interesado",
            telefono="+591 70000021",
            correo_verificado=True,
        )
        cls.ajeno = usuario.objects.create_user(
            email="ajeno@example.com",
            password="Secure-test-password-874!",
            first_name="Eva",
            last_name="Ajena",
            telefono="+591 70000022",
            correo_verificado=True,
        )
        categoria = Categoria.objects.get(slug="celulares-dispositivos-electronicos")
        departamento = Departamento.objects.get(codigo="cochabamba")
        municipio = Municipio.objects.get(
            departamento=departamento,
            nombre="Cochabamba",
        )
        ubicacion = Ubicacion.objects.create(
            departamento=departamento,
            municipio=municipio,
            zona="Centro",
            conoce_lugar_exacto=True,
            referencia_privada="Entrada norte",
        )
        cls.publicacion = Publicacion.objects.create(
            usuario=cls.publicador,
            categoria=categoria,
            ubicacion=ubicacion,
            tipo=Publicacion.Tipo.PERDIDO,
            titulo="Teléfono azul",
            descripcion="Teléfono perdido en el centro.",
            marca="Marca privada",
            color="Azul",
            caracteristicas_publicas="Tiene una funda azul.",
            caracteristica_privada="Una marca secreta.",
            fecha_evento=timezone.localdate() - timedelta(days=1),
        )


class PruebasConversaciones(DatosConversaciones, TestCase):
    def iniciar_url(self):
        return reverse(
            "conversaciones:iniciar",
            args=[self.publicacion.pk],
        )

    def detalle_url(self, conversacion):
        return reverse("conversaciones:detalle", args=[conversacion.pk])

    def test_iniciar_requiere_autenticacion(self):
        response = self.client.post(self.iniciar_url())

        self.assertEqual(response.status_code, 302)
        self.assertIn("next=", response["Location"])
        self.assertFalse(Conversacion.objects.exists())

    def test_interesado_inicia_reutiliza_y_envia_mensaje_privado(self):
        self.client.force_login(self.interesado)
        detalle_publicacion = self.client.get(
            reverse("publicaciones:detalle", args=[self.publicacion.pk])
        )
        self.assertContains(detalle_publicacion, "Contactar por mensaje")
        response = self.client.post(self.iniciar_url())
        conversacion = Conversacion.objects.get(
            publicacion=self.publicacion,
            interesado=self.interesado,
        )
        self.assertRedirects(response, self.detalle_url(conversacion))

        segunda_respuesta = self.client.post(self.iniciar_url())
        self.assertRedirects(segunda_respuesta, self.detalle_url(conversacion))
        self.assertEqual(Conversacion.objects.count(), 1)

        response = self.client.get(self.detalle_url(conversacion))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Teléfono azul")
        self.assertContains(response, 'js/conversaciones/detalle.js')
        self.assertEqual(response.content.count(b"data-chat-conteo"), 2)
        self.assertNotContains(response, self.publicador.email)
        self.assertNotContains(response, self.publicador.telefono)

        response = self.client.post(
            self.detalle_url(conversacion),
            {"contenido": "Hola, creo que encontré este teléfono."},
        )
        self.assertRedirects(response, self.detalle_url(conversacion))
        mensaje = Mensaje.objects.get(conversacion=conversacion)
        self.assertEqual(mensaje.remitente, self.interesado)
        notificacion = Notificacion.objects.get()
        self.assertEqual(notificacion.usuario, self.publicador)
        self.assertEqual(notificacion.tipo, Notificacion.Tipo.MENSAJE)
        self.assertNotIn("creo que encontré", notificacion.mensaje)

        self.client.force_login(self.publicador)
        response = self.client.get(reverse("conversaciones:lista"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Conversaciones")
        self.assertContains(response, 'aria-label="1 mensaje sin leer"')
        self.assertNotContains(response, self.interesado.email)

        response = self.client.get(self.detalle_url(conversacion))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hola, creo que encontré este teléfono.")
        mensaje.refresh_from_db()
        self.assertIsNotNone(mensaje.leida_en)

    def test_publicador_no_puede_iniciar_conversacion_con_si_mismo(self):
        self.client.force_login(self.publicador)

        response = self.client.post(self.iniciar_url())

        self.assertRedirects(
            response,
            reverse("publicaciones:detalle", args=[self.publicacion.pk]),
        )
        self.assertFalse(Conversacion.objects.exists())

    def test_persona_ajena_no_puede_leer_ni_enviar_mensajes(self):
        conversacion = Conversacion.objects.create(
            publicacion=self.publicacion,
            interesado=self.interesado,
        )
        self.client.force_login(self.ajeno)

        response_lectura = self.client.get(self.detalle_url(conversacion))
        response_envio = self.client.post(
            self.detalle_url(conversacion),
            {"contenido": "Mensaje no autorizado"},
        )

        self.assertEqual(response_lectura.status_code, 404)
        self.assertEqual(response_envio.status_code, 404)
        self.assertFalse(Mensaje.objects.exists())

    def test_no_se_inicia_conversacion_para_publicacion_cerrada(self):
        self.publicacion.estado = Publicacion.Estado.PAUSADA
        self.publicacion.save(update_fields=["estado"])
        self.client.force_login(self.interesado)

        response = self.client.post(self.iniciar_url())

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Conversacion.objects.exists())

    def test_adjuntos_son_privados_y_se_entregan_con_tipo_seguro(self):
        conversacion = Conversacion.objects.create(
            publicacion=self.publicacion,
            interesado=self.interesado,
        )
        imagen_bytes = BytesIO()
        Image.new("RGB", (4, 4), color="blue").save(imagen_bytes, format="PNG")
        imagen = SimpleUploadedFile(
            "foto.png",
            imagen_bytes.getvalue(),
            content_type="image/png",
        )

        with TemporaryDirectory() as directorio:
            with override_settings(MEDIA_ROOT=directorio):
                self.client.force_login(self.interesado)
                response = self.client.post(
                    self.detalle_url(conversacion),
                    {"contenido": "Mira esta foto", "archivo": imagen},
                )
                self.assertRedirects(response, self.detalle_url(conversacion))
                mensaje = Mensaje.objects.get(conversacion=conversacion)
                self.assertEqual(mensaje.tipo_adjunto, Mensaje.TipoAdjunto.IMAGEN)
                self.assertContains(
                    self.client.get(self.detalle_url(conversacion)),
                    "messenger-burbuja-imagen",
                )

                url_adjunto = reverse(
                    "conversaciones:adjunto",
                    args=(conversacion.pk, mensaje.pk),
                )
                response = self.client.get(url_adjunto)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Type"], "image/png")
                self.assertEqual(response["X-Content-Type-Options"], "nosniff")
                response._resource_closers[0]()

                self.client.force_login(self.ajeno)
                response = self.client.get(url_adjunto)
                self.assertEqual(response.status_code, 404)

    def test_audio_adjunto_se_valida_y_se_puede_reproducir_solo_en_el_chat(self):
        conversacion = Conversacion.objects.create(
            publicacion=self.publicacion,
            interesado=self.interesado,
        )
        audio = SimpleUploadedFile(
            "nota.webm",
            b"\x1a\x45\xdf\xa3" + b"\x00" * 24,
            content_type="audio/webm",
        )

        with TemporaryDirectory() as directorio:
            with override_settings(MEDIA_ROOT=directorio):
                self.client.force_login(self.interesado)
                response = self.client.post(
                    self.detalle_url(conversacion),
                    {"contenido": "", "archivo": audio},
                )
                self.assertRedirects(response, self.detalle_url(conversacion))
                mensaje = Mensaje.objects.get(conversacion=conversacion)
                self.assertEqual(mensaje.tipo_adjunto, Mensaje.TipoAdjunto.AUDIO)

                url_adjunto = reverse(
                    "conversaciones:adjunto",
                    args=(conversacion.pk, mensaje.pk),
                )
                response = self.client.get(url_adjunto)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Type"], "audio/webm")
                response._resource_closers[0]()

    @override_settings(
        WEBPUSH_VAPID_PUBLIC_KEY="public-key",
        WEBPUSH_VAPID_PRIVATE_KEY="private-key.pem",
        WEBPUSH_VAPID_SUBJECT="mailto:admin@lotengo.app",
    )
    @patch("app.notificaciones.services.webpush")
    def test_push_de_mensaje_no_expone_contenido_privado(self, enviar_push):
        conversacion = Conversacion.objects.create(
            publicacion=self.publicacion,
            interesado=self.interesado,
        )
        SuscripcionPush.objects.create(
            usuario=self.publicador,
            endpoint="https://fcm.googleapis.com/fcm/send/push-token",
            clave_publica="publicKey_123",
            clave_auth="authKey_456",
        )

        with self.captureOnCommitCallbacks(execute=True):
            crear_mensaje(
                conversacion.pk,
                self.interesado,
                "Mi código privado de verificación es 7431.",
            )

        datos_push = json.loads(enviar_push.call_args.kwargs["data"])
        self.assertEqual(datos_push["title"], "Nuevo mensaje")
        self.assertNotIn("7431", datos_push["body"])
        self.assertNotIn("7431", enviar_push.call_args.kwargs["data"])
        self.assertEqual(
            datos_push["url"],
            reverse("conversaciones:detalle", args=(conversacion.pk,)),
        )

    def test_historial_pagina_mensajes_anteriores(self):
        conversacion = Conversacion.objects.create(
            publicacion=self.publicacion,
            interesado=self.interesado,
        )
        Mensaje.objects.bulk_create(
            [
                Mensaje(
                    conversacion=conversacion,
                    remitente=self.interesado,
                    contenido=f"Mensaje {numero}",
                )
                for numero in range(1, 52)
            ]
        )
        self.client.force_login(self.interesado)

        response = self.client.get(self.detalle_url(conversacion))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cargar mensajes anteriores")
        self.assertEqual(response.content.count(b"data-mensaje-id="), 50)
        mensajes_visibles = response.context["mensajes"]
        self.assertEqual(mensajes_visibles[0].contenido, "Mensaje 2")
        self.assertEqual(mensajes_visibles[-1].contenido, "Mensaje 51")
        primer_mensaje_cargado = response.context["mensajes"][0]

        respuesta_anterior = self.client.get(
            reverse(
                "conversaciones:mensajes_anteriores",
                args=(conversacion.pk,),
            ),
            {"antes": primer_mensaje_cargado.pk},
        )
        self.assertEqual(respuesta_anterior.status_code, 200)
        self.assertEqual(
            respuesta_anterior.json()["mensajes"][0]["contenido"],
            "Mensaje 1",
        )

    def test_hora_de_mensaje_se_muestra_en_zona_horaria_de_la_paz(self):
        conversacion = Conversacion.objects.create(
            publicacion=self.publicacion,
            interesado=self.interesado,
        )
        mensaje = Mensaje.objects.create(
            conversacion=conversacion,
            remitente=self.interesado,
            contenido="Hora de prueba",
        )
        fecha_utc = datetime(
            2026,
            11,
            20,
            14,
            15,
            tzinfo=datetime_timezone.utc,
        )
        Mensaje.objects.filter(pk=mensaje.pk).update(enviada_en=fecha_utc)
        mensaje.refresh_from_db()
        self.assertEqual(serializar_mensaje(mensaje)["hora_la_paz"], "10:15")
        self.assertFalse(serializar_mensaje(mensaje)["leida"])

        self.client.force_login(self.interesado)
        respuesta = self.client.get(self.detalle_url(conversacion))

        self.assertContains(
            respuesta,
            'datetime="2026-11-20T10:15:00-04:00">10:15</time>',
        )
        self.assertContains(respuesta, 'data-estado="enviada"')

        mensaje.leida_en = timezone.now()
        mensaje.save(update_fields=["leida_en"])
        self.assertTrue(serializar_mensaje(mensaje)["leida"])

        respuesta = self.client.get(self.detalle_url(conversacion))
        self.assertContains(respuesta, 'data-estado="leida"')


class PruebasWebSocketContadores(TransactionTestCase):
    serialized_rollback = True

    def setUp(self):
        super().setUp()
        DatosConversaciones.setUpTestData.__func__(self.__class__)

    def test_contadores_se_actualizan_al_recibir_y_leer_un_mensaje(self):
        conversacion = Conversacion.objects.create(
            publicacion=self.publicacion,
            interesado=self.interesado,
        )
        async_to_sync(self._verificar_contadores)(conversacion.pk)

    def test_presencia_se_actualiza_desde_el_websocket_global(self):
        conversacion = Conversacion.objects.create(
            publicacion=self.publicacion,
            interesado=self.interesado,
        )
        async_to_sync(self._verificar_presencia_global)(conversacion.pk)

    async def _verificar_presencia_global(self, conversacion_id):
        chat = WebsocketCommunicator(
            URLRouter(websocket_urlpatterns),
            f"/ws/conversaciones/{conversacion_id}/",
        )
        chat.scope["user"] = self.interesado
        conectado_chat, _ = await chat.connect()
        self.assertTrue(conectado_chat)
        estado_inicial = await chat.receive_json_from(timeout=2)
        self.assertFalse(estado_inicial["en_linea"])

        global_usuario = WebsocketCommunicator(
            URLRouter(notificaciones_websocket_urlpatterns),
            "/ws/notificaciones/",
        )
        global_usuario.scope["user"] = self.publicador
        conectado_global, _ = await global_usuario.connect()
        self.assertTrue(conectado_global)
        await global_usuario.receive_json_from(timeout=2)
        await global_usuario.send_json_to(
            {
                "tipo": "presencia_suscribir",
                "usuarios": [str(self.interesado.pk)],
            }
        )
        presencia_contacto = await global_usuario.receive_json_from(timeout=2)
        self.assertEqual(presencia_contacto["tipo"], "presencia")
        self.assertEqual(presencia_contacto["usuario_id"], self.interesado.pk)
        self.assertTrue(presencia_contacto["en_linea"])

        estado_en_linea = await chat.receive_json_from(timeout=2)
        self.assertEqual(estado_en_linea["tipo"], "presencia")
        self.assertEqual(estado_en_linea["usuario_id"], self.publicador.pk)
        self.assertTrue(estado_en_linea["en_linea"])
        self.assertIsNone(estado_en_linea["segundos_desde_ultima_vez"])

        await global_usuario.disconnect()
        estado_desconectado = await chat.receive_json_from(timeout=2)
        self.assertEqual(estado_desconectado["tipo"], "presencia")
        self.assertFalse(estado_desconectado["en_linea"])
        self.assertEqual(estado_desconectado["segundos_desde_ultima_vez"], 0)
        await chat.disconnect()

    async def _verificar_contadores(self, conversacion_id):
        aplicacion = URLRouter(notificaciones_websocket_urlpatterns)
        comunicador = WebsocketCommunicator(aplicacion, "/ws/notificaciones/")
        comunicador.scope["user"] = self.publicador
        conectado, _ = await comunicador.connect()
        self.assertTrue(conectado)
        self.assertEqual(
            await comunicador.receive_json_from(timeout=2),
            {
                "tipo": "contadores",
                "chats_sin_leer": 0,
                "mensajes_por_conversacion": {},
                "notificaciones_sin_leer": 0,
            },
        )

        await database_sync_to_async(crear_mensaje)(
            conversacion_id,
            self.interesado,
            "Hola",
        )
        recibidos = await comunicador.receive_json_from(timeout=2)
        self.assertEqual(recibidos["chats_sin_leer"], 1)
        self.assertEqual(
            recibidos["mensajes_por_conversacion"],
            {str(conversacion_id): 1},
        )
        self.assertEqual(recibidos["notificaciones_sin_leer"], 1)

        await database_sync_to_async(marcar_mensajes_leidos)(
            conversacion_id,
            self.publicador.pk,
        )
        leidos = await comunicador.receive_json_from(timeout=2)
        self.assertEqual(leidos["chats_sin_leer"], 0)
        self.assertEqual(leidos["mensajes_por_conversacion"], {})
        self.assertEqual(leidos["notificaciones_sin_leer"], 0)
        await comunicador.disconnect()


class PruebasWebSocketConversaciones(DatosConversaciones, TransactionTestCase):
    serialized_rollback = True

    def setUp(self):
        super().setUp()
        DatosConversaciones.setUpTestData.__func__(self.__class__)

    @patch(
        "app.conversaciones.consumers._marcar_leido",
        new_callable=AsyncMock,
    )
    @patch(
        "app.conversaciones.consumers._crear_mensaje",
        new_callable=AsyncMock,
    )
    @patch(
        "app.conversaciones.consumers._es_participante",
        new_callable=AsyncMock,
    )
    def test_mensaje_se_transmite_al_otro_participante_en_tiempo_real(
        self,
        es_participante,
        crear,
        marcar,
    ):
        conversacion = Conversacion.objects.create(
            publicacion=self.publicacion,
            interesado=self.interesado,
        )
        async_to_sync(self._verificar_websocket)(
            conversacion.pk,
            es_participante,
            crear,
            marcar,
        )

    async def _verificar_websocket(
        self,
        conversacion_id,
        es_participante,
        crear,
        marcar,
    ):
        es_participante.side_effect = lambda id_conversacion, usuario_id: (
            id_conversacion == conversacion_id
            and usuario_id in {self.interesado.pk, self.publicador.pk}
        )
        crear.return_value = {
            "id": 987,
            "remitente_id": self.interesado.pk,
            "contenido": "Hola en vivo",
            "tipo_adjunto": "",
            "adjunto_url": "",
            "enviada_en": timezone.now().isoformat(),
            "hora_la_paz": "10:00",
        }
        remitente, destinatario, ajeno = await self._intercambiar_mensaje(
            conversacion_id
        )

        self.assertEqual(remitente["mensaje"]["contenido"], "Hola en vivo")
        self.assertEqual(remitente["mensaje"]["hora_la_paz"], "10:00")
        self.assertEqual(destinatario["mensaje"]["contenido"], "Hola en vivo")
        self.assertEqual(ajeno, (False, 4403))
        crear.assert_awaited_once()
        self.assertGreaterEqual(marcar.await_count, 3)

    async def _intercambiar_mensaje(self, conversacion_id):
        aplicacion = URLRouter(websocket_urlpatterns)
        ruta = f"/ws/conversaciones/{conversacion_id}/"
        remitente = WebsocketCommunicator(aplicacion, ruta)
        remitente.scope["user"] = self.interesado
        destinatario = WebsocketCommunicator(aplicacion, ruta)
        destinatario.scope["user"] = self.publicador
        ajeno = WebsocketCommunicator(aplicacion, ruta)
        ajeno.scope["user"] = self.ajeno

        conectado_ajeno, codigo_ajeno = await ajeno.connect()
        conectado_remitente, _ = await remitente.connect()
        conectado_destinatario, _ = await destinatario.connect()
        self.assertFalse(conectado_ajeno)
        self.assertTrue(conectado_remitente)
        self.assertTrue(conectado_destinatario)
        await remitente.receive_json_from(timeout=2)
        await destinatario.receive_json_from(timeout=2)
        await remitente.receive_json_from(timeout=2)

        await remitente.send_json_to(
            {
                "tipo": "mensaje",
                "contenido": "Hola en vivo",
                "id_cliente": "prueba-websocket",
            }
        )
        recibido_remitente = await remitente.receive_json_from(timeout=2)
        recibido_destinatario = await destinatario.receive_json_from(timeout=2)
        await remitente.disconnect()
        await destinatario.disconnect()
        return recibido_remitente, recibido_destinatario, (conectado_ajeno, codigo_ajeno)


class PruebasPresenciaChat(DatosConversaciones, TransactionTestCase):
    serialized_rollback = True

    def setUp(self):
        super().setUp()
        DatosConversaciones.setUpTestData.__func__(self.__class__)

    def test_presencia_escritura_y_ultima_conexion_en_tiempo_real(self):
        conversacion = Conversacion.objects.create(
            publicacion=self.publicacion,
            interesado=self.interesado,
        )
        async_to_sync(self._verificar_presencia)(conversacion.pk)

    def test_confirmacion_de_lectura_se_envia_al_remitente_en_tiempo_real(self):
        conversacion = Conversacion.objects.create(
            publicacion=self.publicacion,
            interesado=self.interesado,
        )
        mensaje = Mensaje.objects.create(
            conversacion=conversacion,
            remitente=self.interesado,
            contenido="Mensaje pendiente de lectura",
        )

        confirmacion = async_to_sync(self._verificar_confirmacion_lectura)(
            conversacion.pk
        )

        self.assertEqual(confirmacion["tipo"], "lectura")
        self.assertEqual(confirmacion["usuario_id"], self.publicador.pk)
        self.assertEqual(confirmacion["mensaje_ids"], [mensaje.pk])
        mensaje.refresh_from_db()
        self.assertIsNotNone(mensaje.leida_en)

    async def _verificar_confirmacion_lectura(self, conversacion_id):
        aplicacion = URLRouter(websocket_urlpatterns)
        ruta = f"/ws/conversaciones/{conversacion_id}/"
        remitente = WebsocketCommunicator(aplicacion, ruta)
        remitente.scope["user"] = self.interesado
        lector = WebsocketCommunicator(aplicacion, ruta)
        lector.scope["user"] = self.publicador

        conectado_remitente, _ = await remitente.connect()
        self.assertTrue(conectado_remitente)
        await remitente.receive_json_from(timeout=2)
        conectado_lector, _ = await lector.connect()
        self.assertTrue(conectado_lector)

        while True:
            evento = await remitente.receive_json_from(timeout=2)
            if evento["tipo"] == "lectura":
                break

        await lector.disconnect()
        await remitente.disconnect()
        return evento

    async def _verificar_presencia(self, conversacion_id):
        aplicacion = URLRouter(websocket_urlpatterns)
        ruta = f"/ws/conversaciones/{conversacion_id}/"
        publicador = WebsocketCommunicator(aplicacion, ruta)
        publicador.scope["user"] = self.publicador
        interesado = WebsocketCommunicator(aplicacion, ruta)
        interesado.scope["user"] = self.interesado

        conectado_publicador, _ = await publicador.connect()
        self.assertTrue(conectado_publicador)
        estado_inicial = await publicador.receive_json_from(timeout=2)
        self.assertEqual(estado_inicial["tipo"], "presencia")
        self.assertFalse(estado_inicial["en_linea"])

        conectado_interesado, _ = await interesado.connect()
        self.assertTrue(conectado_interesado)
        estado_publicador = await interesado.receive_json_from(timeout=2)
        estado_interesado = await publicador.receive_json_from(timeout=2)
        self.assertTrue(estado_publicador["en_linea"])
        self.assertTrue(estado_interesado["en_linea"])

        await interesado.send_json_to(
            {"tipo": "escribiendo", "escribiendo": True}
        )
        escritura = await publicador.receive_json_from(timeout=2)
        self.assertEqual(escritura["tipo"], "escribiendo")
        self.assertEqual(escritura["usuario_id"], self.interesado.pk)
        self.assertTrue(escritura["escribiendo"])

        await interesado.send_json_to(
            {"tipo": "escribiendo", "escribiendo": False}
        )
        fin_escritura = await publicador.receive_json_from(timeout=2)
        self.assertFalse(fin_escritura["escribiendo"])

        await interesado.disconnect()
        ultima_vez = await publicador.receive_json_from(timeout=2)
        self.assertEqual(ultima_vez["tipo"], "presencia")
        self.assertFalse(ultima_vez["en_linea"])
        self.assertTrue(ultima_vez["ultima_vez"])
        await publicador.disconnect()
