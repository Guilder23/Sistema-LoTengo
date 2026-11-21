from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from app.categorias.models import Categoria
from app.conversaciones.models import Conversacion, Mensaje
from app.geografia.models import Departamento, Municipio
from app.moderacion.models import DecisionModeracion
from app.publicaciones.models import Publicacion
from app.ubicaciones.models import Ubicacion

from .models import BloqueoUsuario, Denuncia
from .views import descargar_evidencia
from app.conversaciones.services import ErrorMensaje, crear_mensaje


class PruebasDenunciasYModeracion(TestCase):
    @classmethod
    def setUpTestData(cls):
        usuarios = get_user_model()
        cls.denunciante = usuarios.objects.create_user(
            email="denunciante@example.com",
            password="Secure-test-password-872!",
            first_name="Ana",
            telefono="+591 70000020",
            correo_verificado=True,
        )
        cls.publicador = usuarios.objects.create_user(
            email="publicador@example.com",
            password="Secure-test-password-873!",
            first_name="Luis",
            telefono="+591 70000021",
            correo_verificado=True,
        )
        cls.moderador = usuarios.objects.create_user(
            email="moderador@example.com",
            password="Secure-test-password-874!",
            first_name="Eva",
            telefono="+591 70000022",
            correo_verificado=True,
            is_staff=True,
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
        )
        cls.publicacion = Publicacion.objects.create(
            usuario=cls.publicador,
            categoria=categoria,
            ubicacion=ubicacion,
            tipo=Publicacion.Tipo.PERDIDO,
            titulo="Teléfono azul",
            descripcion="Teléfono perdido en el centro.",
            fecha_evento=timezone.localdate() - timedelta(days=1),
        )

    def crear_denuncia(self):
        return Denuncia.objects.create(
            denunciante=self.denunciante,
            denunciado=self.publicador,
            publicacion=self.publicacion,
            motivo=Denuncia.Motivo.PUBLICACION_FALSA,
            descripcion="La publicación incluye información falsa.",
        )

    def test_denuncia_se_envia_y_el_denunciante_consulta_estado(self):
        self.client.force_login(self.denunciante)

        respuesta = self.client.post(
            f"{reverse('denuncias:crear')}?publicacion={self.publicacion.pk}",
            {
                "publicacion": str(self.publicacion.pk),
                "motivo": Denuncia.Motivo.ESTAFA,
                "descripcion": "El aviso intenta obtener pagos por adelantado.",
            },
        )

        self.assertRedirects(respuesta, reverse("denuncias:mis_denuncias"))
        denuncia = Denuncia.objects.get(denunciante=self.denunciante)
        self.assertEqual(denuncia.publicacion, self.publicacion)
        self.assertEqual(denuncia.denunciado, self.publicador)
        self.assertContains(self.client.get(reverse("denuncias:mis_denuncias")), "Pendiente")

    def test_solo_personal_puede_moderar_y_decision_oculta_publicacion(self):
        denuncia = self.crear_denuncia()
        respuesta = self.client.get(reverse("moderacion:bandeja"))
        self.assertEqual(respuesta.status_code, 302)

        self.client.force_login(self.moderador)
        respuesta = self.client.get(reverse("moderacion:bandeja"))
        self.assertContains(respuesta, 'id="barraLateralCuenta"')
        self.assertContains(respuesta, "Moderación")

        respuesta = self.client.post(
            reverse("moderacion:decidir", args=(denuncia.pk,)),
            {
                "accion": DecisionModeracion.Accion.OCULTAR_PUBLICACION,
                "nota": "Se ocultó mientras se verifica la información.",
            },
        )

        self.assertRedirects(respuesta, reverse("moderacion:bandeja"))
        self.publicacion.refresh_from_db()
        denuncia.refresh_from_db()
        self.assertTrue(self.publicacion.oculta_por_moderacion)
        self.assertEqual(denuncia.estado, Denuncia.Estado.EN_REVISION)
        self.assertEqual(denuncia.decisiones.count(), 1)

    def test_bloqueo_impide_enviar_mensajes(self):
        conversacion = Conversacion.objects.create(
            publicacion=self.publicacion,
            interesado=self.denunciante,
        )
        BloqueoUsuario.objects.create(
            bloqueador=self.denunciante,
            bloqueado=self.publicador,
        )

        with self.assertRaises(ErrorMensaje):
            crear_mensaje(conversacion.pk, self.denunciante, "Hola")

    def test_denuncia_mensaje_permite_reportar_al_otro_participante(self):
        conversacion = Conversacion.objects.create(
            publicacion=self.publicacion,
            interesado=self.denunciante,
        )
        mensaje = Mensaje.objects.create(
            conversacion=conversacion,
            remitente=self.denunciante,
            contenido="Mensaje inapropiado",
        )
        self.client.force_login(self.publicador)

        respuesta = self.client.post(
            f"{reverse('denuncias:crear')}?mensaje={mensaje.pk}",
            {
                "mensaje": str(mensaje.pk),
                "publicacion": str(self.publicacion.pk),
                "usuario": str(self.denunciante.pk),
                "motivo": Denuncia.Motivo.MENSAJE_INAPROPIADO,
                "descripcion": "El mensaje contiene lenguaje ofensivo.",
            },
        )

        self.assertRedirects(respuesta, reverse("denuncias:mis_denuncias"))
        denuncia = Denuncia.objects.get(denunciante=self.publicador)
        self.assertEqual(denuncia.mensaje, mensaje)
        self.assertEqual(denuncia.denunciado, self.denunciante)

    def test_suspension_temporal_registra_duracion_y_bloquea_acceso(self):
        denuncia = self.crear_denuncia()
        self.client.force_login(self.moderador)

        respuesta = self.client.post(
            reverse("moderacion:decidir", args=(denuncia.pk,)),
            {
                "accion": DecisionModeracion.Accion.SUSPENDER_USUARIO,
                "dias": "3",
                "nota": "Suspensión temporal por infracción confirmada.",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        decision = DecisionModeracion.objects.get(denuncia=denuncia)
        self.assertEqual(decision.duracion_dias, 3)
        self.publicador.refresh_from_db()
        self.assertGreater(self.publicador.suspendido_hasta, timezone.now())
        self.client.logout()
        self.assertFalse(
            self.client.login(
                email="publicador@example.com",
                password="Secure-test-password-873!",
            )
        )

    def test_evidencia_es_privada_y_solo_la_ven_denunciante_o_personal(self):
        imagen = BytesIO()
        Image.new("RGB", (4, 4), color="red").save(imagen, format="JPEG")
        evidencia = SimpleUploadedFile(
            "captura.jpg",
            imagen.getvalue(),
            content_type="image/jpeg",
        )

        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                self.client.force_login(self.denunciante)
                respuesta = self.client.post(
                    f"{reverse('denuncias:crear')}?publicacion={self.publicacion.pk}",
                    {
                        "motivo": Denuncia.Motivo.PUBLICACION_FALSA,
                        "descripcion": "La información no coincide con lo ocurrido.",
                        "evidencia": evidencia,
                    },
                )
                self.assertEqual(respuesta.status_code, 302)
                denuncia = Denuncia.objects.get(denunciante=self.denunciante)
                url_evidencia = reverse(
                    "denuncias:evidencia",
                    args=(denuncia.pk,),
                )

                solicitud = RequestFactory().get(url_evidencia)
                solicitud.user = self.denunciante
                respuesta = descargar_evidencia(solicitud, denuncia.pk)
                self.assertEqual(respuesta.status_code, 200)
                respuesta.file_to_stream.close()
                solicitud.user = self.publicador
                with self.assertRaises(Http404):
                    descargar_evidencia(solicitud, denuncia.pk)
                solicitud.user = self.moderador
                respuesta = descargar_evidencia(solicitud, denuncia.pk)
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta["Cache-Control"], "private, no-store")
                respuesta.file_to_stream.close()
