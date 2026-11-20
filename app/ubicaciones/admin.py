from django.contrib import admin

from .models import Ubicacion


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ["municipio", "departamento", "zona", "conoce_lugar_exacto"]
    list_filter = ["departamento", "conoce_lugar_exacto"]
    search_fields = ["municipio__nombre", "departamento__nombre", "zona"]
