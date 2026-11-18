from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from .correos import ErrorEnvioCorreo, _crear_enlace, _enviar
from .models import AceptacionLegal


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PruebasCuentas(TestCase):
    def datos_registro(self):
        return {
            "first_name": "Ada",
            "last_name": "Ejemplo",
            "email": "ada@example.com",
            "telefono": "+591 70000000",
            "password": "Long-term-private-phrase-492!",
            "password_confirm": "Long-term-private-phrase-492!",
            "acepta_terminos": "on",
            "acepta_privacidad": "on",
        }

    def test_paginas_de_cuenta_usan_plantillas_organizadas(self):
        paginas = [
            "cuentas:registro",
            "cuentas:iniciar_sesion",
            "cuentas:verificacion_enviada",
            "cuentas:reenviar_verificacion",
            "cuentas:solicitar_restauracion",
            "cuentas:restauracion_solicitada",
            "cuentas:contrasena_actualizada",
            "cuentas:terminos",
            "cuentas:privacidad",
        ]

        for nombre_url in paginas:
            with self.subTest(pagina=nombre_url):
                response = self.client.get(reverse(nombre_url), HTTP_HOST="localhost")
                self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse("cuentas:verificar_correo", args=("invalid", "invalid")),
            HTTP_HOST="localhost",
        )
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, "cuentas/acceso/enlace_invalido.html")

        usuario = get_user_model().objects.create_user(
            email="ada@example.com",
            password="Long-term-private-phrase-492!",
            first_name="Ada",
            last_name="Ejemplo",
            telefono="+591 70000000",
            correo_verificado=True,
        )
        self.client.force_login(usuario)
        response = self.client.get(reverse("cuentas:panel"), HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)

    @override_settings(DEBUG=False, PUBLIC_BASE_URL="")
    def test_produccion_no_usa_el_host_de_solicitud_para_enlaces(self):
        request = RequestFactory().get("/", HTTP_HOST="localhost")

        with self.assertRaises(ErrorEnvioCorreo):
            _crear_enlace(request, "/cuentas/recuperar/")

    @override_settings(DEBUG=True, PUBLIC_BASE_URL="")
    def test_desarrollo_local_envia_texto_plano_sin_alternativa_html(self):
        _enviar(
            "Prueba de cuenta",
            "Texto de prueba.",
            "ada@example.com",
            "correos/verificacion.html",
            {
                "nombre": "Ada",
                "enlace": "http://127.0.0.1:8000/cuentas/verificar/",
            },
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].body, "Texto de prueba.")
        self.assertEqual(mail.outbox[0].alternatives, [])

    @override_settings(PUBLIC_BASE_URL="https://lotengo.example")
    def test_registro_guarda_aceptaciones_y_verifica_correo(self):
        response = self.client.post(
            reverse("cuentas:registro"),
            self.datos_registro(),
            HTTP_HOST="localhost",
        )

        self.assertRedirects(
            response,
            reverse("cuentas:verificacion_enviada"),
            fetch_redirect_response=False,
        )
        usuario = get_user_model().objects.get(email="ada@example.com")
        self.assertFalse(usuario.correo_verificado)
        self.assertTrue(usuario.check_password("Long-term-private-phrase-492!"))
        self.assertEqual(usuario.aceptaciones_legales.count(), 2)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].alternatives), 1)
        cuerpo_html = mail.outbox[0].alternatives[0][0]
        self.assertIn("Confirma tu correo electrónico", cuerpo_html)
        self.assertIn("Confirmar mi correo", cuerpo_html)
        self.assertEqual(mail.outbox[0].alternatives[0][1], "text/html")
        self.assertIn(mail.outbox[0].body.splitlines()[3], cuerpo_html)
        self.assertTrue(
            mail.outbox[0].body.splitlines()[3].startswith("https://lotengo.example/")
        )

        enlace = urlparse(mail.outbox[0].body.splitlines()[3]).path
        response = self.client.get(enlace, HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        usuario.refresh_from_db()
        self.assertTrue(usuario.correo_verificado)
        response = self.client.get(enlace, HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse("cuentas:iniciar_sesion"),
            {
                "email": "ada@example.com",
                "password": "Long-term-private-phrase-492!",
            },
            HTTP_HOST="localhost",
        )
        self.assertRedirects(
            response,
            reverse("cuentas:panel"),
            fetch_redirect_response=False,
        )

    def test_no_permite_registro_sin_aceptar_documentos(self):
        datos = self.datos_registro()
        datos.pop("acepta_terminos")
        datos.pop("acepta_privacidad")

        response = self.client.post(
            reverse("cuentas:registro"),
            datos,
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(email="ada@example.com").exists())
        self.assertEqual(AceptacionLegal.objects.count(), 0)

    @override_settings(PUBLIC_BASE_URL="https://lotengo.example")
    def test_reenviar_verificacion_usa_el_correo_de_verificacion(self):
        usuario = get_user_model().objects.create_user(
            email="ada@example.com",
            password="Long-term-private-phrase-492!",
            first_name="Ada",
            last_name="Ejemplo",
            telefono="+591 70000000",
        )

        response = self.client.post(
            reverse("cuentas:reenviar_verificacion"),
            {"email": usuario.email},
            HTTP_HOST="localhost",
        )

        self.assertRedirects(
            response,
            reverse("cuentas:verificacion_enviada"),
            fetch_redirect_response=False,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [usuario.email])
        self.assertIn("Verifica tu correo de Lotengo", mail.outbox[0].subject)
        self.assertIn(
            "Confirma tu correo electrónico",
            mail.outbox[0].alternatives[0][0],
        )

    @override_settings(PUBLIC_BASE_URL="https://lotengo.example")
    def test_inicio_de_sesion_requiere_correo_verificado(self):
        self.client.post(
            reverse("cuentas:registro"),
            self.datos_registro(),
            HTTP_HOST="localhost",
        )

        response = self.client.post(
            reverse("cuentas:iniciar_sesion"),
            {
                "email": "ada@example.com",
                "password": "Long-term-private-phrase-492!",
            },
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verifica tu correo")
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(PUBLIC_BASE_URL="https://lotengo.example")
    def test_restauracion_cambia_contrasena_con_token_valido(self):
        usuario = get_user_model().objects.create_user(
            email="ada@example.com",
            password="Original-password-492!",
            first_name="Ada",
            last_name="Ejemplo",
            telefono="+591 70000000",
            correo_verificado=True,
        )
        self.client.post(
            reverse("cuentas:solicitar_restauracion"),
            {"email": usuario.email},
            HTTP_HOST="localhost",
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].alternatives), 1)
        cuerpo_html = mail.outbox[0].alternatives[0][0]
        self.assertIn("Solicitaste cambiar tu contraseña", cuerpo_html)
        self.assertIn("Crear una contraseña nueva", cuerpo_html)
        self.assertEqual(mail.outbox[0].alternatives[0][1], "text/html")
        self.assertIn(mail.outbox[0].body.splitlines()[3], cuerpo_html)

        enlace = urlparse(mail.outbox[0].body.splitlines()[3]).path
        response = self.client.get(enlace, HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            enlace,
            {
                "password": "Replacement-password-639!",
                "password_confirm": "Replacement-password-639!",
            },
            HTTP_HOST="localhost",
        )

        self.assertRedirects(
            response,
            reverse("cuentas:contrasena_actualizada"),
            fetch_redirect_response=False,
        )
        usuario.refresh_from_db()
        self.assertTrue(usuario.check_password("Replacement-password-639!"))
        self.assertFalse(usuario.check_password("Original-password-492!"))

    def test_cierre_de_sesion_solo_acepta_post(self):
        usuario = get_user_model().objects.create_user(
            email="ada@example.com",
            password="Original-password-492!",
            first_name="Ada",
            last_name="Ejemplo",
            telefono="+591 70000000",
            correo_verificado=True,
        )
        self.client.force_login(usuario)

        response = self.client.get(
            reverse("cuentas:cerrar_sesion"),
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)
