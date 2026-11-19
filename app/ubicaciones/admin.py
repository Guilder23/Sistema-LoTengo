from django.contrib import admin

from .models import Municipio, Ubicacion


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ["nombre", "departamento"]
    list_filter = ["departamento"]
    search_fields = ["nombre"]


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ["municipio", "departamento", "zona", "conoce_lugar_exacto"]
    list_filter = ["departamento", "conoce_lugar_exacto"]
    search_fields = ["municipio", "zona"]
