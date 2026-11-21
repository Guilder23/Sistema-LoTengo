from django.conf import settings
from django.db import models


class DecisionModeracion(models.Model):
    class Accion(models.TextChoices):
        RESPONDER = "responder", "Responder a la denuncia"
        RESOLVER = "resolver", "Resolver denuncia"
        RECHAZAR = "rechazar", "Rechazar denuncia"
        OCULTAR_PUBLICACION = "ocultar_publicacion", "Ocultar publicación"
        RESTAURAR_PUBLICACION = "restaurar_publicacion", "Restaurar publicación"
        SUSPENDER_USUARIO = "suspender_usuario", "Suspender cuenta temporalmente"
        BLOQUEAR_USUARIO = "bloquear_usuario", "Bloquear cuenta definitivamente"
        REACTIVAR_USUARIO = "reactivar_usuario", "Reactivar cuenta"

    denuncia = models.ForeignKey(
        "denuncias.Denuncia",
        on_delete=models.PROTECT,
        related_name="decisiones",
    )
    moderador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="decisiones_moderacion",
    )
    accion = models.CharField(max_length=32, choices=Accion.choices)
    nota = models.TextField(max_length=2000)
    duracion_dias = models.PositiveSmallIntegerField(null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creada_en", "-pk"]
        verbose_name = "decisión de moderación"
        verbose_name_plural = "decisiones de moderación"

    def __str__(self):
        return f"{self.get_accion_display()} — denuncia #{self.denuncia_id}"
