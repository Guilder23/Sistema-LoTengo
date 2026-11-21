from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class GestorUsuarios(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo electrónico es obligatorio.")
        email = email.strip().casefold()
        usuario = self.model(email=email, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("correo_verificado", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superusuario debe tener is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractUser):
    username = None
    email = models.EmailField("correo electrónico", unique=True)
    telefono = models.CharField("teléfono", max_length=30)
    correo_verificado = models.BooleanField("correo verificado", default=False)
    suspendido_hasta = models.DateTimeField(
        "suspendido hasta",
        null=True,
        blank=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "telefono"]

    objects = GestorUsuarios()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["last_name", "first_name", "email"]

    def save(self, *args, **kwargs):
        self.email = self.email.strip().casefold()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name() or self.email


class AceptacionLegal(models.Model):
    class Documento(models.TextChoices):
        TERMINOS = "terminos", "Términos y condiciones"
        PRIVACIDAD = "privacidad", "Política de privacidad"

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="aceptaciones_legales",
    )
    documento = models.CharField(max_length=20, choices=Documento.choices)
    version = models.CharField(max_length=20)
    aceptado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "aceptación legal"
        verbose_name_plural = "aceptaciones legales"
        ordering = ["-aceptado_en"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "documento", "version"],
                name="cuentas_aceptacion_documento_version_unica",
            )
        ]

    def __str__(self):
        return f"{self.usuario}: {self.get_documento_display()} v{self.version}"
