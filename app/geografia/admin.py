from django.contrib import admin

from .models import Departamento, Municipio


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "codigo"]
    search_fields = ["nombre", "codigo"]
    prepopulated_fields = {"codigo": ["nombre"]}


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ["nombre", "departamento"]
    list_filter = ["departamento"]
    search_fields = ["nombre", "departamento__nombre"]
