from django.contrib import admin

from .models import ImagenPublicacion, Publicacion


class ImagenPublicacionInline(admin.TabularInline):
    model = ImagenPublicacion
    extra = 0


@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = [
        "titulo",
        "tipo",
        "categoria",
        "usuario",
        "estado",
        "creada_en",
    ]
    list_filter = ["tipo", "estado", "categoria", "ubicacion__departamento"]
    search_fields = ["titulo", "descripcion", "usuario__email"]
    readonly_fields = ["creada_en", "actualizada_en"]
    inlines = [ImagenPublicacionInline]
