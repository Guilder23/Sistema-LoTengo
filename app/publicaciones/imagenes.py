from io import BytesIO
import warnings
from uuid import uuid4

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError


TAMANO_MAXIMO_IMAGEN = 5 * 1024 * 1024
MAXIMO_PIXELES = 25_000_000
FORMATOS_PERMITIDOS = {
    "JPEG": "jpg",
    "PNG": "png",
    "WEBP": "webp",
}


class ErrorImagen(ValueError):
    pass


def preparar_imagen(archivo):
    if archivo.size > TAMANO_MAXIMO_IMAGEN:
        raise ErrorImagen("Cada fotografía debe pesar 5 MB o menos.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            imagen = Image.open(archivo)
            formato = imagen.format
            if formato not in FORMATOS_PERMITIDOS:
                raise ErrorImagen("Usa una imagen JPG, PNG o WEBP.")
            if imagen.width * imagen.height > MAXIMO_PIXELES:
                raise ErrorImagen("La resolución de la fotografía es demasiado alta.")
            imagen.verify()

            archivo.seek(0)
            imagen = Image.open(archivo)
            imagen = ImageOps.exif_transpose(imagen)
            if formato == "JPEG" and imagen.mode not in {"L", "RGB"}:
                imagen = imagen.convert("RGB")

            salida = BytesIO()
            imagen.save(salida, format=formato, exif=b"")
    except ErrorImagen:
        raise
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as error:
        raise ErrorImagen("No se pudo validar la fotografía. Elige otra imagen.") from error
    finally:
        archivo.seek(0)

    extension = FORMATOS_PERMITIDOS[formato]
    nombre = f"{uuid4().hex}.{extension}"
    return ContentFile(salida.getvalue(), name=nombre)
