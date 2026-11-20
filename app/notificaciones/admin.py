from django.contrib import admin

from .models import Notificacion, PreferenciaNotificaciones, SuscripcionPush


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ("titulo", "usuario", "tipo", "creada_en", "leida_en")
    list_filter = ("tipo", "creada_en", "leida_en")
    search_fields = ("titulo", "mensaje", "usuario__email")
    readonly_fields = ("creada_en",)


@admin.register(PreferenciaNotificaciones)
class PreferenciaNotificacionesAdmin(admin.ModelAdmin):
    list_display = ("usuario", "nuevas_publicaciones", "actualizada_en")
    list_filter = ("nuevas_publicaciones",)
    search_fields = ("usuario__email",)


@admin.register(SuscripcionPush)
class SuscripcionPushAdmin(admin.ModelAdmin):
    list_display = ("usuario", "creada_en", "actualizada_en")
    search_fields = ("usuario__email",)
    fields = ("usuario", "creada_en", "actualizada_en")
    readonly_fields = ("usuario", "creada_en", "actualizada_en")
