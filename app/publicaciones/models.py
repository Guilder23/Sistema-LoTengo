from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from app.categorias.models import Categoria
from app.ubicaciones.models import Ubicacion


class Publicacion(models.Model):
    class Tipo(models.TextChoices):
        PERDIDO = "perdido", "Objeto perdido"
        ENCONTRADO = "encontrado", "Objeto encontrado"

    class Estado(models.TextChoices):
        PUBLICADA = "publicada", "Publicada"
        PAUSADA = "pausada", "Pausada"
        RESUELTA = "resuelta", "Resuelta"
        ELIMINADA = "eliminada", "Eliminada"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="publicaciones",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="publicaciones",
    )
    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.PROTECT,
        related_name="publicaciones",
    )
    tipo = models.CharField(max_length=12, choices=Tipo.choices)
    titulo = models.CharField(max_length=140)
    descripcion = models.TextField(max_length=1600)
    marca = models.CharField(max_length=80, blank=True)
    color = models.CharField(max_length=60, blank=True)
    caracteristicas_publicas = models.TextField(max_length=500, blank=True)
    caracteristica_privada = models.TextField(
        max_length=500,
        blank=True,
        help_text="Dato de verificación que no se muestra públicamente.",
    )
    fecha_evento = models.DateField()
    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.PUBLICADA,
    )
    eliminada_en = models.DateTimeField(null=True, blank=True)
    oculta_por_moderacion = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "publicación"
        verbose_name_plural = "publicaciones"
        ordering = ["-creada_en"]
        indexes = [
            models.Index(fields=["estado", "tipo", "-creada_en"]),
            models.Index(fields=["categoria", "estado"]),
        ]

    def clean(self):
        super().clean()
        if self.fecha_evento and self.fecha_evento > timezone.localdate():
            raise ValidationError(
                {"fecha_evento": "La fecha del objeto no puede estar en el futuro."}
            )

    def __str__(self):
        return self.titulo

    @property
    def etiqueta_resolucion(self):
        if self.tipo == self.Tipo.PERDIDO:
            return "Objeto recuperado"
        return "Objeto entregado"


def ruta_imagen_publicacion(instance, filename):
    return f"publicaciones/{instance.publicacion_id}/{filename}"


class ImagenPublicacion(models.Model):
    publicacion = models.ForeignKey(
        Publicacion,
        on_delete=models.CASCADE,
        related_name="imagenes",
    )
    archivo = models.ImageField(upload_to=ruta_imagen_publicacion)
    subida_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "fotografía de publicación"
        verbose_name_plural = "fotografías de publicaciones"
        ordering = ["subida_en", "pk"]

    def __str__(self):
        return f"Fotografía de {self.publicacion}"
