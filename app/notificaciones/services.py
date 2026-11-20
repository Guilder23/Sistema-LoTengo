import json
import logging
from urllib.parse import urlsplit

import requests
from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from pywebpush import WebPushException, webpush

from .models import Notificacion, PreferenciaNotificaciones, SuscripcionPush
from .realtime import publicar_actualizacion_contadores


logger = logging.getLogger(__name__)
DOMINIOS_PUSH_PERMITIDOS = {
    "fcm.googleapis.com",
    "updates.push.services.mozilla.com",
    "web.push.apple.com",
}


def push_configurado():
    return bool(
        settings.WEBPUSH_VAPID_PUBLIC_KEY
        and settings.WEBPUSH_VAPID_PRIVATE_KEY
        and settings.WEBPUSH_VAPID_SUBJECT
    )


def endpoint_push_valido(endpoint):
    try:
        parsed = urlsplit(endpoint)
        puerto = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and parsed.hostname in DOMINIOS_PUSH_PERMITIDOS
        and parsed.username is None
        and parsed.password is None
        and puerto in {None, 443}
        and bool(parsed.path)
    )


def _enviar_push(notificacion):
    if not push_configurado():
        return

    datos = json.dumps(
        {
            "title": notificacion.titulo,
            "body": notificacion.mensaje,
            "url": notificacion.url,
        },
        ensure_ascii=True,
    )
    suscripciones = SuscripcionPush.objects.filter(
        usuario_id=notificacion.usuario_id
    )
    for suscripcion in suscripciones.iterator():
        try:
            webpush(
                subscription_info={
                    "endpoint": suscripcion.endpoint,
                    "keys": {
                        "p256dh": suscripcion.clave_publica,
                        "auth": suscripcion.clave_auth,
                    },
                },
                data=datos,
                vapid_private_key=settings.WEBPUSH_VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.WEBPUSH_VAPID_SUBJECT},
                ttl=60,
                timeout=5,
            )
        except WebPushException as error:
            response = getattr(error, "response", None)
            if response is not None and response.status_code in {404, 410}:
                suscripcion.delete()
                continue
            logger.warning(
                "Falló el envío push de la notificación %s (tipo de error: %s).",
                notificacion.pk,
                type(error).__name__,
            )
        except requests.exceptions.RequestException as error:
            logger.warning(
                "Falló el envío push de la notificación %s (tipo de error: %s).",
                notificacion.pk,
                type(error).__name__,
            )


def enviar_push_notificaciones(ids_notificaciones):
    if not push_configurado():
        return
    for notificacion in Notificacion.objects.filter(
        pk__in=ids_notificaciones
    ).iterator():
        _enviar_push(notificacion)


def crear_notificacion(usuario, tipo, titulo, mensaje, url):
    notificacion = Notificacion.objects.create(
        usuario=usuario,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        url=url,
    )
    transaction.on_commit(
        lambda usuario_id=usuario.pk: publicar_actualizacion_contadores(usuario_id),
        robust=True,
    )
    transaction.on_commit(
        lambda: enviar_push_notificaciones((notificacion.pk,)),
        robust=True,
    )
    return notificacion


def notificar_mensaje_recibido(conversacion, remitente):
    if conversacion.interesado_id == remitente.pk:
        destinatario = conversacion.publicacion.usuario
    else:
        destinatario = conversacion.interesado

    nombre = remitente.get_full_name().strip() or "Alguien"
    return crear_notificacion(
        usuario=destinatario,
        tipo=Notificacion.Tipo.MENSAJE,
        titulo="Nuevo mensaje",
        mensaje=f"{nombre} te envió un mensaje.",
        url=reverse(
            "conversaciones:detalle",
            args=(conversacion.pk,),
        ),
    )


def notificar_nueva_publicacion(publicacion):
    if publicacion.estado != publicacion.Estado.PUBLICADA:
        return []

    preferencias = PreferenciaNotificaciones.objects.filter(
        nuevas_publicaciones=True
    ).exclude(usuario_id=publicacion.usuario_id)
    municipio = publicacion.ubicacion.municipio.nombre
    notificaciones = [
        Notificacion(
            usuario_id=preferencia.usuario_id,
            tipo=Notificacion.Tipo.NUEVA_PUBLICACION,
            titulo="Nueva publicación",
            mensaje=f"{publicacion.titulo} · {municipio}",
            url=reverse("publicaciones:detalle", args=(publicacion.pk,)),
        )
        for preferencia in preferencias.only("usuario_id").iterator()
    ]
    if not notificaciones:
        return []

    usuarios_id = {notificacion.usuario_id for notificacion in notificaciones}
    creadas = Notificacion.objects.bulk_create(notificaciones)
    ids_notificaciones = tuple(
        notificacion.pk for notificacion in creadas if notificacion.pk is not None
    )
    if ids_notificaciones:
        transaction.on_commit(
            lambda: enviar_push_notificaciones(ids_notificaciones),
            robust=True,
        )
    for usuario_id in usuarios_id:
        transaction.on_commit(
            lambda usuario_id=usuario_id: publicar_actualizacion_contadores(
                usuario_id
            ),
            robust=True,
        )
    return creadas


def marcar_notificaciones_conversacion_leidas(usuario_id, conversacion_id):
    return Notificacion.objects.filter(
        usuario_id=usuario_id,
        tipo=Notificacion.Tipo.MENSAJE,
        url=reverse("conversaciones:detalle", args=(conversacion_id,)),
        leida_en__isnull=True,
    ).update(leida_en=timezone.now())
