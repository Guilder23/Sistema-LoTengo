from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("app.cuentas.urls")),
    path("publicaciones/", include("app.publicaciones.urls")),
    path(
        "administracion/categorias/",
        include("app.categorias.urls"),
    ),
    path(
        "administracion/",
        include("app.geografia.urls"),
    ),
    path("", include("app.general.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
