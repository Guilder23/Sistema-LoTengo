from django.urls import path

from . import views


app_name = "perfiles"

urlpatterns = [
    path("editar/", views.editar, name="editar"),
]
