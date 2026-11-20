from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .models import ConexionPresencia, PresenciaUsuario


TIEMPO_EXPIRACION_PRESENCIA = timedelta(seconds=75)
ZONA_HORARIA_LA_PAZ = ZoneInfo("America/La_Paz")


def _serializar_ultima_vez(fecha):
    if fecha is None:
        return ""
    return timezone.localtime(fecha, ZONA_HORARIA_LA_PAZ).isoformat()


def _segundos_desde_ultima_vez(fecha, ahora=None):
    if fecha is None:
        return None
    ahora = ahora or timezone.now()
    return max(0, int((ahora - fecha).total_seconds()))


def obtener_estado_presencia(usuario_id):
    return obtener_estados_presencia([usuario_id])[usuario_id]


def obtener_estados_presencia(usuarios_ids):
    usuarios_ids = set(usuarios_ids)
    if not usuarios_ids:
        return {}

    ahora = timezone.now()
    en_linea_ids = set(
        ConexionPresencia.objects.filter(
            usuario_id__in=usuarios_ids,
            ultimo_latido__gte=ahora - TIEMPO_EXPIRACION_PRESENCIA,
        )
        .values_list("usuario_id", flat=True)
        .distinct()
    )
    ultimas_veces = dict(
        PresenciaUsuario.objects.filter(usuario_id__in=usuarios_ids).values_list(
            "usuario_id",
            "ultima_vez_en_linea",
        )
    )
    estados = {}
    for usuario_id in usuarios_ids:
        en_linea = usuario_id in en_linea_ids
        ultima_vez = ultimas_veces.get(usuario_id)
        estados[usuario_id] = {
            "usuario_id": usuario_id,
            "en_linea": en_linea,
            "ultima_vez": "" if en_linea else _serializar_ultima_vez(ultima_vez),
            "segundos_desde_ultima_vez": (
                None
                if en_linea
                else _segundos_desde_ultima_vez(ultima_vez, ahora)
            ),
        }
    return estados


def _limpiar_conexiones_expiradas(ahora):
    vencidas = ConexionPresencia.objects.filter(
        ultimo_latido__lt=ahora - TIEMPO_EXPIRACION_PRESENCIA,
    )
    expiradas_por_usuario = list(
        vencidas.values("usuario_id").annotate(ultimo_latido=Max("ultimo_latido"))
    )
    vencidas.delete()

    eventos = []
    for expiracion in expiradas_por_usuario:
        usuario_id = expiracion["usuario_id"]
        sigue_en_linea = ConexionPresencia.objects.filter(
            usuario_id=usuario_id,
            ultimo_latido__gte=ahora - TIEMPO_EXPIRACION_PRESENCIA,
        ).exists()
        if sigue_en_linea:
            continue

        PresenciaUsuario.objects.update_or_create(
            usuario_id=usuario_id,
            defaults={"ultima_vez_en_linea": expiracion["ultimo_latido"]},
        )
        eventos.append(
            {
                "usuario_id": usuario_id,
                "en_linea": False,
                "ultima_vez": _serializar_ultima_vez(
                    expiracion["ultimo_latido"]
                ),
                "segundos_desde_ultima_vez": _segundos_desde_ultima_vez(
                    expiracion["ultimo_latido"],
                    ahora,
                ),
            }
        )
    return eventos


@transaction.atomic
def registrar_conexion_presencia(usuario_id, canal):
    ahora = timezone.now()
    eventos_expirados = _limpiar_conexiones_expiradas(ahora)
    ConexionPresencia.objects.update_or_create(
        canal=canal,
        defaults={"usuario_id": usuario_id, "ultimo_latido": ahora},
    )
    return eventos_expirados


def actualizar_latido_presencia(usuario_id, canal):
    return ConexionPresencia.objects.filter(
        usuario_id=usuario_id,
        canal=canal,
    ).update(ultimo_latido=timezone.now()) > 0


@transaction.atomic
def cerrar_conexion_presencia(canal):
    conexion = (
        ConexionPresencia.objects.select_for_update()
        .filter(canal=canal)
        .first()
    )
    if conexion is None:
        return None

    usuario_id = conexion.usuario_id
    conexion.delete()
    ahora = timezone.now()
    sigue_en_linea = ConexionPresencia.objects.filter(
        usuario_id=usuario_id,
        ultimo_latido__gte=ahora - TIEMPO_EXPIRACION_PRESENCIA,
    ).exists()
    if sigue_en_linea:
        return {
            "usuario_id": usuario_id,
            "en_linea": True,
            "ultima_vez": "",
            "segundos_desde_ultima_vez": None,
        }

    PresenciaUsuario.objects.update_or_create(
        usuario_id=usuario_id,
        defaults={"ultima_vez_en_linea": ahora},
    )
    return {
        "usuario_id": usuario_id,
        "en_linea": False,
        "ultima_vez": _serializar_ultima_vez(ahora),
        "segundos_desde_ultima_vez": 0,
    }
