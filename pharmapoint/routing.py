from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({

    "websocket": URLRouter(
        websocket_urlpatterns
    ),
})
