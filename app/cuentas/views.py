import logging
from smtplib import SMTPException

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils.encoding import force_str
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode
from django.views.decorators.http import require_http_methods, require_POST

from app.notificaciones.models import SuscripcionPush

from .correos import (
    ErrorEnvioCorreo,
    enviar_restauracion_contrasena,
    enviar_verificacion,
)
from .models import AceptacionLegal
from .tokens import token_verificacion_correo


logger = logging.getLogger(__name__)
Usuario = get_user_model()


def _agregar_error(errores, campo, mensaje):
    errores.setdefault(campo, []).append(mensaje)


def _usuario_desde_uid(uidb64):
    try:
        usuario_id = force_str(urlsafe_base64_decode(uidb64))
        return Usuario.objects.get(pk=usuario_id)
    except (
        TypeError,
        ValueError,
        OverflowError,
        UnicodeDecodeError,
        Usuario.DoesNotExist,
    ):
        return None


@require_http_methods(["GET", "POST"])
def registro(request):
    if request.user.is_authenticated:
        return redirect("cuentas:panel")

    errores = {}
    valores = {}
    if request.method == "POST":
        nombre = request.POST.get("first_name", "").strip()
        apellido = request.POST.get("last_name", "").strip()
        correo = request.POST.get("email", "").strip().casefold()
        telefono = request.POST.get("telefono", "").strip()
        contrasena = request.POST.get("password", "")
        confirmacion = request.POST.get("password_confirm", "")
        valores = {
            "first_name": nombre,
            "last_name": apellido,
            "email": correo,
            "telefono": telefono,
            "acepta_terminos": request.POST.get("acepta_terminos") == "on",
            "acepta_privacidad": request.POST.get("acepta_privacidad") == "on",
        }

        if not nombre:
            _agregar_error(errores, "first_name", "Escribe tu nombre.")
        elif len(nombre) > 150:
            _agregar_error(errores, "first_name", "El nombre supera el máximo permitido.")
        if not apellido:
            _agregar_error(errores, "last_name", "Escribe tu apellido.")
        elif len(apellido) > 150:
            _agregar_error(errores, "last_name", "El apellido supera el máximo permitido.")
        try:
            validate_email(correo)
        except ValidationError:
            _agregar_error(errores, "email", "Escribe un correo electrónico válido.")
        if len(correo) > 254:
            _agregar_error(errores, "email", "El correo supera el máximo permitido.")
        if Usuario.objects.filter(email__iexact=correo).exists():
            _agregar_error(errores, "email", "Ya existe una cuenta con ese correo.")
        if not telefono:
            _agregar_error(errores, "telefono", "Escribe tu número de celular.")
        elif len(telefono) > 30:
            _agregar_error(errores, "telefono", "El número supera el máximo permitido.")
        if contrasena != confirmacion:
            _agregar_error(errores, "password_confirm", "Las contraseñas no coinciden.")
        if request.POST.get("acepta_terminos") != "on":
            _agregar_error(errores, "acepta_terminos", "Debes aceptar los términos y condiciones.")
        if request.POST.get("acepta_privacidad") != "on":
            _agregar_error(errores, "acepta_privacidad", "Debes aceptar la política de privacidad.")

        usuario_candidato = Usuario(
            email=correo,
            first_name=nombre,
            last_name=apellido,
            telefono=telefono,
        )
        try:
            validate_password(contrasena, user=usuario_candidato)
        except ValidationError as error:
            for mensaje in error.messages:
                _agregar_error(errores, "password", mensaje)

        if not errores:
            try:
                with transaction.atomic():
                    usuario = Usuario.objects.create_user(
                        email=correo,
                        password=contrasena,
                        first_name=nombre,
                        last_name=apellido,
                        telefono=telefono,
                    )
                    AceptacionLegal.objects.bulk_create(
                        [
                            AceptacionLegal(
                                usuario=usuario,
                                documento=AceptacionLegal.Documento.TERMINOS,
                                version=settings.TERMINOS_VERSION,
                            ),
                            AceptacionLegal(
                                usuario=usuario,
                                documento=AceptacionLegal.Documento.PRIVACIDAD,
                                version=settings.PRIVACIDAD_VERSION,
                            ),
                        ]
                    )
            except IntegrityError:
                _agregar_error(errores, "email", "Ya existe una cuenta con ese correo.")
            else:
                try:
                    enviar_verificacion(request, usuario)
                except (ErrorEnvioCorreo, SMTPException, OSError):
                    logger.exception(
                        "No se pudo enviar la verificación de correo para el usuario %s.",
                        usuario.pk,
                    )
                    return render(
                        request,
                        "cuentas/acceso/verificacion_enviada.html",
                        {"envio_fallido": True},
                        status=503,
                    )
                messages.success(
                    request,
                    "Cuenta creada. Revisa tu correo para verificarla antes de iniciar sesión.",
                )
                return redirect("cuentas:verificacion_enviada")

    return render(
        request,
        "cuentas/acceso/registro.html",
        {"errores": errores, "valores": valores},
    )


@require_http_methods(["GET", "POST"])
def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect("cuentas:panel")

    error = ""
    correo = ""
    siguiente = request.POST.get("next", request.GET.get("next", ""))
    if request.method == "POST":
        correo = request.POST.get("email", "").strip().casefold()
        contrasena = request.POST.get("password", "")
        usuario = authenticate(request, email=correo, password=contrasena)
        if usuario is None:
            candidato = Usuario.objects.filter(email__iexact=correo).first()
            if (
                candidato
                and candidato.check_password(contrasena)
                and candidato.is_active
                and not candidato.correo_verificado
            ):
                error = "Verifica tu correo antes de iniciar sesión."
            else:
                error = "El correo o la contraseña no son correctos."
        else:
            login(request, usuario)
            if not url_has_allowed_host_and_scheme(
                siguiente,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                siguiente = ""
            return redirect(siguiente or "cuentas:panel")

    return render(
        request,
        "cuentas/acceso/iniciar_sesion.html",
        {"error": error, "correo": correo, "siguiente": siguiente},
    )


@require_POST
def cerrar_sesion(request):
    endpoint_push = request.POST.get("push_endpoint", "").strip()
    if request.user.is_authenticated and 0 < len(endpoint_push) <= 2048:
        SuscripcionPush.objects.filter(
            usuario=request.user,
            endpoint=endpoint_push,
        ).delete()
    logout(request)
    messages.success(request, "Cerraste sesión correctamente.")
    return redirect("general:inicio")


@require_http_methods(["GET", "POST"])
def verificar_correo(request, uidb64, token):
    usuario = _usuario_desde_uid(uidb64)
    if usuario is None:
        return render(request, "cuentas/acceso/enlace_invalido.html", status=400)

    if usuario.correo_verificado:
        return render(request, "cuentas/acceso/correo_verificado.html")
    if not token_verificacion_correo.check_token(usuario, token):
        return render(request, "cuentas/acceso/enlace_invalido.html", status=400)

    usuario.correo_verificado = True
    usuario.save(update_fields=["correo_verificado"])
    return render(request, "cuentas/acceso/correo_verificado.html")


@require_http_methods(["GET", "POST"])
def reenviar_verificacion(request):
    if request.method == "POST":
        correo = request.POST.get("email", "").strip().casefold()
        usuario = Usuario.objects.filter(
            email__iexact=correo,
            correo_verificado=False,
            is_active=True,
        ).first()
        if usuario:
            try:
                enviar_verificacion(request, usuario)
            except (ErrorEnvioCorreo, SMTPException, OSError):
                logger.exception(
                    "No se pudo reenviar la verificación de correo para el usuario %s.",
                    usuario.pk,
                )
                messages.error(request, "No se pudo enviar el correo. Inténtalo más tarde.")
                return redirect("cuentas:reenviar_verificacion")
        messages.success(
            request,
            "Si existe una cuenta pendiente para ese correo, enviaremos un nuevo enlace.",
        )
        return redirect("cuentas:verificacion_enviada")

    return render(request, "cuentas/acceso/reenviar_verificacion.html")


def verificacion_enviada(request):
    return render(request, "cuentas/acceso/verificacion_enviada.html")


@require_http_methods(["GET", "POST"])
def solicitar_restauracion(request):
    if request.method == "POST":
        correo = request.POST.get("email", "").strip().casefold()
        usuario = Usuario.objects.filter(
            email__iexact=correo,
            is_active=True,
            correo_verificado=True,
        ).first()
        if usuario:
            try:
                enviar_restauracion_contrasena(request, usuario)
            except (ErrorEnvioCorreo, SMTPException, OSError):
                logger.exception(
                    "No se pudo enviar el restablecimiento de contraseña para el usuario %s.",
                    usuario.pk,
                )
                messages.error(
                    request,
                    "No se pudo enviar el correo ahora. Inténtalo más tarde.",
                )
                return redirect("cuentas:solicitar_restauracion")
        return redirect("cuentas:restauracion_solicitada")

    return render(request, "cuentas/recuperacion/solicitar_restauracion.html")


def restauracion_solicitada(request):
    return render(request, "cuentas/recuperacion/restauracion_solicitada.html")


@require_http_methods(["GET", "POST"])
def restablecer_contrasena(request, uidb64, token):
    usuario = _usuario_desde_uid(uidb64)
    if (
        usuario is None
        or not usuario.is_active
        or not usuario.correo_verificado
        or not default_token_generator.check_token(usuario, token)
    ):
        return render(request, "cuentas/acceso/enlace_invalido.html", status=400)

    errores = []
    if request.method == "POST":
        contrasena = request.POST.get("password", "")
        confirmacion = request.POST.get("password_confirm", "")
        if contrasena != confirmacion:
            errores.append("Las contraseñas no coinciden.")
        try:
            validate_password(contrasena, user=usuario)
        except ValidationError as error:
            errores.extend(error.messages)
        if not errores:
            usuario.set_password(contrasena)
            usuario.save(update_fields=["password"])
            return redirect("cuentas:contrasena_actualizada")

    return render(
        request,
        "cuentas/recuperacion/restablecer_contrasena.html",
        {"errores": errores, "uidb64": uidb64, "token": token},
    )


def contrasena_actualizada(request):
    return render(request, "cuentas/recuperacion/contrasena_actualizada.html")


@login_required
def panel(request):
    return render(
        request,
        "cuentas/panel/panel.html",
        {"mostrar_sidebar_cuenta": True},
    )


def terminos(request):
    return render(
        request,
        "cuentas/legales/terminos.html",
        {"version": settings.TERMINOS_VERSION},
    )


def privacidad(request):
    return render(
        request,
        "cuentas/legales/privacidad.html",
        {"version": settings.PRIVACIDAD_VERSION},
    )
