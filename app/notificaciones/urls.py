from django.urls import path

from . import views


app_name = "notificaciones"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("resumen/", views.resumen, name="resumen"),
    path("preferencias/", views.preferencias, name="preferencias"),
    path("marcar-todas-leidas/", views.marcar_todas_leidas, name="marcar_todas_leidas"),
    path("push/configuracion/", views.configuracion_push, name="configuracion_push"),
    path("push/suscripciones/", views.registrar_suscripcion, name="registrar_suscripcion"),
    path(
        "push/suscripciones/eliminar/",
        views.eliminar_suscripcion,
        name="eliminar_suscripcion",
    ),
    path("<int:pk>/abrir/", views.abrir, name="abrir"),
]
