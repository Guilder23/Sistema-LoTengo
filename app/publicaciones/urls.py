from django.urls import path

from . import views


app_name = "publicaciones"

urlpatterns = [
    path("", views.listado, name="listado"),
    path("municipios/", views.municipios_por_departamento, name="municipios_por_departamento"),
    path("mis-publicaciones/", views.mis_publicaciones, name="mis_publicaciones"),
    path("nueva/", views.crear, name="crear"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/eliminar/", views.eliminar, name="eliminar"),
    path("<int:pk>/estado/", views.cambiar_estado, name="cambiar_estado"),
    path("<int:pk>/", views.detalle, name="detalle"),
]
