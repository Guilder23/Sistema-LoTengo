import logging
from smtplib import SMTPException

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from app.cuentas.correos import ErrorEnvioCorreo, enviar_verificacion
from app.categorias.models import Categoria
from app.geografia.models import Departamento
from app.publicaciones.models import Publicacion

from .forms import FormularioEditarPerfil
from .models import Perfil


logger = logging.getLogger(__name__)


def publico(request, pk):
    usuario = get_object_or_404(
        get_user_model().objects.select_related("perfil"),
        pk=pk,
        is_active=True,
    )
    perfil, _ = Perfil.objects.get_or_create(usuario=usuario)
    publicaciones = (
        Publicacion.objects.filter(
            usuario=usuario,
            estado=Publicacion.Estado.PUBLICADA,
        )
        .select_related(
            "categoria",
            "ubicacion",
            "ubicacion__departamento",
            "ubicacion__municipio",
        )
        .prefetch_related("imagenes")
        .order_by("-creada_en")
    )
    pagina = Paginator(publicaciones, 12).get_page(request.GET.get("pagina"))
    return render(
        request,
        "perfiles/publico.html",
        {
            "usuario_publico": usuario,
            "perfil_publico": perfil,
            "pagina": pagina,
            "categorias": Categoria.objects.filter(activa=True),
            "departamentos": Departamento.objects.all(),
            "filtros": {
                "q": "",
                "tipo": "",
                "categoria": "",
                "departamento": "",
                "municipio": "",
            },
            "mostrar_sidebar_cuenta": False,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def editar(request):
    perfil, _ = Perfil.objects.get_or_create(usuario=request.user)
    formulario = FormularioEditarPerfil(
        request.user,
        perfil,
        data=request.POST if request.method == "POST" else None,
        files=request.FILES if request.method == "POST" else None,
    )

    if request.method == "POST" and formulario.is_valid():
        try:
            correo_cambiado, almacenamiento, foto_anterior, foto_actual = (
                formulario.guardar_cambios()
            )
        except IntegrityError:
            formulario.add_error(
                "email",
                "Ya existe una cuenta con ese correo electrónico.",
            )
        else:
            if foto_anterior and foto_anterior != foto_actual:
                try:
                    almacenamiento.delete(foto_anterior)
                except OSError:
                    logger.exception(
                        "No se pudo eliminar la foto anterior del usuario %s.",
                        request.user.pk,
                    )

            messages.success(request, "Tu información se actualizó correctamente.")
            if correo_cambiado:
                try:
                    enviar_verificacion(request, request.user)
                except (ErrorEnvioCorreo, SMTPException, OSError):
                    logger.exception(
                        "No se pudo verificar el nuevo correo del usuario %s.",
                        request.user.pk,
                    )
                    messages.warning(
                        request,
                        "Tus cambios se guardaron, pero no se pudo enviar el "
                        "enlace de verificación. Solicita otro desde la opción "
                        "«Reenviar verificación».",
                    )
                    return redirect("cuentas:reenviar_verificacion")
                else:
                    messages.info(
                        request,
                        "Enviamos un enlace a tu nuevo correo. Debes verificarlo "
                        "antes de volver a iniciar sesión.",
                    )
                    return redirect("cuentas:verificacion_enviada")
            return redirect("perfiles:editar")

    return render(
        request,
        "perfiles/editar.html",
        {
            "formulario": formulario,
            "perfil": perfil,
            "mostrar_sidebar_cuenta": True,
        },
    )
