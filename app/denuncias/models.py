from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db.models import Q


def ruta_evidencia_denuncia(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in {"jpg", "jpeg", "png", "webp"}:
        extension = "jpg"
    return f"denuncias/{uuid4().hex}.{extension}"


class Denuncia(models.Model):
    class Motivo(models.TextChoices):
        PUBLICACION_FALSA = "publicacion_falsa", "Publicación falsa"
        OBJETO_SOSPECHOSO = "objeto_sospechoso", "Objeto sospechoso"
        ESTAFA = "estafa", "Intento de estafa"
        ACOSO = "acoso", "Acoso"
        MENSAJE_INAPROPIADO = "mensaje_inapropiado", "Mensaje inapropiado"
        SUPLANTACION = "suplantacion", "Intento de suplantación"
        OTRO = "otro", "Otro"

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EN_REVISION = "en_revision", "En revisión"
        RESUELTA = "resuelta", "Resuelta"
        RECHAZADA = "rechazada", "Rechazada"

    denunciante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="denuncias_enviadas",
    )
    denunciado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="denuncias_recibidas",
        null=True,
        blank=True,
    )
    publicacion = models.ForeignKey(
        "publicaciones.Publicacion",
        on_delete=models.PROTECT,
        related_name="denuncias",
        null=True,
        blank=True,
    )
    mensaje = models.ForeignKey(
        "conversaciones.Mensaje",
        on_delete=models.PROTECT,
        related_name="denuncias",
        null=True,
        blank=True,
    )
    motivo = models.CharField(max_length=32, choices=Motivo.choices)
    descripcion = models.TextField(max_length=2000)
    evidencia = models.ImageField(
        upload_to=ruta_evidencia_denuncia,
        blank=True,
    )
    estado = models.CharField(
        max_length=16,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    respuesta = models.TextField(max_length=2000, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["estado", "-creada_en"]
        indexes = [models.Index(fields=["estado", "-creada_en"])]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(publicacion__isnull=False)
                    | Q(mensaje__isnull=False)
                    | Q(denunciado__isnull=False)
                ),
                name="denuncia_debe_tener_objetivo",
            )
        ]
        verbose_name = "denuncia"
        verbose_name_plural = "denuncias"

    def __str__(self):
        return f"Denuncia #{self.pk}: {self.get_motivo_display()}"


class BloqueoUsuario(models.Model):
    bloqueador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="usuarios_bloqueados",
    )
    bloqueado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bloqueado_por",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["bloqueador", "bloqueado"],
                name="bloqueo_usuario_unico",
            ),
            models.CheckConstraint(
                condition=~Q(bloqueador=models.F("bloqueado")),
                name="usuario_no_puede_bloquearse",
            ),
        ]
        verbose_name = "bloqueo de usuario"
        verbose_name_plural = "bloqueos de usuarios"


class ConversacionSilenciada(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversaciones_silenciadas",
    )
    conversacion = models.ForeignKey(
        "conversaciones.Conversacion",
        on_delete=models.CASCADE,
        related_name="silencios",
    )
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "conversacion"],
                name="silencio_conversacion_usuario_unico",
            )
        ]
        verbose_name = "conversación silenciada"
        verbose_name_plural = "conversaciones silenciadas"
