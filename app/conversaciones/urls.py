from django.urls import path

from . import views


app_name = "conversaciones"

urlpatterns = [
    path("", views.lista, name="lista"),
    path(
        "publicacion/<int:publicacion_id>/contactar/",
        views.iniciar,
        name="iniciar",
    ),
    path(
        "<int:pk>/mensajes/anteriores/",
        views.mensajes_anteriores,
        name="mensajes_anteriores",
    ),
    path("<int:pk>/ajustes/", views.ajustes, name="ajustes"),
    path(
        "<int:pk>/adjuntos/<int:mensaje_id>/",
        views.adjunto,
        name="adjunto",
    ),
    path("<int:pk>/", views.detalle, name="detalle"),
]
