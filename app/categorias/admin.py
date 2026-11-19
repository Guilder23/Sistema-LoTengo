from django.contrib import admin

from .models import Categoria


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "slug", "activa", "orden"]
    list_filter = ["activa"]
    search_fields = ["nombre"]
    prepopulated_fields = {"slug": ["nombre"]}
    ordering = ["orden", "nombre"]
