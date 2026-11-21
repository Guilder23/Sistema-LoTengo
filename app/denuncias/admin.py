from django.contrib import admin

from .models import BloqueoUsuario, ConversacionSilenciada, Denuncia


@admin.register(Denuncia)
class DenunciaAdmin(admin.ModelAdmin):
    list_display = ("id", "motivo", "denunciante", "denunciado", "estado", "creada_en")
    list_filter = ("estado", "motivo")
    search_fields = ("descripcion", "denunciante__email", "denunciado__email")
    readonly_fields = ("creada_en", "actualizada_en")


admin.site.register(BloqueoUsuario)
admin.site.register(ConversacionSilenciada)
