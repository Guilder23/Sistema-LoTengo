from django.contrib import admin

from .models import DecisionModeracion


@admin.register(DecisionModeracion)
class DecisionModeracionAdmin(admin.ModelAdmin):
    list_display = ("denuncia", "accion", "moderador", "creada_en")
    list_filter = ("accion", "creada_en")
    readonly_fields = (
        "denuncia",
        "moderador",
        "accion",
        "nota",
        "duracion_dias",
        "creada_en",
    )
