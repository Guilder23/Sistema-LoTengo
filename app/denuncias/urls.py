from django.urls import path

from . import views


app_name = "denuncias"

urlpatterns = [
    path("", views.mis_denuncias, name="mis_denuncias"),
    path("nueva/", views.crear, name="crear"),
    path("<int:denuncia_id>/evidencia/", views.descargar_evidencia, name="evidencia"),
    path("usuarios/<int:usuario_id>/bloquear/", views.bloquear_usuario, name="bloquear"),
    path(
        "conversaciones/<int:conversacion_id>/silenciar/",
        views.silenciar_conversacion,
        name="silenciar",
    ),
]
