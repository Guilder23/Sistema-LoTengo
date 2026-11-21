from django.utils import timezone
from django.contrib.auth.backends import ModelBackend


class CorreoVerificadoBackend(ModelBackend):
    def user_can_authenticate(self, user):
        return super().user_can_authenticate(user) and (
            user.is_superuser or user.correo_verificado
        ) and not (
            user.suspendido_hasta and user.suspendido_hasta > timezone.now()
        )
