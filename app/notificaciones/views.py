import json
import re
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import Notificacion, PreferenciaNotificaciones, SuscripcionPush
from .realtime import obtener_contadores_usuario, publicar_actualizacion_contadores
from .services import endpoint_push_valido, push_configurado


PATRON_CLAVE_PUSH = re.compile(r"^[A-Za-z0-9_-]+$")
TAMANO_MAXIMO_SOLICITUD_PUSH = 4096


def _leer_json(request):
    if len(request.body) > TAMANO_MAXIMO_SOLICITUD_PUSH:
        return None
    try:
        datos = json.loads(request.body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return datos if isinstance(datos, dict) else None


def _es_clave_push_valida(valor, maximo):
    return (
        isinstance(valor, str)
        and 1 <= len(valor) <= maximo
        and PATRON_CLAVE_PUSH.fullmatch(valor) is not None
    )


@login_required
@require_GET
def lista(request):
    preferencia, _ = PreferenciaNotificaciones.objects.get_or_create(
        usuario=request.user
    )
    notificaciones = Notificacion.objects.filter(
        usuario=request.user,
        tipo=Notificacion.Tipo.NUEVA_PUBLICACION,
    )
    pagina = Paginator(notificaciones, 20).get_page(request.GET.get("pagina"))
    return render(
        request,
        "notificaciones/lista.html",
        {
            "pagina": pagina,
            "preferencia": preferencia,
            "push_configurado": push_configurado(),
            "mostrar_sidebar_cuenta": True,
        },
    )


@login_required
@require_POST
def preferencias(request):
    preferencia, _ = PreferenciaNotificaciones.objects.get_or_create(
        usuario=request.user
    )
    preferencia.nuevas_publicaciones = (
        request.POST.get("nuevas_publicaciones") == "on"
    )
    preferencia.save(update_fields=["nuevas_publicaciones", "actualizada_en"])
    return redirect("notificaciones:lista")


@login_required
@require_GET
def resumen(request):
    notificaciones = Notificacion.objects.filter(
        usuario=request.user,
        tipo=Notificacion.Tipo.NUEVA_PUBLICACION,
    )
    recientes = notificaciones[:8]
    contadores = obtener_contadores_usuario(request.user.pk)
    return JsonResponse(
        {
            "sin_leer": contadores["notificaciones_sin_leer"],
            "chats_sin_leer": contadores["chats_sin_leer"],
            "mensajes_por_conversacion": contadores["mensajes_por_conversacion"],
            "notificaciones": [
                {
                    "id": notificacion.pk,
                    "titulo": notificacion.titulo,
                    "mensaje": notificacion.mensaje,
                    "leida": notificacion.leida_en is not None,
                    "url": reverse(
                        "notificaciones:abrir",
                        args=(notificacion.pk,),
                    ),
                }
                for notificacion in recientes
            ],
        },
        headers={"Cache-Control": "private, no-store"},
    )


@login_required
@require_POST
def marcar_todas_leidas(request):
    actualizadas = Notificacion.objects.filter(
        usuario=request.user,
        tipo=Notificacion.Tipo.NUEVA_PUBLICACION,
        leida_en__isnull=True,
    ).update(leida_en=timezone.now())
    if actualizadas:
        publicar_actualizacion_contadores(request.user.pk)
    return redirect("notificaciones:lista")


@login_required
@require_GET
def abrir(request, pk):
    notificacion = get_object_or_404(
        Notificacion,
        pk=pk,
        usuario=request.user,
    )
    if notificacion.leida_en is None:
        notificacion.leida_en = timezone.now()
        notificacion.save(update_fields=["leida_en"])
        publicar_actualizacion_contadores(request.user.pk)

    destino = notificacion.url
    if not destino.startswith("/") or destino.startswith("//") or "\\" in destino:
        destino = reverse("notificaciones:lista")
    return redirect(destino)


@login_required
@require_GET
def configuracion_push(_request):
    habilitado = push_configurado()
    return JsonResponse(
        {
            "habilitado": habilitado,
            "clave_publica": settings.WEBPUSH_VAPID_PUBLIC_KEY if habilitado else "",
            "dispositivos_activos": SuscripcionPush.objects.filter(
                usuario=_request.user
            ).count(),
        },
        headers={"Cache-Control": "private, no-store"},
    )


@login_required
@require_POST
def registrar_suscripcion(request):
    if not push_configurado():
        return JsonResponse(
            {"error": "Las notificaciones del navegador no están configuradas."},
            status=503,
        )
    datos = _leer_json(request)
    if datos is None:
        return JsonResponse({"error": "La solicitud no es válida."}, status=400)

    endpoint = datos.get("endpoint")
    claves = datos.get("keys")
    if (
        not isinstance(endpoint, str)
        or len(endpoint) > 2048
        or not endpoint_push_valido(endpoint)
        or not isinstance(claves, dict)
        or not _es_clave_push_valida(claves.get("p256dh"), 256)
        or not _es_clave_push_valida(claves.get("auth"), 128)
    ):
        return JsonResponse(
            {"error": "La suscripción del navegador no es válida."},
            status=400,
        )

    suscripcion, creada = SuscripcionPush.objects.get_or_create(
        endpoint=endpoint,
        defaults={
            "usuario": request.user,
            "clave_publica": claves["p256dh"],
            "clave_auth": claves["auth"],
        },
    )
    if not creada and suscripcion.usuario_id != request.user.pk:
        return JsonResponse(
            {"error": "Este dispositivo está asociado a otra cuenta."},
            status=409,
        )
    if not creada:
        suscripcion.clave_publica = claves["p256dh"]
        suscripcion.clave_auth = claves["auth"]
        suscripcion.save(
            update_fields=["clave_publica", "clave_auth", "actualizada_en"]
        )
    return JsonResponse({"suscrita": True}, status=201 if creada else 200)


@login_required
@require_POST
def eliminar_suscripcion(request):
    datos = _leer_json(request)
    endpoint = datos.get("endpoint") if datos else None
    if (
        not isinstance(endpoint, str)
        or len(endpoint) > 2048
        or not endpoint_push_valido(endpoint)
    ):
        return JsonResponse({"error": "La suscripción no es válida."}, status=400)
    SuscripcionPush.objects.filter(
        usuario=request.user,
        endpoint=endpoint,
    ).delete()
    return JsonResponse({"suscrita": False})


def service_worker(_request):
    archivo = (
        Path(settings.BASE_DIR)
        / "static"
        / "js"
        / "notificaciones"
        / "service-worker.js"
    )
    respuesta = HttpResponse(
        archivo.read_text(encoding="utf-8"),
        content_type="application/javascript; charset=utf-8",
    )
    respuesta["Service-Worker-Allowed"] = "/"
    respuesta["Cache-Control"] = "no-cache"
    return respuesta
