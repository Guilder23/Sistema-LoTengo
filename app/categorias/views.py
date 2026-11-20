from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods

from .models import Categoria


def _url_lista():
    return reverse("categorias:lista")


def _contexto_sidebar_cuenta():
    return {"mostrar_sidebar_cuenta": True}


def _datos_categoria(categoria):
    return {
        "nombre": categoria.nombre or "",
        "slug": categoria.slug or "",
        "activa": categoria.activa,
        "orden": categoria.orden,
    }


def _agregar_errores_modelo(errores, excepcion):
    for campo, mensajes in excepcion.message_dict.items():
        clave = "non_field_errors" if campo == "__all__" else campo
        errores.setdefault(clave, []).extend(mensajes)


def _validar_categoria(post, categoria):
    datos = {
        "nombre": post.get("nombre", "").strip(),
        "slug": post.get("slug", "").strip(),
        "activa": post.get("activa") == "on",
        "orden": post.get("orden", "0").strip(),
    }
    errores = {}
    try:
        categoria.orden = int(datos["orden"] or 0)
    except ValueError:
        categoria.orden = 0
        errores["orden"] = ["Introduce un número entero válido."]

    categoria.nombre = datos["nombre"]
    categoria.slug = datos["slug"] or slugify(datos["nombre"])
    categoria.activa = datos["activa"]
    datos["slug"] = categoria.slug

    try:
        categoria.full_clean()
    except ValidationError as excepcion:
        _agregar_errores_modelo(errores, excepcion)

    return datos, errores


@staff_member_required
def lista(request):
    categorias = Categoria.objects.all()
    return render(
        request,
        "categorias/categorias.html",
        {
            "titulo": "Gestión de categorías",
            "descripcion": "Administra las categorías disponibles para las publicaciones.",
            "categorias": categorias,
            "url_crear": reverse("categorias:crear"),
            **_contexto_sidebar_cuenta(),
        },
    )


@staff_member_required
def detalle(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    return render(
        request,
        "categorias/crud/detalle.html",
        {
            "titulo": categoria.nombre,
            "categoria": categoria,
            "publicaciones_relacionadas": categoria.publicaciones.count(),
            **_contexto_sidebar_cuenta(),
            "url_lista": _url_lista(),
            "url_editar": reverse("categorias:editar", args=[categoria.pk]),
            "url_eliminar": reverse("categorias:eliminar", args=[categoria.pk]),
        },
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def crear(request):
    categoria = Categoria()
    datos = _datos_categoria(categoria)
    errores = {}
    if request.method == "POST":
        datos, errores = _validar_categoria(request.POST, categoria)
    if request.method == "POST" and not errores:
        categoria.save()
        messages.success(request, "La categoría se creó correctamente.")
        return redirect("categorias:detalle", pk=categoria.pk)
    return render(
        request,
        "categorias/crud/crear.html",
        {
            **_contexto_sidebar_cuenta(),
            "titulo": "Crear categoría",
            "datos": datos,
            "errores": errores,
            "url_cancelar": _url_lista(),
        },
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    datos = _datos_categoria(categoria)
    errores = {}
    if request.method == "POST":
        datos, errores = _validar_categoria(request.POST, categoria)
    if request.method == "POST" and not errores:
        categoria.save()
        messages.success(request, "La categoría se actualizó correctamente.")
        return redirect("categorias:detalle", pk=categoria.pk)
    return render(
        request,
        "categorias/crud/editar.html",
        {
            **_contexto_sidebar_cuenta(),
            "titulo": f"Editar {categoria.nombre}",
            "categoria": categoria,
            "datos": datos,
            "errores": errores,
            "url_cancelar": reverse("categorias:detalle", args=[categoria.pk]),
        },
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def eliminar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        try:
            categoria.delete()
        except ProtectedError:
            messages.error(
                request,
                "No se puede eliminar esta categoría porque tiene publicaciones asociadas. "
                "Puedes desactivarla para impedir que se use en nuevas publicaciones.",
            )
            return redirect("categorias:detalle", pk=categoria.pk)
        messages.success(request, "La categoría se eliminó correctamente.")
        return redirect("categorias:lista")
    publicaciones = categoria.publicaciones.count()
    return render(
        request,
        "categorias/crud/eliminar.html",
        {
            **_contexto_sidebar_cuenta(),
            "titulo": "Eliminar categoría",
            "categoria": categoria,
            "url_cancelar": reverse("categorias:detalle", args=[categoria.pk]),
            "url_editar": reverse("categorias:editar", args=[categoria.pk]),
            "elementos_relacionados": publicaciones,
            "relacion": "publicaciones",
            "bloqueado_por_referencias": publicaciones,
            "mensaje_bloqueo": (
                "No se puede eliminar mientras tenga publicaciones relacionadas. "
                "Puedes desactivar la categoría editándola."
            ),
        },
    )
