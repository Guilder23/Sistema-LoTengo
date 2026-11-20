from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Perfil


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    PUBLIC_BASE_URL="https://lotengo.example",
)
class PruebasPerfil(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            email="perfil@example.com",
            password="Secure-profile-password-951!",
            first_name="Ada",
            last_name="Ejemplo",
            telefono="+591 70000010",
            correo_verificado=True,
        )

    def datos_perfil(self, **cambios):
        datos = {
            "first_name": "Ada",
            "last_name": "Ejemplo",
            "email": self.usuario.email,
            "telefono": "+591 70000010",
        }
        datos.update(cambios)
        return datos

    def crear_foto(self):
        contenido = BytesIO()
        Image.new("RGB", (40, 40), color="blue").save(contenido, format="JPEG")
        return SimpleUploadedFile(
            "foto.jpg",
            contenido.getvalue(),
            content_type="image/jpeg",
        )

    def test_perfil_requiere_autenticacion_y_muestra_formulario(self):
        url = reverse("perfiles:editar")

        anonimo = self.client.get(url)
        self.assertEqual(anonimo.status_code, 302)

        self.client.force_login(self.usuario)
        respuesta = self.client.get(url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, "perfiles/editar.html")
        self.assertContains(respuesta, 'enctype="multipart/form-data"')
        self.assertContains(respuesta, "data-perfil-foto")
        self.assertTrue(Perfil.objects.filter(usuario=self.usuario).exists())

    def test_actualiza_datos_y_foto_y_verifica_el_correo_nuevo(self):
        self.client.force_login(self.usuario)
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                respuesta = self.client.post(
                    reverse("perfiles:editar"),
                    self.datos_perfil(
                        first_name="Ada María",
                        telefono="+591 70000011",
                        email="ada.nueva@example.com",
                        foto=self.crear_foto(),
                    ),
                    follow=True,
                )

                self.assertEqual(respuesta.status_code, 200)
                self.assertRedirects(
                    respuesta,
                    reverse("cuentas:verificacion_enviada"),
                )
                self.usuario.refresh_from_db()
                perfil = Perfil.objects.get(usuario=self.usuario)

                self.assertEqual(self.usuario.first_name, "Ada María")
                self.assertEqual(self.usuario.telefono, "+591 70000011")
                self.assertEqual(self.usuario.email, "ada.nueva@example.com")
                self.assertFalse(self.usuario.correo_verificado)
                self.assertTrue(perfil.foto)
                self.assertTrue(Path(media_root, perfil.foto.name).is_file())
                self.assertEqual(len(mail.outbox), 1)

    def test_quitar_foto_elimina_el_archivo_guardado(self):
        self.client.force_login(self.usuario)
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                self.client.post(
                    reverse("perfiles:editar"),
                    self.datos_perfil(foto=self.crear_foto()),
                )
                perfil = Perfil.objects.get(usuario=self.usuario)
                ruta_foto = Path(media_root, perfil.foto.name)
                self.assertTrue(ruta_foto.is_file())

                respuesta = self.client.post(
                    reverse("perfiles:editar"),
                    self.datos_perfil(eliminar_foto="on"),
                )

                self.assertEqual(respuesta.status_code, 302)
                perfil.refresh_from_db()
                self.assertFalse(perfil.foto)
                self.assertFalse(ruta_foto.exists())

    def test_rechaza_un_archivo_que_no_es_una_imagen(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(
            reverse("perfiles:editar"),
            self.datos_perfil(
                first_name="No debe guardarse",
                foto=SimpleUploadedFile(
                    "not-image.txt",
                    b"not an image",
                    content_type="text/plain",
                ),
            ),
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "No se pudo validar la fotografía.")
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.first_name, "Ada")
        self.assertFalse(Perfil.objects.get(usuario=self.usuario).foto)
