from django.contrib.auth.tokens import PasswordResetTokenGenerator


class GeneradorTokenVerificacion(PasswordResetTokenGenerator):
    key_salt = "app.cuentas.tokens.GeneradorTokenVerificacion"

    def _make_hash_value(self, user, timestamp):
        return (
            f"{user.pk}{timestamp}{user.password}"
            f"{user.correo_verificado}{user.email}"
        )


token_verificacion_correo = GeneradorTokenVerificacion()
