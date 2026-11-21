from django.urls import path

from . import views


app_name = "moderacion"

urlpatterns = [
    path("", views.bandeja, name="bandeja"),
    path("<int:denuncia_id>/decidir/", views.decidir, name="decidir"),
]
