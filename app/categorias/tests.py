from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from app.geografia.models import Departamento, Municipio
from app.ubicaciones.models import Ubicacion

from .models import Categoria


class PruebasGestionCategorias(TestCase):
    def setUp(self):
        self.administrador = get_user_model().objects.create_user(
            email="admin-categorias@example.com",
            password="Long-term-private-phrase-494!",
            telefono="+591 70000002",
            is_staff=True,
            correo_verificado=True,
        )
        self.client.force_login(self.administrador)

    def test_crea_detalla_edita_y_elimina_categoria(self):
        respuesta = self.client.get(reverse("categorias:crear"))
        self.assertContains(respuesta, "css/categorias/crud/crear.css")
        self.assertContains(respuesta, "js/categorias/crud/crear.js")
        respuesta = self.client.post(
            reverse("categorias:crear"),
            {"nombre": "Instrumentos musicales", "slug": "", "activa": "on", "orden": 4},
        )

        categoria = Categoria.objects.get(nombre="Instrumentos musicales")
        self.assertRedirects(
            respuesta,
            reverse("categorias:detalle", args=[categoria.pk]),
        )
        self.assertEqual(categoria.slug, "instrumentos-musicales")
        self.assertEqual(
            self.client.get(reverse("categorias:detalle", args=[categoria.pk])).status_code,
            200,
        )
        self.assertContains(
            self.client.get(reverse("categorias:editar", args=[categoria.pk])),
            "css/categorias/crud/editar.css",
        )
        self.assertContains(
            self.client.get(reverse("categorias:editar", args=[categoria.pk])),
            "js/categorias/crud/editar.js",
        )

        respuesta = self.client.post(
            reverse("categorias:editar", args=[categoria.pk]),
            {
                "nombre": "Instrumentos",
                "slug": "instrumentos",
                "orden": 2,
            },
        )
        self.assertRedirects(
            respuesta,
            reverse("categorias:detalle", args=[categoria.pk]),
        )
        categoria.refresh_from_db()
        self.assertEqual(categoria.nombre, "Instrumentos")
        self.assertFalse(categoria.activa)

        self.assertEqual(
            self.client.get(reverse("categorias:eliminar", args=[categoria.pk])).status_code,
            200,
        )
        respuesta = self.client.post(
            reverse("categorias:eliminar", args=[categoria.pk])
        )
        self.assertRedirects(respuesta, reverse("categorias:lista"))
        self.assertFalse(Categoria.objects.filter(pk=categoria.pk).exists())

    def test_listados_y_confirmaciones_de_eliminacion_renderizan(self):
        categoria = Categoria.objects.get(slug="mascotas")
        respuesta = self.client.get(reverse("categorias:lista"))
        self.assertContains(respuesta, 'class="cuenta-sidebar"', html=False)
        self.assertContains(respuesta, "css/categorias/categorias.css")
        self.assertContains(respuesta, "js/categorias/categorias.js")
        self.assertContains(respuesta, 'class="catalogo-fila-acciones"')
        self.assertContains(respuesta, 'title="Ver detalle"')
        self.assertContains(respuesta, 'title="Editar"')
        self.assertContains(respuesta, 'title="Eliminar"')
        self.assertContains(
            respuesta,
            reverse("geografia:departamentos"),
        )
        self.assertContains(
            respuesta,
            reverse("geografia:municipios"),
        )
        respuesta = self.client.get(reverse("geografia:departamentos"))
        self.assertContains(respuesta, "css/geografia/departamentos/departamentos.css")
        self.assertContains(respuesta, "js/geografia/departamentos/departamentos.js")
        self.assertContains(respuesta, 'class="sidebar-accordion" open')
        self.assertContains(respuesta, 'title="Editar"')
        respuesta = self.client.get(reverse("geografia:municipios"))
        self.assertContains(respuesta, "css/geografia/municipios/municipios.css")
        self.assertContains(respuesta, "js/geografia/municipios/municipios.js")
        self.assertContains(respuesta, 'class="sidebar-accordion" open')
        self.assertContains(respuesta, 'title="Eliminar"')
        self.assertEqual(
            self.client.get(
                reverse("categorias:eliminar", args=[categoria.pk])
            ).status_code,
            200,
        )

    def test_validacion_manual_rechaza_orden_no_numerico(self):
        respuesta = self.client.post(
            reverse("categorias:crear"),
            {
                "nombre": "Categoría con orden inválido",
                "slug": "",
                "activa": "on",
                "orden": "inválido",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Introduce un número entero válido.")
        self.assertFalse(
            Categoria.objects.filter(nombre="Categoría con orden inválido").exists()
        )

    def test_gestion_de_categorias_requiere_personal_administrador(self):
        self.client.logout()
        respuesta = self.client.get(reverse("categorias:lista"))

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/admin/login/", respuesta["Location"])

    def test_no_elimina_categoria_que_tiene_publicaciones(self):
        from app.publicaciones.models import Publicacion

        categoria = Categoria.objects.get(slug="mascotas")
        departamento = Departamento.objects.get(codigo="beni")
        municipio = Municipio.objects.get(
            departamento=departamento,
            nombre="Trinidad",
        )
        ubicacion = Ubicacion.objects.create(
            departamento=departamento,
            municipio=municipio,
        )
        Publicacion.objects.create(
            usuario=self.administrador,
            categoria=categoria,
            ubicacion=ubicacion,
            tipo=Publicacion.Tipo.PERDIDO,
            titulo="Perro extraviado",
            descripcion="Perro perdido cerca del centro.",
            fecha_evento=date.today(),
        )

        respuesta = self.client.post(
            reverse("categorias:eliminar", args=[categoria.pk])
        )

        self.assertRedirects(
            respuesta,
            reverse("categorias:detalle", args=[categoria.pk]),
        )
        self.assertTrue(Categoria.objects.filter(pk=categoria.pk).exists())
