from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from app.ubicaciones.models import Ubicacion

from .models import Departamento, Municipio


class PruebasGestionGeografia(TestCase):
    def setUp(self):
        self.administrador = get_user_model().objects.create_user(
            email="admin-geografia@example.com",
            password="Long-term-private-phrase-495!",
            telefono="+591 70000003",
            is_staff=True,
            correo_verificado=True,
        )
        self.client.force_login(self.administrador)
        self.departamento = Departamento.objects.get(codigo="cochabamba")
        self.municipio = Municipio.objects.get(
            departamento=self.departamento,
            nombre="Cochabamba",
        )

    def test_migra_catalogo_de_municipios_existente_a_geografia(self):
        self.assertEqual(Departamento.objects.count(), 9)
        self.assertTrue(
            Municipio.objects.filter(
                departamento__codigo="beni",
                nombre="Trinidad",
            ).exists()
        )

    def test_crea_edita_y_elimina_departamento(self):
        respuesta = self.client.get(reverse("geografia:departamento_crear"))
        self.assertContains(respuesta, "css/geografia/departamentos/crud/crear.css")
        self.assertContains(respuesta, "js/geografia/departamentos/crud/crear.js")
        respuesta = self.client.post(
            reverse("geografia:departamento_crear"),
            {"nombre": "Departamento de prueba"},
        )
        departamento = Departamento.objects.get(nombre="Departamento de prueba")
        self.assertRedirects(
            respuesta,
            reverse("geografia:departamento_detalle", args=[departamento.pk]),
        )
        self.assertEqual(departamento.codigo, "departamento_de_prueba")

        self.assertEqual(
            self.client.get(
                reverse("geografia:departamento_editar", args=[departamento.pk])
            ).status_code,
            200,
        )
        self.assertContains(
            self.client.get(
                reverse("geografia:departamento_editar", args=[departamento.pk])
            ),
            "css/geografia/departamentos/crud/editar.css",
        )
        self.assertContains(
            self.client.get(
                reverse("geografia:departamento_editar", args=[departamento.pk])
            ),
            "js/geografia/departamentos/crud/editar.js",
        )
        respuesta = self.client.post(
            reverse("geografia:departamento_editar", args=[departamento.pk]),
            {"nombre": "Departamento actualizado"},
        )
        self.assertRedirects(
            respuesta,
            reverse("geografia:departamento_detalle", args=[departamento.pk]),
        )
        departamento.refresh_from_db()
        self.assertEqual(departamento.nombre, "Departamento actualizado")

        self.assertEqual(
            self.client.get(
                reverse("geografia:departamento_eliminar", args=[departamento.pk])
            ).status_code,
            200,
        )
        respuesta = self.client.post(
            reverse("geografia:departamento_eliminar", args=[departamento.pk])
        )
        self.assertRedirects(respuesta, reverse("geografia:departamentos"))
        self.assertFalse(Departamento.objects.filter(pk=departamento.pk).exists())

    def test_validacion_manual_rechaza_codigo_de_departamento_duplicado(self):
        respuesta = self.client.post(
            reverse("geografia:departamento_crear"),
            {"nombre": "Cochabamba"},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(
            respuesta,
            "Ya existe un departamento con un código derivado de ese nombre.",
        )
        self.assertEqual(
            Departamento.objects.filter(codigo="cochabamba").count(),
            1,
        )

    def test_crea_edita_municipio_y_actualiza_ubicaciones_asociadas(self):
        respuesta = self.client.get(reverse("geografia:municipio_crear"))
        self.assertContains(respuesta, "css/geografia/municipios/crud/crear.css")
        self.assertContains(respuesta, "js/geografia/municipios/crud/crear.js")
        respuesta = self.client.post(
            reverse("geografia:municipio_crear"),
            {"departamento": self.departamento.pk, "nombre": "Municipio de prueba"},
        )
        municipio = Municipio.objects.get(nombre="Municipio de prueba")
        self.assertRedirects(
            respuesta,
            reverse("geografia:municipio_detalle", args=[municipio.pk]),
        )

        self.assertEqual(
            self.client.get(
                reverse("geografia:municipio_editar", args=[municipio.pk])
            ).status_code,
            200,
        )
        self.assertContains(
            self.client.get(
                reverse("geografia:municipio_editar", args=[municipio.pk])
            ),
            "css/geografia/municipios/crud/editar.css",
        )
        self.assertContains(
            self.client.get(
                reverse("geografia:municipio_editar", args=[municipio.pk])
            ),
            "js/geografia/municipios/crud/editar.js",
        )
        ubicacion = Ubicacion.objects.create(
            departamento=self.departamento,
            municipio=municipio,
            zona="Centro",
        )
        respuesta = self.client.post(
            reverse("geografia:municipio_editar", args=[municipio.pk]),
            {"departamento": self.departamento.pk, "nombre": "Municipio actualizado"},
        )
        self.assertRedirects(
            respuesta,
            reverse("geografia:municipio_detalle", args=[municipio.pk]),
        )
        ubicacion.refresh_from_db()
        self.assertEqual(ubicacion.municipio.nombre, "Municipio actualizado")

        respuesta = self.client.post(
            reverse("geografia:municipio_eliminar", args=[municipio.pk])
        )
        self.assertRedirects(
            respuesta,
            reverse("geografia:municipio_detalle", args=[municipio.pk]),
        )
        self.assertTrue(Municipio.objects.filter(pk=municipio.pk).exists())
        ubicacion.delete()
        self.assertEqual(
            self.client.get(
                reverse("geografia:municipio_eliminar", args=[municipio.pk])
            ).status_code,
            200,
        )
        respuesta = self.client.post(
            reverse("geografia:municipio_eliminar", args=[municipio.pk])
        )
        self.assertRedirects(respuesta, reverse("geografia:municipios"))
        self.assertFalse(Municipio.objects.filter(pk=municipio.pk).exists())

    def test_eliminar_departamento_con_ubicaciones_guardadas_se_bloquea(self):
        Ubicacion.objects.create(
            departamento=self.departamento,
            municipio=self.municipio,
            zona="Centro",
        )
        respuesta = self.client.post(
            reverse(
                "geografia:departamento_eliminar",
                args=[self.departamento.pk],
            )
        )

        self.assertRedirects(
            respuesta,
            reverse(
                "geografia:departamento_detalle",
                args=[self.departamento.pk],
            ),
        )
        self.assertTrue(
            Departamento.objects.filter(pk=self.departamento.pk).exists()
        )

    def test_validacion_manual_rechaza_departamento_inexistente_en_municipio(self):
        respuesta = self.client.post(
            reverse("geografia:municipio_crear"),
            {"departamento": "999999", "nombre": "Municipio inválido"},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Selecciona un departamento válido.")
        self.assertFalse(
            Municipio.objects.filter(nombre="Municipio inválido").exists()
        )
