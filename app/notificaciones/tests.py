import json

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Notificacion, PreferenciaNotificaciones, SuscripcionPush


class PruebasNotificaciones(TestCase):
    @classmethod
    def setUpTestData(cls):
        usuario = get_user_model()
        cls.persona = usuario.objects.create_user(
            email="notificaciones@example.com",
            password="Secure-test-password-901!",
            first_name="Persona",
            last_name="Notificada",
            telefono="+591 70000090",
            correo_verificado=True,
        )
        cls.otra_persona = usuario.objects.create_user(
            email="otra-notificaciones@example.com",
            password="Secure-test-password-902!",
            first_name="Otra",
            last_name="Persona",
            telefono="+591 70000091",
            correo_verificado=True,
        )

    def test_bandeja_y_resumen_solo_muestran_notificaciones_propias(self):
        propia = Notificacion.objects.create(
            usuario=self.persona,
            tipo=Notificacion.Tipo.MENSAJE,
            titulo="Nuevo mensaje",
            mensaje="Recibiste un mensaje.",
            url="/conversaciones/1/",
        )
        Notificacion.objects.create(
            usuario=self.otra_persona,
            tipo=Notificacion.Tipo.MENSAJE,
            titulo="Mensaje privado",
            mensaje="Contenido de otra cuenta.",
            url="/conversaciones/2/",
        )
        self.client.force_login(self.persona)

        respuesta = self.client.get(reverse("notificaciones:resumen"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["sin_leer"], 1)
        self.assertEqual(len(respuesta.json()["notificaciones"]), 1)
        self.assertEqual(
            respuesta.json()["notificaciones"][0]["url"],
            reverse("notificaciones:abrir", args=(propia.pk,)),
        )
        self.assertEqual(self.client.get(reverse("notificaciones:lista")).status_code, 200)

    def test_abrir_marca_leida_y_no_permite_acceso_a_otra_cuenta(self):
        notificacion = Notificacion.objects.create(
            usuario=self.persona,
            tipo=Notificacion.Tipo.NUEVA_PUBLICACION,
            titulo="Nueva publicación",
            mensaje="Mochila roja · Cochabamba",
            url="/publicaciones/12/",
        )
        self.client.force_login(self.otra_persona)

        ajena = self.client.get(
            reverse("notificaciones:abrir", args=(notificacion.pk,))
        )

        self.assertEqual(ajena.status_code, 404)
        self.client.force_login(self.persona)
        propia = self.client.get(
            reverse("notificaciones:abrir", args=(notificacion.pk,))
        )

        self.assertRedirects(propia, "/publicaciones/12/", fetch_redirect_response=False)
        notificacion.refresh_from_db()
        self.assertIsNotNone(notificacion.leida_en)

    def test_preferencia_de_publicaciones_es_opt_in_y_se_puede_desactivar(self):
        self.client.force_login(self.persona)
        preferencia = PreferenciaNotificaciones.objects.create(usuario=self.persona)
        self.assertFalse(preferencia.nuevas_publicaciones)

        respuesta = self.client.post(
            reverse("notificaciones:preferencias"),
            {"nuevas_publicaciones": "on"},
        )

        self.assertRedirects(respuesta, reverse("notificaciones:lista"))
        preferencia.refresh_from_db()
        self.assertTrue(preferencia.nuevas_publicaciones)

        self.client.post(reverse("notificaciones:preferencias"), {})
        preferencia.refresh_from_db()
        self.assertFalse(preferencia.nuevas_publicaciones)

    @override_settings(
        WEBPUSH_VAPID_PUBLIC_KEY="public-key",
        WEBPUSH_VAPID_PRIVATE_KEY="private-key.pem",
        WEBPUSH_VAPID_SUBJECT="mailto:admin@lotengo.app",
    )
    def test_suscripcion_push_valida_y_no_permite_reutilizar_dispositivo_ajeno(self):
        self.client.force_login(self.persona)
        datos = {
            "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint",
            "keys": {"p256dh": "publicKey_123", "auth": "authKey_456"},
        }

        respuesta = self.client.post(
            reverse("notificaciones:registrar_suscripcion"),
            data=json.dumps(datos),
            content_type="application/json",
        )

        self.assertEqual(respuesta.status_code, 201)
        suscripcion = SuscripcionPush.objects.get()
        self.assertEqual(suscripcion.usuario, self.persona)

        self.client.force_login(self.otra_persona)
        reutilizada = self.client.post(
            reverse("notificaciones:registrar_suscripcion"),
            data=json.dumps(datos),
            content_type="application/json",
        )
        datos["endpoint"] = "http://127.0.0.1:8000/interno"
        insegura = self.client.post(
            reverse("notificaciones:registrar_suscripcion"),
            data=json.dumps(datos),
            content_type="application/json",
        )

        self.assertEqual(reutilizada.status_code, 409)
        self.assertEqual(insegura.status_code, 400)
        self.assertEqual(SuscripcionPush.objects.count(), 1)

    def test_service_worker_tiene_alcance_de_raiz(self):
        respuesta = self.client.get(reverse("service_worker"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Service-Worker-Allowed"], "/")
        self.assertContains(respuesta, 'addEventListener("push"')

    def test_cerrar_sesion_desvincula_el_dispositivo_actual(self):
        SuscripcionPush.objects.create(
            usuario=self.persona,
            endpoint="https://fcm.googleapis.com/fcm/send/push-token",
            clave_publica="publicKey_123",
            clave_auth="authKey_456",
        )
        self.client.force_login(self.persona)

        respuesta = self.client.post(
            reverse("cuentas:cerrar_sesion"),
            {"push_endpoint": "https://fcm.googleapis.com/fcm/send/push-token"},
        )

        self.assertRedirects(respuesta, reverse("general:inicio"))
        self.assertFalse(SuscripcionPush.objects.exists())
