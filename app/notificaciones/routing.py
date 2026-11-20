from django.urls import re_path

from .consumers import ContadoresConsumer


websocket_urlpatterns = [
    re_path(
        r"^ws/notificaciones/$",
        ContadoresConsumer.as_asgi(),
    ),
]
