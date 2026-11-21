from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from app.denuncias.models import Denuncia
from app.publicaciones.models import Publicacion

from .models import DecisionModeracion


@staff_member_required
def bandeja(request):
    base_denuncias = Denuncia.objects.select_related(
        "denunciante",
        "denunciado",
        "publicacion",
        "mensaje",
    ).prefetch_related("decisiones__moderador")
    conteos = dict(
        base_denuncias.values("estado")
        .annotate(cantidad=Count("pk"))
        .values_list("estado", "cantidad")
    )
    estados = [
        {
            "valor": "",
            "etiqueta": "Todas",
            "cantidad": sum(conteos.values()),
        }
    ]
    estados.extend(
        {
            "valor": valor,
            "etiqueta": etiqueta,
            "cantidad": conteos.get(valor, 0),
        }
        for valor, etiqueta in Denuncia.Estado.choices
    )
    estado = request.GET.get("estado", "")
    if estado in Denuncia.Estado.values:
        denuncias = base_denuncias.filter(estado=estado)
    else:
        denuncias = base_denuncias
    pagina = Paginator(denuncias, 25).get_page(request.GET.get("pagina"))
    return render(
        request,
        "moderacion/bandeja.html",
        {
            "pagina": pagina,
            "estados": estados,
            "estado_seleccionado": estado,
            "acciones": DecisionModeracion.Accion.choices,
            "mostrar_sidebar_cuenta": True,
        },
    )


def _usuario_denunciado(denuncia):
    if denuncia.denunciado_id:
        return denuncia.denunciado
    if denuncia.publicacion_id:
        return denuncia.publicacion.usuario
    if denuncia.mensaje_id:
        return denuncia.mensaje.remitente
    return None


@staff_member_required
@require_POST
def decidir(request, denuncia_id):
    denuncia = get_object_or_404(
        Denuncia.objects.select_related(
            "denunciado",
            "publicacion__usuario",
            "mensaje__remitente",
        ),
        pk=denuncia_id,
    )
    accion = request.POST.get("accion", "")
    nota = request.POST.get("nota", "").strip()
    dias = request.POST.get("dias", "")
    if accion not in DecisionModeracion.Accion.values or len(nota) < 5 or len(nota) > 2000:
        messages.error(request, "Selecciona una acción válida e incluye una nota de al menos 5 caracteres.")
        return redirect("moderacion:bandeja")

    usuario = _usuario_denunciado(denuncia)
    publicacion = denuncia.publicacion
    requiere_usuario = accion in {
        DecisionModeracion.Accion.SUSPENDER_USUARIO,
        DecisionModeracion.Accion.BLOQUEAR_USUARIO,
        DecisionModeracion.Accion.REACTIVAR_USUARIO,
    }
    requiere_publicacion = accion in {
        DecisionModeracion.Accion.OCULTAR_PUBLICACION,
        DecisionModeracion.Accion.RESTAURAR_PUBLICACION,
    }
    if (requiere_usuario and (usuario is None or usuario.is_staff)):
        messages.error(request, "Esta acción requiere una cuenta denunciada que no pertenezca al personal.")
        return redirect("moderacion:bandeja")
    if requiere_publicacion and publicacion is None:
        messages.error(request, "Esta acción requiere una denuncia asociada a una publicación.")
        return redirect("moderacion:bandeja")
    if accion == DecisionModeracion.Accion.SUSPENDER_USUARIO:
        if not dias.isascii() or not dias.isdecimal() or not 1 <= int(dias) <= 365:
            messages.error(request, "La suspensión debe durar entre 1 y 365 días.")
            return redirect("moderacion:bandeja")

    with transaction.atomic():
        if accion == DecisionModeracion.Accion.OCULTAR_PUBLICACION:
            Publicacion.objects.filter(pk=publicacion.pk).update(
                oculta_por_moderacion=True
            )
        elif accion == DecisionModeracion.Accion.RESTAURAR_PUBLICACION:
            Publicacion.objects.filter(pk=publicacion.pk).update(
                oculta_por_moderacion=False
            )
        elif accion == DecisionModeracion.Accion.SUSPENDER_USUARIO:
            usuario.suspendido_hasta = timezone.now() + timedelta(days=int(dias))
            usuario.save(update_fields=["suspendido_hasta"])
        elif accion == DecisionModeracion.Accion.BLOQUEAR_USUARIO:
            usuario.is_active = False
            usuario.suspendido_hasta = None
            usuario.save(update_fields=["is_active", "suspendido_hasta"])
        elif accion == DecisionModeracion.Accion.REACTIVAR_USUARIO:
            usuario.is_active = True
            usuario.suspendido_hasta = None
            usuario.save(update_fields=["is_active", "suspendido_hasta"])

        if accion == DecisionModeracion.Accion.RESOLVER:
            denuncia.estado = Denuncia.Estado.RESUELTA
        elif accion == DecisionModeracion.Accion.RECHAZAR:
            denuncia.estado = Denuncia.Estado.RECHAZADA
        elif denuncia.estado in {
            Denuncia.Estado.PENDIENTE,
            Denuncia.Estado.EN_REVISION,
        }:
            denuncia.estado = Denuncia.Estado.EN_REVISION
        denuncia.respuesta = nota
        denuncia.save(update_fields=["estado", "respuesta", "actualizada_en"])
        DecisionModeracion.objects.create(
            denuncia=denuncia,
            moderador=request.user,
            accion=accion,
            nota=nota,
            duracion_dias=(
                int(dias)
                if accion == DecisionModeracion.Accion.SUSPENDER_USUARIO
                else None
            ),
        )

    messages.success(request, "La decisión quedó registrada en el historial.")
    return redirect("moderacion:bandeja")
