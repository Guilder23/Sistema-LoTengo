from django.urls import path

from . import views


app_name = "cuentas"

urlpatterns = [
    path("registro/", views.registro, name="registro"),
    path("iniciar-sesion/", views.iniciar_sesion, name="iniciar_sesion"),
    path("cerrar-sesion/", views.cerrar_sesion, name="cerrar_sesion"),
    path("panel/", views.panel, name="panel"),
    path("verificar-correo/<uidb64>/<token>/", views.verificar_correo, name="verificar_correo"),
    path("verificacion-enviada/", views.verificacion_enviada, name="verificacion_enviada"),
    path("reenviar-verificacion/", views.reenviar_verificacion, name="reenviar_verificacion"),
    path("restaurar-contrasena/", views.solicitar_restauracion, name="solicitar_restauracion"),
    path("restauracion-solicitada/", views.restauracion_solicitada, name="restauracion_solicitada"),
    path(
        "restablecer-contrasena/<uidb64>/<token>/",
        views.restablecer_contrasena,
        name="restablecer_contrasena",
    ),
    path("contrasena-actualizada/", views.contrasena_actualizada, name="contrasena_actualizada"),
    path("terminos/", views.terminos, name="terminos"),
    path("privacidad/", views.privacidad, name="privacidad"),
]
