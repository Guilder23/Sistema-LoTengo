from datetime import timedelta
from io import BytesIO
import re
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from app.categorias.models import Categoria
from app.geografia.models import Departamento, Municipio
from app.notificaciones.models import Notificacion, PreferenciaNotificaciones
from app.perfiles.models import Perfil
from app.ubicaciones.models import Ubicacion

from .imagenes import ErrorImagen, TAMANO_MAXIMO_IMAGEN, preparar_imagen
from .models import ImagenPublicacion, Publicacion


class PruebasPublicaciones(TestCase):
    @classmethod
    def setUpTestData(cls):
        usuario = get_user_model()
        cls.propietario = usuario.objects.create_user(
            email="ana@example.com",
            password="Long-term-private-phrase-492!",
            first_name="Ana",
            last_name="Ejemplo",
            telefono="+591 70000000",
            correo_verificado=True,
        )
        cls.otro_usuario = usuario.objects.create_user(
            email="luis@example.com",
            password="Long-term-private-phrase-493!",
            first_name="Luis",
            last_name="Ejemplo",
            telefono="+591 70000001",
            correo_verificado=True,
        )
        cls.categoria = Categoria.objects.get(slug="celulares-dispositivos-electronicos")
        cls.departamento = Departamento.objects.get(codigo="cochabamba")
        cls.municipio = Municipio.objects.get(
            departamento=cls.departamento,
            nombre="Cochabamba",
        )
        cls.ubicacion = Ubicacion.objects.create(
            departamento=cls.departamento,
            municipio=cls.municipio,
            zona="Centro",
            conoce_lugar_exacto=True,
            referencia_privada="En la entrada norte",
        )

    def crear_publicacion(self, **cambios):
        datos = {
            "usuario": self.propietario,
            "categoria": self.categoria,
            "ubicacion": self.ubicacion,
            "tipo": Publicacion.Tipo.PERDIDO,
            "titulo": "Celular negro",
            "descripcion": "Celular perdido en la zona central.",
            "marca": "Samsung",
            "color": "Negro",
            "caracteristicas_publicas": "Tiene funda oscura.",
            "caracteristica_privada": "Tiene una calcomanía debajo de la funda.",
            "fecha_evento": timezone.localdate() - timedelta(days=1),
        }
        datos.update(cambios)
        return Publicacion.objects.create(**datos)

    def datos_formulario(self):
        return {
            "tipo": "perdido",
            "categoria": str(self.categoria.pk),
            "titulo": "Billetera azul",
            "descripcion": "Billetera perdida cerca del mercado.",
            "marca": "",
            "color": "Azul",
            "caracteristicas_publicas": "",
            "caracteristica_privada": "",
            "fecha_evento": (timezone.localdate() - timedelta(days=1)).isoformat(),
            "departamento": self.departamento.codigo,
            "municipio": "Cochabamba",
            "zona": "Centro",
            "conoce_lugar_exacto": "on",
            "referencia_privada": "Cerca de la entrada norte",
        }

    def test_municipios_corresponden_al_departamento_seleccionado(self):
        response = self.client.get(
            reverse("publicaciones:municipios_por_departamento"),
            {"departamento": self.departamento.codigo},
        )

        self.assertEqual(response.status_code, 200)
        municipios = response.json()["municipios"]
        self.assertIn("Cochabamba", municipios)
        self.assertIn("Sacaba", municipios)
        self.assertNotIn("Trinidad", municipios)
        self.assertTrue(
            Municipio.objects.filter(
                departamento=self.departamento,
                nombre="Cochabamba",
            ).exists()
        )

    def test_listado_filtra_por_busqueda_tipo_y_municipio(self):
        encontrada = self.crear_publicacion(
            tipo=Publicacion.Tipo.ENCONTRADO,
            titulo="Mochila roja encontrada",
        )
        response = self.client.get(
            reverse("publicaciones:listado"),
            {"q": "mochila", "tipo": "encontrado", "municipio": "cochabamba"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "general/publicaciones.html")
        self.assertNotContains(response, 'class="cuenta-sidebar"', html=False)
        self.assertNotContains(response, 'class="navbar-notificaciones-boton"', html=False)
        self.assertContains(response, "marketplace-page", html=False)
        self.assertContains(response, 'class="marketplace-card"', html=False)
        self.assertContains(response, 'role="combobox"', html=False)
        self.assertNotContains(response, '<table class="tabla-publicaciones">', html=False)
        self.assertContains(response, encontrada.titulo)
        self.assertNotContains(response, "Celular negro")

    def test_publico_no_ve_referencias_ni_dato_privado(self):
        publicacion = self.crear_publicacion()
        Perfil.objects.create(
            usuario=self.propietario,
            foto="perfiles/fotos/ana-publicadora.jpg",
        )

        response = self.client.get(
            reverse("publicaciones:detalle", args=[publicacion.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "general/detalle_publicacion.html")
        self.assertNotContains(response, 'class="cuenta-sidebar"', html=False)
        self.assertContains(response, 'class="marketplace-sidebar"', html=False)
        self.assertNotContains(response, "entrada norte")
        self.assertNotContains(response, "calcomanía debajo")
        self.assertNotContains(response, self.propietario.email)
        self.assertContains(response, "Ana Ejemplo")
        self.assertContains(response, "/media/perfiles/fotos/ana-publicadora.jpg")
        self.assertContains(response, reverse("perfiles:publico", args=[self.propietario.pk]))
        self.assertContains(response, "Inicia sesión para contactar")
        publicador = response.content.find(b"publicacion-detalle-contacto-publicador")
        boton = response.content.find(b"publicacion-detalle-boton")
        self.assertGreaterEqual(publicador, 0)
        self.assertGreater(boton, publicador)

    def test_perfil_publico_muestra_datos_y_publicaciones_del_autor(self):
        activa = self.crear_publicacion(titulo="Mochila publicada")
        self.crear_publicacion(
            titulo="Mochila pausada",
            estado=Publicacion.Estado.PAUSADA,
        )
        Perfil.objects.create(
            usuario=self.propietario,
            foto="perfiles/fotos/ana-publicadora.jpg",
        )

        response = self.client.get(
            reverse("perfiles:publico", args=[self.propietario.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "perfiles/publico.html")
        self.assertContains(response, "Ana Ejemplo")
        self.assertContains(response, "/media/perfiles/fotos/ana-publicadora.jpg")
        self.assertContains(response, activa.titulo)
        self.assertNotContains(response, "Mochila pausada")
        self.assertNotContains(response, self.propietario.email)

    def test_propietario_ve_sus_datos_privados_y_estado(self):
        publicacion = self.crear_publicacion()
        self.client.force_login(self.propietario)

        response = self.client.get(
            reverse("publicaciones:detalle", args=[publicacion.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="cuenta-sidebar"', html=False)
        self.assertContains(response, "calcomanía debajo")
        self.assertContains(response, "entrada norte")
        self.assertNotContains(response, "Contactar por mensaje")

    def test_paginas_de_creacion_edicion_y_gestion_renderizan(self):
        publicacion = self.crear_publicacion()
        self.client.force_login(self.propietario)

        for url in (
            reverse("publicaciones:crear"),
            reverse("publicaciones:editar", args=[publicacion.pk]),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'class="cuenta-sidebar"', html=False)
                self.assertContains(response, 'data-progreso-formulario', html=False)

        response = self.client.get(reverse("publicaciones:mis_publicaciones"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="cuenta-sidebar"', html=False)
        self.assertTemplateUsed(response, "publicaciones/publicaciones.html")
        self.assertContains(response, '<table class="tabla-publicaciones">', html=False)
        self.assertContains(response, reverse("publicaciones:eliminar", args=[publicacion.pk]))
        self.assertContains(response, "Acciones")
        self.assertContains(response, 'class="icono-accion"', html=False)

    def test_creacion_solicita_tipo_antes_de_mostrar_el_formulario(self):
        self.client.force_login(self.propietario)

        selector = self.client.get(reverse("publicaciones:crear"))
        formulario = self.client.get(
            reverse("publicaciones:crear"),
            {"tipo": Publicacion.Tipo.ENCONTRADO},
        )

        self.assertEqual(selector.status_code, 200)
        self.assertFalse(selector.context["mostrar_formulario"])
        self.assertContains(selector, "¿Qué ocurrió con el objeto?")
        self.assertContains(selector, "data-formulario-publicacion hidden", html=False)
        self.assertContains(selector, 'data-paso-formulario="paso-objeto"', html=False)
        self.assertContains(selector, "data-campo-contador", html=False)
        self.assertEqual(formulario.status_code, 200)
        self.assertTrue(formulario.context["mostrar_formulario"])
        self.assertContains(formulario, 'value="encontrado" data-tipo-publicacion-input', html=False)

    def test_edicion_conserva_fotografia_marcada_si_hay_errores(self):
        publicacion = self.crear_publicacion()
        buffer = BytesIO()
        Image.new("RGB", (20, 20), color="blue").save(buffer, format="PNG")
        self.client.force_login(self.propietario)

        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                fotografia = ImagenPublicacion.objects.create(
                    publicacion=publicacion,
                    archivo=SimpleUploadedFile(
                        "foto.png",
                        buffer.getvalue(),
                        content_type="image/png",
                    ),
                )
                datos = self.datos_formulario()
                datos["titulo"] = ""
                datos["eliminar_imagenes"] = [str(fotografia.pk)]
                response = self.client.post(
                    reverse("publicaciones:editar", args=[publicacion.pk]),
                    datos,
                )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'value="{fotografia.pk}" checked',
            html=False,
        )

    def test_inicio_muestra_marketplace_con_avisos_recientes_y_filtros(self):
        publicacion = self.crear_publicacion()

        response = self.client.get(reverse("general:inicio"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="navbar-notificaciones-boton"', html=False)
        self.assertContains(response, "marketplace-page", html=False)
        self.assertContains(response, 'class="marketplace-card"', html=False)
        self.assertContains(response, "Categorías")
        self.assertContains(response, "Todos los departamentos")
        self.assertContains(response, publicacion.titulo)
        self.assertNotContains(response, publicacion.caracteristica_privada)
        self.assertContains(
            response,
            reverse("publicaciones:detalle", args=[publicacion.pk]),
        )

    def test_creacion_requiere_sesion_y_guarda_usuario_autenticado(self):
        url = reverse("publicaciones:crear")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("next=", response["Location"])

        self.client.force_login(self.propietario)
        response = self.client.post(url, self.datos_formulario())

        self.assertEqual(response.status_code, 302)
        publicacion = Publicacion.objects.get(titulo="Billetera azul")
        self.assertRedirects(
            response,
            reverse("publicaciones:detalle", args=[publicacion.pk]),
            fetch_redirect_response=False,
        )
        self.assertEqual(publicacion.usuario, self.propietario)
        self.assertEqual(publicacion.ubicacion.referencia_privada, "Cerca de la entrada norte")

    def test_nueva_publicacion_avisa_solo_a_cuentas_opt_in_y_no_repite_al_editar(self):
        PreferenciaNotificaciones.objects.create(
            usuario=self.otro_usuario,
            nuevas_publicaciones=True,
        )
        self.client.force_login(self.propietario)

        respuesta = self.client.post(
            reverse("publicaciones:crear"),
            self.datos_formulario(),
        )
        publicacion = Publicacion.objects.get(titulo="Billetera azul")
        notificacion = Notificacion.objects.get()

        self.assertRedirects(
            respuesta,
            reverse("publicaciones:detalle", args=[publicacion.pk]),
            fetch_redirect_response=False,
        )
        self.assertEqual(notificacion.usuario, self.otro_usuario)
        self.assertEqual(notificacion.tipo, Notificacion.Tipo.NUEVA_PUBLICACION)
        self.assertEqual(notificacion.url, reverse("publicaciones:detalle", args=[publicacion.pk]))
        self.assertFalse(
            Notificacion.objects.filter(usuario=self.propietario).exists()
        )

        datos = self.datos_formulario()
        datos["titulo"] = "Billetera azul editada"
        self.client.post(
            reverse("publicaciones:editar", args=[publicacion.pk]),
            datos,
        )
        self.assertEqual(Notificacion.objects.count(), 1)

    def test_creacion_guarda_fotografia_validada_con_nombre_aleatorio(self):
        self.client.force_login(self.propietario)
        buffer = BytesIO()
        Image.new("RGB", (20, 20), color="blue").save(buffer, format="PNG")
        archivo = SimpleUploadedFile(
            "mi-carnet.png",
            buffer.getvalue(),
            content_type="image/png",
        )

        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse("publicaciones:crear"),
                    {**self.datos_formulario(), "imagenes": [archivo]},
                )
                publicacion = Publicacion.objects.get(titulo="Billetera azul")
                fotografia = ImagenPublicacion.objects.get(publicacion=publicacion)

                self.assertRedirects(
                    response,
                    reverse("publicaciones:detalle", args=[publicacion.pk]),
                    fetch_redirect_response=False,
                )
                self.assertRegex(
                    fotografia.archivo.name,
                    rf"^publicaciones/{publicacion.pk}/[0-9a-f]{{32}}\.png$",
                )
                self.assertTrue(fotografia.archivo.storage.exists(fotografia.archivo.name))

    def test_usuario_no_puede_editar_ni_cambiar_estado_de_otro(self):
        publicacion = self.crear_publicacion()
        self.client.force_login(self.otro_usuario)

        editar = self.client.get(
            reverse("publicaciones:editar", args=[publicacion.pk])
        )
        estado = self.client.post(
            reverse("publicaciones:cambiar_estado", args=[publicacion.pk]),
            {"accion": "pausar"},
        )

        self.assertEqual(editar.status_code, 404)
        self.assertEqual(estado.status_code, 404)
        publicacion.refresh_from_db()
        self.assertEqual(publicacion.estado, Publicacion.Estado.PUBLICADA)

    def test_pausar_oculta_publicacion_del_listado_publico(self):
        publicacion = self.crear_publicacion()
        self.client.force_login(self.propietario)
        response = self.client.post(
            reverse("publicaciones:cambiar_estado", args=[publicacion.pk]),
            {"accion": "pausar"},
        )

        self.assertRedirects(response, reverse("publicaciones:mis_publicaciones"))
        publicacion.refresh_from_db()
        self.assertEqual(publicacion.estado, Publicacion.Estado.PAUSADA)
        self.assertEqual(
            self.client.get(reverse("publicaciones:listado")).context["pagina"].paginator.count,
            0,
        )

    def test_eliminar_retiro_logico_oculta_publicacion_y_conserva_registro(self):
        publicacion = self.crear_publicacion()
        self.client.force_login(self.propietario)
        url = reverse("publicaciones:eliminar", args=[publicacion.pk])

        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, 200)
        self.assertTemplateUsed(get_response, "publicaciones/crud/eliminar.html")
        self.assertContains(get_response, 'class="cuenta-sidebar"', html=False)

        response = self.client.post(url)

        self.assertRedirects(response, reverse("publicaciones:mis_publicaciones"))
        publicacion.refresh_from_db()
        self.assertEqual(publicacion.estado, Publicacion.Estado.ELIMINADA)
        self.assertIsNotNone(publicacion.eliminada_en)
        self.assertEqual(
            Publicacion.objects.filter(pk=publicacion.pk).count(),
            1,
        )
        self.assertEqual(
            self.client.get(reverse("publicaciones:mis_publicaciones"))
            .context["pagina"]
            .paginator.count,
            0,
        )
        self.assertEqual(
            self.client.get(reverse("publicaciones:listado")).context["pagina"].paginator.count,
            0,
        )

    def test_usuario_no_puede_eliminar_publicacion_ajena(self):
        publicacion = self.crear_publicacion()
        self.client.force_login(self.otro_usuario)

        response = self.client.post(
            reverse("publicaciones:eliminar", args=[publicacion.pk])
        )

        self.assertEqual(response.status_code, 404)
        publicacion.refresh_from_db()
        self.assertEqual(publicacion.estado, Publicacion.Estado.PUBLICADA)


class PruebasImagenesPublicacion(TestCase):
    def test_rechaza_archivo_superior_al_limite(self):
        archivo = SimpleUploadedFile(
            "imagen.jpg",
            b"x" * (TAMANO_MAXIMO_IMAGEN + 1),
            content_type="image/jpeg",
        )

        with self.assertRaises(ErrorImagen):
            preparar_imagen(archivo)

    def test_normaliza_nombre_y_elimina_metadatos_exif(self):
        buffer = BytesIO()
        imagen = Image.new("RGB", (20, 20), color="red")
        exif = Image.Exif()
        exif[274] = 1
        imagen.save(buffer, format="JPEG", exif=exif)
        archivo = SimpleUploadedFile(
            "foto-personal.jpg",
            buffer.getvalue(),
            content_type="image/jpeg",
        )

        resultado = preparar_imagen(archivo)
        imagen_limpia = Image.open(resultado)

        self.assertRegex(resultado.name, re.compile(r"^[0-9a-f]{32}\.jpg$"))
        self.assertEqual(len(imagen_limpia.getexif()), 0)
