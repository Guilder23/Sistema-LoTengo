from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("app.cuentas.urls")),
    path("", include("app.general.urls")),
]
