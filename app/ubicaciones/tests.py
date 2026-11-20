from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class PruebasMigracionCatalogoGeografico(TransactionTestCase):
    migrate_from = ("ubicaciones", "0003_delete_municipio_alter_ubicacion_departamento")
    migrate_to = ("ubicaciones", "0004_relacionar_ubicacion_con_catalogo_geografico")

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])

        apps_anteriores = executor.loader.project_state(
            [self.migrate_from]
        ).apps
        UbicacionAnterior = apps_anteriores.get_model("ubicaciones", "Ubicacion")
        self.ubicacion_pk = UbicacionAnterior.objects.create(
            departamento="beni",
            municipio="Trinidad",
            zona="Centro",
        ).pk

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_preserva_la_ubicacion_y_la_relaciona_con_los_catalogos(self):
        apps_actuales = MigrationExecutor(connection).loader.project_state(
            [self.migrate_to]
        ).apps
        Ubicacion = apps_actuales.get_model("ubicaciones", "Ubicacion")
        ubicacion = Ubicacion.objects.get(pk=self.ubicacion_pk)

        self.assertEqual(ubicacion.departamento.codigo, "beni")
        self.assertEqual(ubicacion.departamento.nombre, "Beni")
        self.assertEqual(ubicacion.municipio.nombre, "Trinidad")
