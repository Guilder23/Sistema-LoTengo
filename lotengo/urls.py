from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from app.notificaciones import views as notificaciones_views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("app.cuentas.urls")),
    path("perfil/", include("app.perfiles.urls")),
    path("publicaciones/", include("app.publicaciones.urls")),
    path("conversaciones/", include("app.conversaciones.urls")),
    path("denuncias/", include("app.denuncias.urls")),
    path("administracion/moderacion/", include("app.moderacion.urls")),
    path(
        "notificaciones/",
        include("app.notificaciones.urls"),
    ),
    path("service-worker.js", notificaciones_views.service_worker, name="service_worker"),
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
