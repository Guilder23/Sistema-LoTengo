import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, OuterRef, Q, Subquery
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from app.publicaciones.models import Publicacion

from .models import Conversacion, Mensaje
from .services import (
    ErrorMensaje,
    crear_mensaje,
    extension_mime_adjunto,
    marcar_mensajes_leidos,
    serializar_mensaje,
)


MAXIMO_CARACTERES_MENSAJE = 2000
MENSAJES_POR_CARGA = 50
logger = logging.getLogger(__name__)


def _listar_conversaciones(usuario):
    ultimo_mensaje = Mensaje.objects.filter(
        conversacion_id=OuterRef("pk")
    ).order_by("-enviada_en", "-pk")
    conversaciones = list(
        Conversacion.objects.filter(
            Q(interesado=usuario) | Q(publicacion__usuario=usuario)
        )
        .select_related("publicacion", "publicacion__usuario", "interesado")
        .annotate(
            ultimo_mensaje=Subquery(ultimo_mensaje.values("contenido")[:1]),
            ultimo_adjunto=Subquery(ultimo_mensaje.values("tipo_adjunto")[:1]),
            ultimo_remitente_id=Subquery(
                ultimo_mensaje.values("remitente_id")[:1]
            ),
            mensajes_no_leidos=Count(
                "mensajes",
                filter=Q(mensajes__leida_en__isnull=True)
                & ~Q(mensajes__remitente=usuario),
            ),
        )
    )
    for conversacion in conversaciones:
        conversacion.persona_contacto = (
            conversacion.publicacion.usuario
            if conversacion.interesado_id == usuario.pk
            else conversacion.interesado
        )
    return conversaciones


def _es_participante(conversacion, usuario):
    return usuario.pk in {
        conversacion.interesado_id,
        conversacion.publicacion.usuario_id,
    }


def _transmitir_mensaje(conversacion_id, mensaje):
    try:
        async_to_sync(get_channel_layer().group_send)(
            f"conversacion_{conversacion_id}",
            {"type": "chat.mensaje", "mensaje": mensaje},
        )
        return True
    except Exception:
        logger.exception(
            "El mensaje %s se guardó, pero no se pudo transmitir en vivo.",
            mensaje.get("id"),
        )
        return False


def _requiere_json(request):
    return (
        request.headers.get("Accept", "").startswith("application/json")
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )


@login_required
def lista(request):
    return render(
        request,
        "conversaciones/lista.html",
        {
            "conversaciones": _listar_conversaciones(request.user),
            "mostrar_sidebar_cuenta": True,
        },
    )


@login_required
@require_POST
def iniciar(request, publicacion_id):
    publicacion = get_object_or_404(
        Publicacion.objects.select_related("usuario"),
        pk=publicacion_id,
        estado=Publicacion.Estado.PUBLICADA,
    )
    if publicacion.usuario_id == request.user.pk:
        messages.error(request, "No puedes iniciar una conversación contigo mismo.")
        return redirect("publicaciones:detalle", pk=publicacion.pk)

    conversacion, _ = Conversacion.objects.get_or_create(
        publicacion=publicacion,
        interesado=request.user,
    )
    return redirect("conversaciones:detalle", pk=conversacion.pk)


@login_required
@require_http_methods(["GET", "POST"])
def detalle(request, pk):
    conversacion = get_object_or_404(
        Conversacion.objects.select_related(
            "publicacion",
            "publicacion__usuario",
            "interesado",
        ),
        pk=pk,
    )
    participantes = {
        conversacion.interesado_id,
        conversacion.publicacion.usuario_id,
    }
    if request.user.pk not in participantes:
        raise Http404

    if request.method == "POST":
        archivos = request.FILES.getlist("archivo")
        try:
            if len(archivos) > 1:
                raise ErrorMensaje("Adjunta un solo archivo por mensaje.")
            datos_mensaje = crear_mensaje(
                conversacion.pk,
                request.user,
                request.POST.get("contenido", ""),
                archivos[0] if archivos else None,
            )
        except ErrorMensaje as error:
            if _requiere_json(request):
                return JsonResponse({"error": str(error)}, status=400)
            messages.error(request, str(error))
            return redirect("conversaciones:detalle", pk=conversacion.pk)

        tiempo_real = _transmitir_mensaje(conversacion.pk, datos_mensaje)
        if _requiere_json(request):
            return JsonResponse(
                {"mensaje": datos_mensaje, "tiempo_real": tiempo_real},
                status=201,
            )
        if not tiempo_real:
            messages.warning(
                request,
                "El mensaje se guardó, pero no se pudo actualizar en tiempo real.",
            )
        return redirect("conversaciones:detalle", pk=conversacion.pk)

    marcar_mensajes_leidos(conversacion.pk, request.user.pk)
    mensajes_descendentes = list(
        conversacion.mensajes.select_related("remitente")
        .order_by("-enviada_en", "-pk")[: MENSAJES_POR_CARGA + 1]
    )
    hay_mensajes_anteriores = len(mensajes_descendentes) > MENSAJES_POR_CARGA
    mensajes = list(reversed(mensajes_descendentes[:MENSAJES_POR_CARGA]))
    persona_contacto = (
        conversacion.publicacion.usuario
        if conversacion.interesado_id == request.user.pk
        else conversacion.interesado
    )
    return render(
        request,
        "conversaciones/detalle.html",
        {
            "conversacion": conversacion,
            "conversaciones": _listar_conversaciones(request.user),
            "mensajes": mensajes,
            "hay_mensajes_anteriores": hay_mensajes_anteriores,
            "persona_contacto": persona_contacto,
            "puede_ver_publicacion": (
                conversacion.publicacion.estado == Publicacion.Estado.PUBLICADA
                or conversacion.publicacion.usuario_id == request.user.pk
            ),
            "maximo_caracteres_mensaje": MAXIMO_CARACTERES_MENSAJE,
            "mostrar_sidebar_cuenta": True,
            "websocket_url": f"/ws/conversaciones/{conversacion.pk}/",
            "mensajes_anteriores_url": reverse(
                "conversaciones:mensajes_anteriores",
                args=(conversacion.pk,),
            ),
        },
    )


@login_required
@require_GET
def mensajes_anteriores(request, pk):
    conversacion = get_object_or_404(Conversacion.objects.select_related("publicacion"), pk=pk)
    if not _es_participante(conversacion, request.user):
        raise Http404

    anterior = request.GET.get("antes", "")
    if not anterior.isascii() or not anterior.isdecimal() or len(anterior) > 20:
        return JsonResponse({"error": "El cursor de mensajes no es válido."}, status=400)

    mensajes = list(
        Mensaje.objects.filter(
            conversacion=conversacion,
            pk__lt=int(anterior),
        )
        .select_related("remitente")
        .order_by("-enviada_en", "-pk")[: MENSAJES_POR_CARGA + 1]
    )
    hay_mas = len(mensajes) > MENSAJES_POR_CARGA
    mensajes = list(reversed(mensajes[:MENSAJES_POR_CARGA]))
    return JsonResponse(
        {
            "mensajes": [serializar_mensaje(mensaje) for mensaje in mensajes],
            "hay_mas": hay_mas,
        }
    )


@login_required
@require_GET
def adjunto(request, pk, mensaje_id):
    conversacion = get_object_or_404(
        Conversacion.objects.select_related("publicacion"),
        pk=pk,
    )
    if not _es_participante(conversacion, request.user):
        raise Http404
    mensaje = get_object_or_404(
        Mensaje,
        pk=mensaje_id,
        conversacion=conversacion,
    )
    if not mensaje.archivo or not mensaje.tipo_adjunto:
        raise Http404

    archivo = mensaje.archivo.open("rb")
    respuesta = FileResponse(
        archivo,
        content_type=extension_mime_adjunto(mensaje),
    )
    respuesta["Content-Disposition"] = "inline"
    respuesta["Cache-Control"] = "private, no-store"
    respuesta["X-Content-Type-Options"] = "nosniff"
    return respuesta
