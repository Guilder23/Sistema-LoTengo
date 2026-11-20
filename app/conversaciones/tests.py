from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory

from asgiref.sync import async_to_sync
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from unittest.mock import AsyncMock, patch

from app.categorias.models import Categoria
from app.geografia.models import Departamento, Municipio
from app.publicaciones.models import Publicacion
from app.ubicaciones.models import Ubicacion

from .models import Conversacion, Mensaje
from .routing import websocket_urlpatterns


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
        self.assertNotContains(response, self.publicador.email)
        self.assertNotContains(response, self.publicador.telefono)

        response = self.client.post(
            self.detalle_url(conversacion),
            {"contenido": "Hola, creo que encontré este teléfono."},
        )
        self.assertRedirects(response, self.detalle_url(conversacion))
        mensaje = Mensaje.objects.get(conversacion=conversacion)
        self.assertEqual(mensaje.remitente, self.interesado)

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


class PruebasWebSocketConversaciones(DatosConversaciones, TestCase):
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
        }
        remitente, destinatario, ajeno = await self._intercambiar_mensaje(
            conversacion_id
        )

        self.assertEqual(remitente["mensaje"]["contenido"], "Hola en vivo")
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
