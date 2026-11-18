import logging
from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from django.contrib.auth.tokens import default_token_generator

from .tokens import token_verificacion_correo


logger = logging.getLogger(__name__)


class ErrorEnvioCorreo(Exception):
    pass


def _crear_enlace(request, ruta):
    if settings.PUBLIC_BASE_URL:
        return urljoin(f"{settings.PUBLIC_BASE_URL}/", ruta.lstrip("/"))
    if not settings.DEBUG:
        raise ErrorEnvioCorreo(
            "PUBLIC_BASE_URL debe configurarse para generar enlaces de correo en producción."
        )
    logger.warning(
        "PUBLIC_BASE_URL no está configurado; los correos de desarrollo usarán el host de la solicitud."
    )
    return request.build_absolute_uri(ruta)


def _enviar(asunto, mensaje, destinatario, plantilla, contexto):
    correo = EmailMultiAlternatives(
        asunto,
        mensaje,
        settings.DEFAULT_FROM_EMAIL,
        [destinatario],
    )
    if not (settings.DEBUG and not settings.PUBLIC_BASE_URL):
        mensaje_html = render_to_string(plantilla, contexto)
        correo.attach_alternative(mensaje_html, "text/html")
    cantidad = correo.send(fail_silently=False)
    if cantidad != 1:
        raise ErrorEnvioCorreo("El servidor de correo no aceptó el mensaje.")


def enviar_verificacion(request, usuario):
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = token_verificacion_correo.make_token(usuario)
    ruta = reverse(
        "cuentas:verificar_correo",
        kwargs={"uidb64": uid, "token": token},
    )
    enlace = _crear_enlace(request, ruta)
    _enviar(
        "Verifica tu correo de Lotengo",
        (
            f"Hola {usuario.first_name},\n\n"
            "Confirma tu correo electrónico abriendo este enlace:\n"
            f"{enlace}\n\n"
            "Si no creaste esta cuenta, puedes ignorar este mensaje."
        ),
        usuario.email,
        "correos/verificacion.html",
        {"nombre": usuario.first_name, "enlace": enlace},
    )


def enviar_restauracion_contrasena(request, usuario):
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = default_token_generator.make_token(usuario)
    ruta = reverse(
        "cuentas:restablecer_contrasena",
        kwargs={"uidb64": uid, "token": token},
    )
    enlace = _crear_enlace(request, ruta)
    _enviar(
        "Restablece tu contraseña de Lotengo",
        (
            f"Hola {usuario.first_name or 'usuario'},\n\n"
            "Para elegir una contraseña nueva, abre este enlace:\n"
            f"{enlace}\n\n"
            "Si no solicitaste este cambio, ignora este mensaje."
        ),
        usuario.email,
        "correos/restablecer_contrasena.html",
        {"nombre": usuario.first_name, "enlace": enlace},
    )
