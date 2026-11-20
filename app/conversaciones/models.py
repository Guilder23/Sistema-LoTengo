from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def ruta_adjunto_mensaje(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    extensiones_permitidas = {
        "imagen": {"jpg", "png", "webp"},
        "audio": {"webm", "ogg", "wav", "mp3", "m4a"},
    }
    if extension not in extensiones_permitidas.get(instance.tipo_adjunto, set()):
        extension = ""
    nombre = uuid4().hex
    sufijo = f".{extension}" if extension else ""
    return f"conversaciones/{instance.conversacion_id}/{nombre}{sufijo}"


class Conversacion(models.Model):
    publicacion = models.ForeignKey(
        "publicaciones.Publicacion",
        on_delete=models.CASCADE,
        related_name="conversaciones",
    )
    interesado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversaciones_iniciadas",
    )
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-actualizada_en", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["publicacion", "interesado"],
                name="conversacion_publicacion_interesado_unica",
            )
        ]

    def __str__(self):
        return f"Conversación sobre {self.publicacion}"


class Mensaje(models.Model):
    class TipoAdjunto(models.TextChoices):
        IMAGEN = "imagen", "Imagen"
        AUDIO = "audio", "Audio"

    conversacion = models.ForeignKey(
        Conversacion,
        on_delete=models.CASCADE,
        related_name="mensajes",
    )
    remitente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mensajes_enviados",
    )
    contenido = models.TextField(max_length=2000, blank=True)
    tipo_adjunto = models.CharField(
        max_length=6,
        choices=TipoAdjunto.choices,
        blank=True,
    )
    archivo = models.FileField(
        upload_to=ruta_adjunto_mensaje,
        blank=True,
    )
    enviada_en = models.DateTimeField(auto_now_add=True)
    leida_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["enviada_en", "pk"]
        indexes = [
            models.Index(fields=["conversacion", "enviada_en"]),
            models.Index(fields=["remitente", "leida_en"]),
        ]

    def clean(self):
        super().clean()
        if not (self.contenido or "").strip():
            if not self.archivo:
                raise ValidationError(
                    {"contenido": "El mensaje necesita texto o un archivo adjunto."}
                )
        if bool(self.archivo) != bool(self.tipo_adjunto):
            raise ValidationError(
                {"archivo": "El tipo y el archivo adjunto deben coincidir."}
            )
        if self.conversacion_id and self.remitente_id:
            participante_ids = {
                self.conversacion.interesado_id,
                self.conversacion.publicacion.usuario_id,
            }
            if self.remitente_id not in participante_ids:
                raise ValidationError(
                    {"remitente": "El remitente debe participar en la conversación."}
                )

    def __str__(self):
        return f"Mensaje de {self.remitente} en conversación {self.conversacion_id}"


class PresenciaUsuario(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="presencia_chat",
    )
    ultima_vez_en_linea = models.DateTimeField(null=True, blank=True)


class ConexionPresencia(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conexiones_chat_activas",
    )
    canal = models.CharField(max_length=255, unique=True)
    ultimo_latido = models.DateTimeField(default=timezone.now, db_index=True)
