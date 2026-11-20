from django.db import models


class Departamento(models.Model):
    codigo = models.SlugField(max_length=30, unique=True)
    nombre = models.CharField(max_length=80, unique=True)

    class Meta:
        verbose_name = "departamento"
        verbose_name_plural = "departamentos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Municipio(models.Model):
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.CASCADE,
        related_name="municipios",
    )
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = "municipio"
        verbose_name_plural = "municipios"
        ordering = ["departamento__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["departamento", "nombre"],
                name="geografia_municipio_departamento_nombre_unicos",
            )
        ]

    def __str__(self):
        return f"{self.nombre}, {self.departamento.nombre}"
