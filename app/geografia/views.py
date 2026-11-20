from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods

from .models import Departamento, Municipio


def _contexto_sidebar_cuenta():
    return {"mostrar_sidebar_cuenta": True}


def _agregar_errores_modelo(errores, excepcion):
    for campo, mensajes in excepcion.message_dict.items():
        clave = "non_field_errors" if campo == "__all__" else campo
        errores.setdefault(clave, []).extend(mensajes)


def _validar_departamento(post, departamento):
    datos = {"nombre": post.get("nombre", "").strip()}
    errores = {}
    departamento.nombre = datos["nombre"]

    if not departamento.pk:
        departamento.codigo = slugify(datos["nombre"]).replace("-", "_")[:30]
        if not departamento.codigo:
            errores["nombre"] = [
                "El nombre debe contener letras o números para generar un código."
            ]
        elif Departamento.objects.filter(codigo=departamento.codigo).exists():
            errores.setdefault("nombre", []).append(
                "Ya existe un departamento con un código derivado de ese nombre."
            )

    try:
        departamento.full_clean(exclude=["codigo"])
    except ValidationError as excepcion:
        _agregar_errores_modelo(errores, excepcion)

    return datos, errores


def _datos_municipio(municipio):
    return {
        "departamento": str(municipio.departamento_id or ""),
        "nombre": municipio.nombre or "",
    }


def _validar_municipio(post, municipio):
    datos = {
        "departamento": post.get("departamento", "").strip(),
        "nombre": post.get("nombre", "").strip(),
    }
    errores = {}
    try:
        departamento_id = int(datos["departamento"])
    except ValueError:
        departamento = None
    else:
        departamento = Departamento.objects.filter(pk=departamento_id).first()

    if departamento is None:
        errores["departamento"] = ["Selecciona un departamento válido."]
    else:
        municipio.departamento = departamento
    municipio.nombre = datos["nombre"]

    exclude = [] if departamento else ["departamento"]
    try:
        municipio.full_clean(exclude=exclude)
    except ValidationError as excepcion:
        _agregar_errores_modelo(errores, excepcion)

    return datos, errores


@staff_member_required
def departamentos(request):
    return render(
        request,
        "geografia/departamentos/departamentos.html",
        {
            **_contexto_sidebar_cuenta(),
            "titulo": "Gestión de departamentos",
            "descripcion": "Administra los departamentos disponibles al publicar objetos.",
            "departamentos": Departamento.objects.annotate(
                municipios_count=Count("municipios", distinct=True),
                ubicaciones_count=Count("ubicaciones", distinct=True),
            ),
            "url_crear": reverse("geografia:departamento_crear"),
        },
    )


@staff_member_required
def departamento_detalle(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    return render(
        request,
        "geografia/departamentos/crud/detalle.html",
        {
            **_contexto_sidebar_cuenta(),
            "titulo": departamento.nombre,
            "departamento": departamento,
            "url_lista": reverse("geografia:departamentos"),
            "url_editar": reverse("geografia:departamento_editar", args=[pk]),
            "url_eliminar": reverse("geografia:departamento_eliminar", args=[pk]),
        },
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def departamento_crear(request):
    departamento = Departamento()
    datos = {"nombre": ""}
    errores = {}
    if request.method == "POST":
        datos, errores = _validar_departamento(request.POST, departamento)
    if request.method == "POST" and not errores:
        departamento.save()
        messages.success(request, "El departamento se creó correctamente.")
        return redirect("geografia:departamento_detalle", pk=departamento.pk)
    return render(
        request,
        "geografia/departamentos/crud/crear.html",
        {
            **_contexto_sidebar_cuenta(),
            "titulo": "Crear departamento",
            "datos": datos,
            "errores": errores,
            "url_cancelar": reverse("geografia:departamentos"),
        },
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def departamento_editar(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    datos = {"nombre": departamento.nombre}
    errores = {}
    if request.method == "POST":
        datos, errores = _validar_departamento(request.POST, departamento)
    if request.method == "POST" and not errores:
        departamento.save()
        messages.success(request, "El departamento se actualizó correctamente.")
        return redirect("geografia:departamento_detalle", pk=departamento.pk)
    return render(
        request,
        "geografia/departamentos/crud/editar.html",
        {
            **_contexto_sidebar_cuenta(),
            "titulo": f"Editar {departamento.nombre}",
            "departamento": departamento,
            "datos": datos,
            "errores": errores,
            "url_cancelar": reverse(
                "geografia:departamento_detalle",
                args=[departamento.pk],
            ),
        },
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def departamento_eliminar(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    ubicaciones = departamento.ubicaciones.count()
    if request.method == "POST":
        if ubicaciones:
            messages.error(
                request,
                "No se puede eliminar el departamento porque existen ubicaciones "
                "guardadas que lo utilizan.",
            )
            return redirect("geografia:departamento_detalle", pk=pk)
        try:
            departamento.delete()
        except ProtectedError:
            messages.error(
                request,
                "No se puede eliminar el departamento porque existen ubicaciones "
                "guardadas que lo utilizan.",
            )
            return redirect("geografia:departamento_detalle", pk=pk)
        messages.success(
            request,
            "El departamento y sus municipios se eliminaron correctamente.",
        )
        return redirect("geografia:departamentos")
    return render(
        request,
        "geografia/departamentos/crud/eliminar.html",
        {
            **_contexto_sidebar_cuenta(),
            "titulo": "Eliminar departamento",
            "departamento": departamento,
            "url_cancelar": reverse("geografia:departamento_detalle", args=[pk]),
            "url_editar": reverse("geografia:departamento_editar", args=[pk]),
            "elementos_relacionados": departamento.municipios.count(),
            "relacion": "municipios, que también se eliminarán",
            "bloqueado_por_referencias": ubicaciones,
            "mensaje_bloqueo": (
                "No se puede eliminar mientras existan ubicaciones guardadas "
                "que utilicen este departamento."
            ),
        },
    )


@staff_member_required
def municipios(request):
    return render(
        request,
        "geografia/municipios/municipios.html",
        {
            **_contexto_sidebar_cuenta(),
            "titulo": "Gestión de municipios",
            "descripcion": "Administra los municipios asociados a cada departamento.",
            "municipios": Municipio.objects.select_related("departamento").annotate(
                ubicaciones_count=Count("ubicaciones", distinct=True)
            ),
            "url_crear": reverse("geografia:municipio_crear"),
        },
    )


@staff_member_required
def municipio_detalle(request, pk):
    municipio = get_object_or_404(
        Municipio.objects.select_related("departamento"),
        pk=pk,
    )
    return render(
        request,
        "geografia/municipios/crud/detalle.html",
        {
            **_contexto_sidebar_cuenta(),
            "titulo": municipio.nombre,
            "municipio": municipio,
            "url_lista": reverse("geografia:municipios"),
            "url_editar": reverse("geografia:municipio_editar", args=[pk]),
            "url_eliminar": reverse("geografia:municipio_eliminar", args=[pk]),
        },
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def municipio_crear(request):
    municipio = Municipio()
    datos = _datos_municipio(municipio)
    errores = {}
    if request.method == "POST":
        datos, errores = _validar_municipio(request.POST, municipio)
    if request.method == "POST" and not errores:
        municipio.save()
        messages.success(request, "El municipio se creó correctamente.")
        return redirect("geografia:municipio_detalle", pk=municipio.pk)
    return render(
        request,
        "geografia/municipios/crud/crear.html",
        {
            **_contexto_sidebar_cuenta(),
            "titulo": "Crear municipio",
            "datos": datos,
            "errores": errores,
            "departamentos": Departamento.objects.all(),
            "url_cancelar": reverse("geografia:municipios"),
        },
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def municipio_editar(request, pk):
    municipio = get_object_or_404(Municipio, pk=pk)
    datos = _datos_municipio(municipio)
    errores = {}
    if request.method == "POST":
        datos, errores = _validar_municipio(request.POST, municipio)
    if request.method == "POST" and not errores:
        municipio.save()
        messages.success(request, "El municipio se actualizó correctamente.")
        return redirect("geografia:municipio_detalle", pk=municipio.pk)
    return render(
        request,
        "geografia/municipios/crud/editar.html",
        {
            **_contexto_sidebar_cuenta(),
            "titulo": f"Editar {municipio.nombre}",
            "municipio": municipio,
            "datos": datos,
            "errores": errores,
            "departamentos": Departamento.objects.all(),
            "url_cancelar": reverse("geografia:municipio_detalle", args=[pk]),
        },
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def municipio_eliminar(request, pk):
    municipio = get_object_or_404(
        Municipio.objects.select_related("departamento"),
        pk=pk,
    )
    ubicaciones = municipio.ubicaciones.count()
    if request.method == "POST":
        if ubicaciones:
            messages.error(
                request,
                "No se puede eliminar el municipio porque existen ubicaciones "
                "guardadas que lo utilizan.",
            )
            return redirect("geografia:municipio_detalle", pk=pk)
        try:
            municipio.delete()
        except ProtectedError:
            messages.error(
                request,
                "No se puede eliminar el municipio porque existen ubicaciones "
                "guardadas que lo utilizan.",
            )
            return redirect("geografia:municipio_detalle", pk=pk)
        messages.success(request, "El municipio se eliminó correctamente.")
        return redirect("geografia:municipios")
    return render(
        request,
        "geografia/municipios/crud/eliminar.html",
        {
            **_contexto_sidebar_cuenta(),
            "titulo": "Eliminar municipio",
            "municipio": municipio,
            "url_cancelar": reverse("geografia:municipio_detalle", args=[pk]),
            "url_editar": reverse("geografia:municipio_editar", args=[pk]),
            "elementos_relacionados": ubicaciones,
            "relacion": "ubicaciones guardadas",
            "bloqueado_por_referencias": ubicaciones,
            "mensaje_bloqueo": (
                "No se puede eliminar mientras existan ubicaciones guardadas "
                "que utilicen este municipio."
            ),
        },
    )
