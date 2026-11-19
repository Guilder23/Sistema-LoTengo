from django.db import models


class Departamento(models.TextChoices):
    BENI = "beni", "Beni"
    CHUQUISACA = "chuquisaca", "Chuquisaca"
    COCHABAMBA = "cochabamba", "Cochabamba"
    LA_PAZ = "la_paz", "La Paz"
    ORURO = "oruro", "Oruro"
    PANDO = "pando", "Pando"
    POTOSI = "potosi", "Potosí"
    SANTA_CRUZ = "santa_cruz", "Santa Cruz"
    TARIJA = "tarija", "Tarija"


class Municipio(models.Model):
    departamento = models.CharField(max_length=20, choices=Departamento.choices)
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = "municipio"
        verbose_name_plural = "municipios"
        ordering = ["departamento", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["departamento", "nombre"],
                name="ubicaciones_municipio_departamento_nombre_unicos",
            )
        ]

    def __str__(self):
        return f"{self.nombre}, {self.get_departamento_display()}"


class Ubicacion(models.Model):
    departamento = models.CharField(max_length=20, choices=Departamento.choices)
    municipio = models.CharField(max_length=100)
    zona = models.CharField(max_length=120, blank=True)
    conoce_lugar_exacto = models.BooleanField(default=False)
    referencia_privada = models.CharField(max_length=240, blank=True)

    class Meta:
        verbose_name = "ubicación"
        verbose_name_plural = "ubicaciones"
        ordering = ["departamento", "municipio", "zona"]

    def __str__(self):
        partes = [self.municipio, self.get_departamento_display()]
        if self.zona:
            partes.insert(1, self.zona)
        return ", ".join(partes)
