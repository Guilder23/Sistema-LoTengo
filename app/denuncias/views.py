from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from app.conversaciones.models import Conversacion
from app.conversaciones.models import Mensaje
from app.cuentas.models import Usuario
from app.publicaciones.imagenes import ErrorImagen, preparar_imagen
from app.publicaciones.models import Publicacion

from .models import BloqueoUsuario, ConversacionSilenciada, Denuncia


def _objetivo_denuncia(request):
    publicacion = None
    mensaje = None
    denunciado = None
    publicacion_id = request.GET.get("publicacion") or request.POST.get("publicacion")
    mensaje_id = request.GET.get("mensaje") or request.POST.get("mensaje")
    usuario_id = request.GET.get("usuario") or request.POST.get("usuario")

    if publicacion_id:
        publicacion = get_object_or_404(Publicacion, pk=publicacion_id)
        denunciado = publicacion.usuario
    if mensaje_id:
        mensaje = get_object_or_404(
            Mensaje.objects.select_related(
                "remitente",
                "conversacion__publicacion",
            ),
            pk=mensaje_id,
        )
        if request.user.pk not in {
            mensaje.conversacion.interesado_id,
            mensaje.conversacion.publicacion.usuario_id,
        }:
            raise Http404
        denunciado = mensaje.remitente
        publicacion = mensaje.conversacion.publicacion
    if usuario_id:
        denunciado = get_object_or_404(Usuario, pk=usuario_id, is_active=True)
        if mensaje and denunciado.pk != mensaje.remitente_id:
            raise Http404
        if not mensaje and publicacion and denunciado.pk != publicacion.usuario_id:
            raise Http404
    if denunciado and denunciado.pk == request.user.pk:
        raise Http404
    if not any((publicacion, mensaje, denunciado)):
        raise Http404
    return publicacion, mensaje, denunciado


@login_required
def crear(request):
    publicacion, mensaje, denunciado = _objetivo_denuncia(request)
    errores = {}
    motivo = ""
    descripcion = ""
    evidencia = None
    if request.method == "POST":
        motivo = request.POST.get("motivo", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        archivos = request.FILES.getlist("evidencia")
        if motivo not in Denuncia.Motivo.values:
            errores["motivo"] = "Selecciona un motivo válido."
        if len(descripcion) < 10:
            errores["descripcion"] = "Describe el motivo con al menos 10 caracteres."
        elif len(descripcion) > 2000:
            errores["descripcion"] = "La descripción no puede superar 2000 caracteres."
        if len(archivos) > 1:
            errores["evidencia"] = "Adjunta una sola imagen como evidencia."
        elif archivos:
            try:
                evidencia = preparar_imagen(archivos[0])
            except ErrorImagen as error:
                errores["evidencia"] = str(error)

        if not errores:
            denuncia = Denuncia.objects.create(
                denunciante=request.user,
                denunciado=denunciado,
                publicacion=publicacion,
                mensaje=mensaje,
                motivo=motivo,
                descripcion=descripcion,
                evidencia=evidencia,
            )
            messages.success(
                request,
                f"Tu denuncia #{denuncia.pk} fue enviada. Puedes consultar su estado desde esta página.",
            )
            return redirect("denuncias:mis_denuncias")
    return render(
        request,
        "denuncias/crear.html",
        {
            "motivos": Denuncia.Motivo.choices,
            "errores": errores,
            "valor_motivo": motivo,
            "valor_descripcion": descripcion,
            "publicacion": publicacion,
            "mensaje": mensaje,
            "denunciado": denunciado,
            "mostrar_sidebar_cuenta": True,
        },
    )


@login_required
def mis_denuncias(request):
    base_denuncias = Denuncia.objects.filter(
        denunciante=request.user
    ).select_related(
        "denunciado",
        "publicacion",
        "mensaje",
    )
    conteos = dict(
        base_denuncias.values("estado")
        .annotate(cantidad=Count("pk"))
        .values_list("estado", "cantidad")
    )
    estados = [
        {
            "valor": "",
            "etiqueta": "Todas",
            "cantidad": sum(conteos.values()),
        }
    ]
    estados.extend(
        {
            "valor": valor,
            "etiqueta": etiqueta,
            "cantidad": conteos.get(valor, 0),
        }
        for valor, etiqueta in Denuncia.Estado.choices
    )
    estado = request.GET.get("estado", "")
    denuncias = (
        base_denuncias.filter(estado=estado)
        if estado in Denuncia.Estado.values
        else base_denuncias
    )
    pagina = Paginator(denuncias, 20).get_page(request.GET.get("pagina"))
    return render(
        request,
        "denuncias/mis_denuncias.html",
        {
            "pagina": pagina,
            "estados": estados,
            "estado_seleccionado": estado,
            "mostrar_sidebar_cuenta": True,
        },
    )


@login_required
def descargar_evidencia(request, denuncia_id):
    denuncia = get_object_or_404(Denuncia, pk=denuncia_id)
    if denuncia.denunciante_id != request.user.pk and not request.user.is_staff:
        raise Http404
    if not denuncia.evidencia:
        raise Http404
    respuesta = FileResponse(
        denuncia.evidencia.open("rb"),
        as_attachment=True,
        filename=f"evidencia-denuncia-{denuncia.pk}",
    )
    respuesta["Cache-Control"] = "private, no-store"
    respuesta["X-Content-Type-Options"] = "nosniff"
    return respuesta


@login_required
@require_POST
def bloquear_usuario(request, usuario_id):
    bloqueado = get_object_or_404(Usuario, pk=usuario_id, is_active=True)
    if bloqueado.pk == request.user.pk:
        raise Http404
    bloqueo, creado = BloqueoUsuario.objects.get_or_create(
        bloqueador=request.user,
        bloqueado=bloqueado,
    )
    if not creado:
        bloqueo.delete()
        messages.success(request, "Se quitó el bloqueo de esta persona.")
    else:
        messages.success(
            request,
            "La persona quedó bloqueada. Ya no podrán enviarse mensajes entre ustedes.",
        )
    destino = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        destino = reverse("general:inicio")
    return redirect(destino)


@login_required
@require_POST
def silenciar_conversacion(request, conversacion_id):
    conversacion = get_object_or_404(
        Conversacion.objects.select_related("publicacion"),
        pk=conversacion_id,
    )
    if request.user.pk not in {
        conversacion.interesado_id,
        conversacion.publicacion.usuario_id,
    }:
        raise Http404
    silencio, creado = ConversacionSilenciada.objects.get_or_create(
        usuario=request.user,
        conversacion=conversacion,
    )
    if not creado:
        silencio.delete()
        messages.success(request, "Se reactivaron las notificaciones del chat.")
    else:
        messages.success(request, "Se silenciaron las notificaciones de este chat.")
    return redirect("conversaciones:detalle", pk=conversacion.pk)
