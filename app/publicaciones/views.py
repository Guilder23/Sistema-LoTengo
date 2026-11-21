from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from app.categorias.models import Categoria
from app.geografia.models import Departamento, Municipio
from app.notificaciones.services import notificar_nueva_publicacion
from app.denuncias.models import BloqueoUsuario
from app.ubicaciones.models import Ubicacion

from .imagenes import ErrorImagen, TAMANO_MAXIMO_IMAGEN, preparar_imagen
from .models import ImagenPublicacion, Publicacion


MAXIMO_IMAGENES = 5


def _publicaciones_activas():
    return (
        Publicacion.objects.filter(
            estado=Publicacion.Estado.PUBLICADA,
            oculta_por_moderacion=False,
            usuario__is_active=True,
        )
        .filter(
            Q(usuario__suspendido_hasta__isnull=True)
            | Q(usuario__suspendido_hasta__lte=timezone.now())
        )
        .select_related(
            "categoria",
            "ubicacion",
            "ubicacion__departamento",
            "ubicacion__municipio",
            "usuario",
            "usuario__perfil",
        )
        .prefetch_related("imagenes")
    )


def listado(request):
    publicaciones = _publicaciones_activas()
    filtros = {
        "q": request.GET.get("q", "").strip()[:100],
        "tipo": request.GET.get("tipo", "").strip(),
        "categoria": request.GET.get("categoria", "").strip(),
        "departamento": request.GET.get("departamento", "").strip(),
        "municipio": request.GET.get("municipio", "").strip()[:100],
    }

    if filtros["q"]:
        publicaciones = publicaciones.filter(
            Q(titulo__icontains=filtros["q"])
            | Q(descripcion__icontains=filtros["q"])
            | Q(marca__icontains=filtros["q"])
            | Q(color__icontains=filtros["q"])
            | Q(caracteristicas_publicas__icontains=filtros["q"])
        )
    if filtros["tipo"] in Publicacion.Tipo.values:
        publicaciones = publicaciones.filter(tipo=filtros["tipo"])
    if (
        filtros["categoria"].isascii()
        and filtros["categoria"].isdecimal()
        and len(filtros["categoria"]) <= 20
    ):
        publicaciones = publicaciones.filter(
            categoria_id=filtros["categoria"],
            categoria__activa=True,
        )
    if Departamento.objects.filter(codigo=filtros["departamento"]).exists():
        publicaciones = publicaciones.filter(
            ubicacion__departamento__codigo=filtros["departamento"]
        )
    if filtros["municipio"]:
        publicaciones = publicaciones.filter(
            ubicacion__municipio__nombre__icontains=filtros["municipio"]
        )

    pagina = Paginator(publicaciones, 12).get_page(request.GET.get("pagina"))
    return render(
        request,
        "general/publicaciones.html",
        {
            "pagina": pagina,
            "categorias": Categoria.objects.filter(activa=True),
            "departamentos": Departamento.objects.all(),
            "filtros": filtros,
            "mostrar_propias": False,
        },
    )


def detalle(request, pk):
    publicaciones = Publicacion.objects.select_related(
        "categoria",
        "ubicacion",
        "ubicacion__departamento",
        "ubicacion__municipio",
        "usuario",
        "usuario__perfil",
    ).prefetch_related("imagenes")
    if request.user.is_authenticated:
        publicaciones = publicaciones.filter(
            (
                Q(
                    estado=Publicacion.Estado.PUBLICADA,
                    oculta_por_moderacion=False,
                    usuario__is_active=True,
                )
                & (
                    Q(usuario__suspendido_hasta__isnull=True)
                    | Q(usuario__suspendido_hasta__lte=timezone.now())
                )
            )
            | Q(usuario=request.user)
        )
    else:
        publicaciones = publicaciones.filter(
            estado=Publicacion.Estado.PUBLICADA,
            oculta_por_moderacion=False,
            usuario__is_active=True,
        ).filter(
            Q(usuario__suspendido_hasta__isnull=True)
            | Q(usuario__suspendido_hasta__lte=timezone.now())
        )
    publicacion = get_object_or_404(publicaciones, pk=pk)
    es_propietario = request.user.is_authenticated and publicacion.usuario_id == request.user.pk
    if es_propietario:
        return render(
            request,
            "publicaciones/crud/detalle.html",
            {
                "publicacion": publicacion,
                "es_propietario": True,
                "mostrar_sidebar_cuenta": True,
            },
        )

    publicaciones_relacionadas = (
        _publicaciones_activas()
        .filter(categoria_id=publicacion.categoria_id)
        .exclude(pk=publicacion.pk)
        .order_by("-creada_en")[:4]
    )
    return render(
        request,
        "general/detalle_publicacion.html",
        {
            "publicacion": publicacion,
            "es_propietario": False,
            "mostrar_sidebar_cuenta": False,
            "puede_reportar": (
                request.user.is_authenticated
                and publicacion.usuario_id != request.user.pk
            ),
            "contacto_bloqueado": (
                request.user.is_authenticated
                and BloqueoUsuario.objects.filter(
                    bloqueador=request.user,
                    bloqueado=publicacion.usuario,
                ).exists()
            ),
            "categorias": Categoria.objects.filter(activa=True),
            "departamentos": Departamento.objects.all(),
            "filtros": {
                "q": "",
                "tipo": "",
                "categoria": "",
                "departamento": "",
                "municipio": "",
            },
            "publicaciones_relacionadas": publicaciones_relacionadas,
        },
    )


def _texto(datos, campo, etiqueta, maximo, errores, obligatorio=False):
    valor = datos.get(campo, "").strip()
    if obligatorio and not valor:
        errores.setdefault(campo, []).append(f"El campo {etiqueta} es obligatorio.")
    elif len(valor) > maximo:
        errores.setdefault(campo, []).append(
            f"El campo {etiqueta} no puede superar {maximo} caracteres."
        )
    return valor


def _validar_datos_publicacion(request, publicacion=None):
    datos = request.POST
    errores = {}
    tipo = datos.get("tipo", "").strip()
    if tipo not in Publicacion.Tipo.values:
        errores.setdefault("tipo", []).append("Selecciona si el objeto se perdió o se encontró.")

    categoria_id = datos.get("categoria", "").strip()
    categoria = None
    if categoria_id.isascii() and categoria_id.isdecimal() and len(categoria_id) <= 20:
        categoria = Categoria.objects.filter(pk=categoria_id, activa=True).first()
    if categoria is None:
        errores.setdefault("categoria", []).append("Selecciona una categoría válida.")

    titulo = _texto(datos, "titulo", "título", 140, errores, obligatorio=True)
    descripcion = _texto(
        datos,
        "descripcion",
        "descripción",
        1600,
        errores,
        obligatorio=True,
    )
    marca = _texto(datos, "marca", "marca", 80, errores)
    color = _texto(datos, "color", "color", 60, errores)
    caracteristicas_publicas = _texto(
        datos,
        "caracteristicas_publicas",
        "características públicas",
        500,
        errores,
    )
    caracteristica_privada = _texto(
        datos,
        "caracteristica_privada",
        "dato privado de verificación",
        500,
        errores,
    )

    fecha_evento = None
    fecha_texto = datos.get("fecha_evento", "").strip()
    try:
        fecha_evento = date.fromisoformat(fecha_texto)
    except ValueError:
        errores.setdefault("fecha_evento", []).append("Indica una fecha válida.")
    if fecha_evento and fecha_evento > timezone.localdate():
        errores.setdefault("fecha_evento", []).append(
            "La fecha del objeto no puede estar en el futuro."
        )

    departamento_codigo = datos.get("departamento", "").strip()
    departamento = Departamento.objects.filter(codigo=departamento_codigo).first()
    if departamento is None:
        errores.setdefault("departamento", []).append("Selecciona un departamento válido.")
    municipio_nombre = _texto(
        datos,
        "municipio",
        "municipio",
        100,
        errores,
        obligatorio=True,
    )
    municipio = (
        Municipio.objects.filter(
            departamento=departamento,
            nombre=municipio_nombre,
        ).first()
        if departamento and municipio_nombre
        else None
    )
    if municipio_nombre and departamento and municipio is None:
        errores.setdefault("municipio", []).append(
            "Selecciona un municipio que pertenezca al departamento elegido."
        )
    zona = _texto(datos, "zona", "zona o lugar aproximado", 120, errores)
    conoce_lugar_exacto = datos.get("conoce_lugar_exacto") == "on"
    referencia_privada = _texto(
        datos,
        "referencia_privada",
        "referencia privada",
        240,
        errores,
    )
    if not conoce_lugar_exacto:
        referencia_privada = ""

    imagenes_nuevas = request.FILES.getlist("imagenes")
    ids_eliminar = []
    imagenes_existentes = publicacion.imagenes.all() if publicacion else ImagenPublicacion.objects.none()
    ids_existentes = set(imagenes_existentes.values_list("pk", flat=True))
    for valor in datos.getlist("eliminar_imagenes"):
        if (
            not valor.isascii()
            or not valor.isdecimal()
            or len(valor) > 20
            or int(valor) not in ids_existentes
        ):
            errores.setdefault("imagenes", []).append(
                "No se pudo validar una de las fotografías seleccionadas."
            )
        else:
            ids_eliminar.append(int(valor))

    cantidad_actual = len(ids_existentes.difference(ids_eliminar))
    if cantidad_actual + len(imagenes_nuevas) > MAXIMO_IMAGENES:
        errores.setdefault("imagenes", []).append(
            f"Puedes adjuntar hasta {MAXIMO_IMAGENES} fotografías."
        )

    imagenes_preparadas = []
    if cantidad_actual + len(imagenes_nuevas) <= MAXIMO_IMAGENES:
        for imagen in imagenes_nuevas:
            try:
                imagenes_preparadas.append(preparar_imagen(imagen))
            except ErrorImagen as error:
                errores.setdefault("imagenes", []).append(str(error))

    valores = {
        "tipo": tipo,
        "categoria": categoria,
        "titulo": titulo,
        "descripcion": descripcion,
        "marca": marca,
        "color": color,
        "caracteristicas_publicas": caracteristicas_publicas,
        "caracteristica_privada": caracteristica_privada,
        "fecha_evento": fecha_evento,
        "departamento": departamento,
        "municipio": municipio,
        "zona": zona,
        "conoce_lugar_exacto": conoce_lugar_exacto,
        "referencia_privada": referencia_privada,
    }
    return valores, imagenes_preparadas, ids_eliminar, errores


def _guardar_publicacion(request, valores, imagenes, ids_eliminar, publicacion=None):
    es_nueva = publicacion is None
    with transaction.atomic():
        ubicacion = publicacion.ubicacion if publicacion else Ubicacion()
        ubicacion.departamento = valores["departamento"]
        ubicacion.municipio = valores["municipio"]
        ubicacion.zona = valores["zona"]
        ubicacion.conoce_lugar_exacto = valores["conoce_lugar_exacto"]
        ubicacion.referencia_privada = valores["referencia_privada"]
        ubicacion.full_clean()
        ubicacion.save()

        if publicacion is None:
            publicacion = Publicacion(usuario=request.user, ubicacion=ubicacion)
        publicacion.ubicacion = ubicacion
        publicacion.categoria = valores["categoria"]
        publicacion.tipo = valores["tipo"]
        publicacion.titulo = valores["titulo"]
        publicacion.descripcion = valores["descripcion"]
        publicacion.marca = valores["marca"]
        publicacion.color = valores["color"]
        publicacion.caracteristicas_publicas = valores["caracteristicas_publicas"]
        publicacion.caracteristica_privada = valores["caracteristica_privada"]
        publicacion.fecha_evento = valores["fecha_evento"]
        publicacion.full_clean()
        publicacion.save()

        for imagen in publicacion.imagenes.filter(pk__in=ids_eliminar):
            nombre_archivo = imagen.archivo.name
            almacenamiento = imagen.archivo.storage
            imagen.delete()
            transaction.on_commit(
                lambda almacenamiento=almacenamiento, nombre_archivo=nombre_archivo: (
                    almacenamiento.delete(nombre_archivo)
                )
            )
        for archivo in imagenes:
            ImagenPublicacion.objects.create(publicacion=publicacion, archivo=archivo)
        if es_nueva:
            notificar_nueva_publicacion(publicacion)
    return publicacion


def _contexto_formulario(publicacion=None, valores=None, errores=None):
    valores = valores or {}
    departamento = valores.get("departamento", "")
    codigo_departamento = (
        departamento.codigo
        if isinstance(departamento, Departamento)
        else departamento
    )
    municipios = (
        Municipio.objects.filter(departamento__codigo=codigo_departamento)
        .order_by("nombre")
        .values_list("nombre", flat=True)
        if Departamento.objects.filter(codigo=codigo_departamento).exists()
        else []
    )
    return {
        "publicacion": publicacion,
        "valores": valores,
        "errores": errores or {},
        "mostrar_formulario": valores.get("tipo", "") in Publicacion.Tipo.values,
        "imagenes_a_eliminar": set(
            valores.getlist("eliminar_imagenes")
            if hasattr(valores, "getlist")
            else []
        ),
        "categorias": Categoria.objects.filter(activa=True),
        "departamentos": Departamento.objects.all(),
        "municipios": municipios,
        "maximo_imagenes": MAXIMO_IMAGENES,
        "tamano_maximo_imagen": TAMANO_MAXIMO_IMAGEN,
        "tamano_maximo_imagen_mb": TAMANO_MAXIMO_IMAGEN // (1024 * 1024),
        "today": timezone.localdate(),
        "mostrar_sidebar_cuenta": True,
    }


def _verificar_cuenta(request):
    if not request.user.correo_verificado:
        messages.warning(
            request,
            "Verifica tu correo electrónico antes de publicar.",
        )
        return redirect("cuentas:reenviar_verificacion")
    return None


@login_required
@require_http_methods(["GET", "POST"])
def crear(request):
    redireccion = _verificar_cuenta(request)
    if redireccion:
        return redireccion

    if request.method == "POST":
        valores, imagenes, ids_eliminar, errores = _validar_datos_publicacion(request)
        if not errores:
            publicacion = _guardar_publicacion(
                request,
                valores,
                imagenes,
                ids_eliminar,
            )
            messages.success(request, "Tu publicación ya está disponible.")
            return redirect("publicaciones:detalle", pk=publicacion.pk)
        return render(
            request,
            "publicaciones/crud/crear.html",
            _contexto_formulario(valores=request.POST, errores=errores),
        )

    tipo = request.GET.get("tipo", "")
    if tipo not in Publicacion.Tipo.values:
        tipo = ""
    valores = {
        "tipo": tipo,
        "fecha_evento": timezone.localdate().isoformat(),
    }
    return render(
        request,
        "publicaciones/crud/crear.html",
        _contexto_formulario(valores=valores),
    )


@login_required
@require_http_methods(["GET", "POST"])
def editar(request, pk):
    redireccion = _verificar_cuenta(request)
    if redireccion:
        return redireccion
    publicacion = get_object_or_404(
        Publicacion.objects.select_related(
            "usuario",
            "usuario__perfil",
            "ubicacion",
            "ubicacion__departamento",
            "ubicacion__municipio",
            "categoria",
        ).prefetch_related("imagenes"),
        pk=pk,
        usuario=request.user,
    )
    if publicacion.estado in {
        Publicacion.Estado.RESUELTA,
        Publicacion.Estado.ELIMINADA,
    }:
        messages.info(request, "Esta publicación ya no se puede editar.")
        return redirect("publicaciones:detalle", pk=publicacion.pk)

    if request.method == "POST":
        valores, imagenes, ids_eliminar, errores = _validar_datos_publicacion(
            request,
            publicacion,
        )
        if not errores:
            publicacion = _guardar_publicacion(
                request,
                valores,
                imagenes,
                ids_eliminar,
                publicacion,
            )
            messages.success(request, "Los cambios se guardaron correctamente.")
            return redirect("publicaciones:detalle", pk=publicacion.pk)
        return render(
            request,
            "publicaciones/crud/editar.html",
            _contexto_formulario(publicacion, request.POST, errores),
        )

    valores = {
        "tipo": publicacion.tipo,
        "categoria": str(publicacion.categoria_id),
        "titulo": publicacion.titulo,
        "descripcion": publicacion.descripcion,
        "marca": publicacion.marca,
        "color": publicacion.color,
        "caracteristicas_publicas": publicacion.caracteristicas_publicas,
        "caracteristica_privada": publicacion.caracteristica_privada,
        "fecha_evento": publicacion.fecha_evento.isoformat(),
        "departamento": publicacion.ubicacion.departamento.codigo,
        "municipio": publicacion.ubicacion.municipio.nombre,
        "zona": publicacion.ubicacion.zona,
        "conoce_lugar_exacto": publicacion.ubicacion.conoce_lugar_exacto,
        "referencia_privada": publicacion.ubicacion.referencia_privada,
    }
    return render(
        request,
        "publicaciones/crud/editar.html",
        _contexto_formulario(publicacion, valores),
    )


@require_GET
def municipios_por_departamento(request):
    departamento = request.GET.get("departamento", "").strip()
    if not Departamento.objects.filter(codigo=departamento).exists():
        return JsonResponse({"municipios": []})
    municipios = list(
        Municipio.objects.filter(departamento__codigo=departamento)
        .order_by("nombre")
        .values_list("nombre", flat=True)
    )
    return JsonResponse({"municipios": municipios})


@login_required
def mis_publicaciones(request):
    publicaciones = (
        Publicacion.objects.filter(usuario=request.user)
        .exclude(estado=Publicacion.Estado.ELIMINADA)
        .select_related(
            "categoria",
            "ubicacion",
            "ubicacion__departamento",
            "ubicacion__municipio",
        )
        .prefetch_related("imagenes")
    )
    pagina = Paginator(publicaciones, 20).get_page(request.GET.get("pagina"))
    return render(
        request,
        "publicaciones/publicaciones.html",
        {
            "pagina": pagina,
            "mostrar_propias": True,
            "categorias": Categoria.objects.filter(activa=True),
            "departamentos": Departamento.objects.all(),
            "filtros": {},
            "mostrar_sidebar_cuenta": True,
        },
    )


@login_required
@require_POST
def cambiar_estado(request, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk, usuario=request.user)
    accion = request.POST.get("accion", "")
    transiciones = {
        "pausar": (Publicacion.Estado.PUBLICADA, Publicacion.Estado.PAUSADA),
        "activar": (Publicacion.Estado.PAUSADA, Publicacion.Estado.PUBLICADA),
        "resolver": (Publicacion.Estado.PUBLICADA, Publicacion.Estado.RESUELTA),
    }
    transicion = transiciones.get(accion)
    if transicion is None or publicacion.estado != transicion[0]:
        messages.error(request, "No se pudo cambiar el estado de la publicación.")
        return redirect("publicaciones:mis_publicaciones")

    publicacion.estado = transicion[1]
    publicacion.save(update_fields=["estado", "actualizada_en"])
    messages.success(request, f"Estado actualizado: {publicacion.get_estado_display().lower()}.")
    return redirect("publicaciones:mis_publicaciones")


@login_required
@require_http_methods(["GET", "POST"])
def eliminar(request, pk):
    publicacion = get_object_or_404(
        Publicacion.objects.select_related("categoria"),
        pk=pk,
        usuario=request.user,
    )
    if publicacion.estado == Publicacion.Estado.ELIMINADA:
        messages.info(request, "Esta publicación ya fue eliminada.")
        return redirect("publicaciones:mis_publicaciones")

    if request.method == "POST":
        publicacion.estado = Publicacion.Estado.ELIMINADA
        publicacion.eliminada_en = timezone.now()
        publicacion.save(update_fields=["estado", "eliminada_en", "actualizada_en"])
        messages.success(
            request,
            "La publicación se retiró del sitio. El registro se conserva por seguridad.",
        )
        return redirect("publicaciones:mis_publicaciones")

    return render(
        request,
        "publicaciones/crud/eliminar.html",
        {
            "publicacion": publicacion,
            "mostrar_sidebar_cuenta": True,
        },
    )
