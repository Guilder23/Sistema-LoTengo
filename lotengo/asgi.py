import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lotengo.settings")

django_asgi_application = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from app.conversaciones.routing import websocket_urlpatterns as conversation_websocket_urlpatterns
from app.notificaciones.routing import websocket_urlpatterns as notification_websocket_urlpatterns


websocket_urlpatterns = (
    conversation_websocket_urlpatterns + notification_websocket_urlpatterns
)


application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    }
)
