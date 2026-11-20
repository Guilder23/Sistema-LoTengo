from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from app.publicaciones.imagenes import ErrorImagen, preparar_imagen

from .models import Conversacion, Mensaje


MAXIMO_CARACTERES_MENSAJE = 2000
MAXIMO_AUDIO_BYTES = 20 * 1024 * 1024


class ErrorMensaje(ValueError):
    pass


def _preparar_adjunto(archivo):
    if not archivo or archivo.size == 0:
        raise ErrorMensaje("El archivo está vacío.")

    cabecera = archivo.read(16)
    archivo.seek(0)

    es_imagen = (
        cabecera.startswith(b"\xff\xd8\xff")
        or cabecera.startswith(b"\x89PNG\r\n\x1a\n")
        or (cabecera.startswith(b"RIFF") and cabecera[8:12] == b"WEBP")
    )
    if es_imagen:
        try:
            return Mensaje.TipoAdjunto.IMAGEN, preparar_imagen(archivo)
        except ErrorImagen as error:
            raise ErrorMensaje(str(error)) from error

    extension = None
    if cabecera.startswith(b"\x1a\x45\xdf\xa3"):
        extension = "webm"
    elif cabecera.startswith(b"OggS"):
        extension = "ogg"
    elif cabecera.startswith(b"RIFF") and cabecera[8:12] == b"WAVE":
        extension = "wav"
    elif cabecera.startswith(b"ID3") or (
        len(cabecera) > 1
        and cabecera[0] == 0xFF
        and cabecera[1] & 0xE0 == 0xE0
    ):
        extension = "mp3"
    elif cabecera[4:8] == b"ftyp":
        extension = "m4a"

    if extension is None:
        raise ErrorMensaje("Adjunta una imagen JPG, PNG, WEBP o un audio compatible.")
    if archivo.size > MAXIMO_AUDIO_BYTES:
        raise ErrorMensaje("El audio no puede superar los 20 MB.")

    archivo.name = f"{uuid4().hex}.{extension}"
    return Mensaje.TipoAdjunto.AUDIO, archivo


def _serializar_mensaje(mensaje):
    adjunto_url = ""
    if mensaje.archivo:
        adjunto_url = reverse(
            "conversaciones:adjunto",
            args=(mensaje.conversacion_id, mensaje.pk),
        )
    return {
        "id": mensaje.pk,
        "remitente_id": mensaje.remitente_id,
        "contenido": mensaje.contenido,
        "tipo_adjunto": mensaje.tipo_adjunto,
        "adjunto_url": adjunto_url,
        "enviada_en": mensaje.enviada_en.isoformat(),
    }


def serializar_mensaje(mensaje):
    return _serializar_mensaje(mensaje)


@transaction.atomic
def crear_mensaje(conversacion_id, remitente, contenido="", archivo=None):
    conversacion = (
        Conversacion.objects.select_related("publicacion")
        .filter(pk=conversacion_id)
        .first()
    )
    if conversacion is None:
        raise Conversacion.DoesNotExist

    participantes = {
        conversacion.interesado_id,
        conversacion.publicacion.usuario_id,
    }
    if remitente.pk not in participantes:
        raise PermissionError("No participas en esta conversación.")

    if not isinstance(contenido, str):
        raise ErrorMensaje("El mensaje debe ser texto.")
    contenido = contenido.strip()
    if len(contenido) > MAXIMO_CARACTERES_MENSAJE:
        raise ErrorMensaje(
            f"El mensaje no puede superar {MAXIMO_CARACTERES_MENSAJE} caracteres."
        )
    if not contenido and archivo is None:
        raise ErrorMensaje("Escribe un mensaje o adjunta una imagen o un audio.")

    tipo_adjunto = ""
    archivo_preparado = None
    if archivo is not None:
        tipo_adjunto, archivo_preparado = _preparar_adjunto(archivo)

    mensaje = Mensaje(
        conversacion=conversacion,
        remitente=remitente,
        contenido=contenido,
        tipo_adjunto=tipo_adjunto,
    )
    if archivo_preparado is not None:
        mensaje.archivo = archivo_preparado

    try:
        mensaje.full_clean()
    except ValidationError as error:
        raise ErrorMensaje("No se pudo validar el mensaje.") from error

    mensaje.save()
    Conversacion.objects.filter(pk=conversacion.pk).update(
        actualizada_en=timezone.now()
    )
    return _serializar_mensaje(mensaje)


def marcar_mensajes_leidos(conversacion_id, usuario_id):
    Mensaje.objects.filter(
        conversacion_id=conversacion_id,
        leida_en__isnull=True,
    ).exclude(remitente_id=usuario_id).update(leida_en=timezone.now())


def extension_mime_adjunto(mensaje):
    if mensaje.tipo_adjunto == Mensaje.TipoAdjunto.IMAGEN:
        extension = mensaje.archivo.name.rsplit(".", 1)[-1].lower()
        return {
            "jpg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
        }.get(extension, "application/octet-stream")
    extension = mensaje.archivo.name.rsplit(".", 1)[-1].lower()
    return {
        "webm": "audio/webm",
        "ogg": "audio/ogg",
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "m4a": "audio/mp4",
    }.get(extension, "application/octet-stream")
