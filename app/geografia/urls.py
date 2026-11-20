from django.urls import path

from . import views


app_name = "geografia"

urlpatterns = [
    path("departamentos/", views.departamentos, name="departamentos"),
    path("departamentos/crear/", views.departamento_crear, name="departamento_crear"),
    path("departamentos/<int:pk>/", views.departamento_detalle, name="departamento_detalle"),
    path("departamentos/<int:pk>/editar/", views.departamento_editar, name="departamento_editar"),
    path("departamentos/<int:pk>/eliminar/", views.departamento_eliminar, name="departamento_eliminar"),
    path("municipios/", views.municipios, name="municipios"),
    path("municipios/crear/", views.municipio_crear, name="municipio_crear"),
    path("municipios/<int:pk>/", views.municipio_detalle, name="municipio_detalle"),
    path("municipios/<int:pk>/editar/", views.municipio_editar, name="municipio_editar"),
    path("municipios/<int:pk>/eliminar/", views.municipio_eliminar, name="municipio_eliminar"),
]
