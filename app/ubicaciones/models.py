from django.core.exceptions import ValidationError
from django.db import models

from app.geografia.models import Departamento, Municipio


class Ubicacion(models.Model):
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        related_name="ubicaciones",
    )
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.PROTECT,
        related_name="ubicaciones",
    )
    zona = models.CharField(max_length=120, blank=True)
    conoce_lugar_exacto = models.BooleanField(default=False)
    referencia_privada = models.CharField(max_length=240, blank=True)

    class Meta:
        verbose_name = "ubicación"
        verbose_name_plural = "ubicaciones"
        ordering = ["departamento__nombre", "municipio__nombre", "zona"]

    def __str__(self):
        partes = [self.municipio.nombre, self.departamento.nombre]
        if self.zona:
            partes.insert(1, self.zona)
        return ", ".join(partes)

    def get_departamento_display(self):
        return self.departamento.nombre

    def clean(self):
        super().clean()
        if (
            self.municipio_id
            and self.departamento_id
            and self.municipio.departamento_id != self.departamento_id
        ):
            raise ValidationError(
                {"municipio": "El municipio debe pertenecer al departamento seleccionado."}
            )
