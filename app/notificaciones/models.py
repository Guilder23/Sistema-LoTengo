from django.conf import settings
from django.db import models


class Notificacion(models.Model):
    class Tipo(models.TextChoices):
        MENSAJE = "mensaje", "Mensaje recibido"
        NUEVA_PUBLICACION = "nueva_publicacion", "Nueva publicación"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificaciones",
    )
    tipo = models.CharField(max_length=24, choices=Tipo.choices)
    titulo = models.CharField(max_length=100)
    mensaje = models.CharField(max_length=240)
    url = models.CharField(max_length=2048)
    creada_en = models.DateTimeField(auto_now_add=True)
    leida_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-creada_en", "-pk"]
        indexes = [
            models.Index(fields=["usuario", "leida_en", "-creada_en"]),
        ]
        verbose_name = "notificación"
        verbose_name_plural = "notificaciones"

    def __str__(self):
        return f"{self.titulo} para {self.usuario}"


class PreferenciaNotificaciones(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferencia_notificaciones",
    )
    nuevas_publicaciones = models.BooleanField(default=False)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "preferencia de notificaciones"
        verbose_name_plural = "preferencias de notificaciones"

    def __str__(self):
        return f"Preferencias de {self.usuario}"


class SuscripcionPush(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="suscripciones_push",
    )
    endpoint = models.URLField(max_length=2048, unique=True)
    clave_publica = models.CharField(max_length=256)
    clave_auth = models.CharField(max_length=128)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-actualizada_en"]
        verbose_name = "suscripción de notificaciones del navegador"
        verbose_name_plural = "suscripciones de notificaciones del navegador"

    def __str__(self):
        return f"Dispositivo de {self.usuario}"
