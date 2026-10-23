"""Fotos de productos: SIEMPRE se guardan como WEBP liviano, sin importar cómo se suban.

- Acepta JPG, PNG, WEBP y HEIC (iPhone) de hasta 10 MB; se valida el contenido real, no la extensión.
- Corrige la orientación de la cámara (EXIF) y luego descarta todos los metadatos (incluida la ubicación GPS).
- Guarda dos tamaños: 800 px (~30-60 KB) para la ficha y 160 px (~5-10 KB) para listas y POS.
- Nombres aleatorios (no se pueden adivinar ni pisar) y archivos inmutables: se sirven con caché larga.
"""

import asyncio
import io
import os
import re
import uuid
from pathlib import Path

import pillow_heif
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings
from app.core.excepciones import ValidacionNegocio

pillow_heif.register_heif_opener()

# Más de 25 megapíxeles avisa y más de 50 se rechaza (protege de "bombas de descompresión")
Image.MAX_IMAGE_PIXELS = 25_000_000
TAMANIO_MAXIMO = 10 * 1024 * 1024
FORMATOS_ACEPTADOS = {"JPEG", "PNG", "WEBP", "HEIF", "MPO"}
LADO_GRANDE, CALIDAD_GRANDE = 800, 75
LADO_MINIATURA, CALIDAD_MINIATURA = 160, 70
NOMBRE_VALIDO = re.compile(r"^[0-9a-f]{32}(_m)?$")


def carpeta() -> Path:
    ruta = Path(settings.MEDIA_DIR) / "productos"
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def _a_webp(imagen: Image.Image, lado: int, calidad: int) -> bytes:
    copia = imagen.copy()
    copia.thumbnail((lado, lado), Image.Resampling.LANCZOS)
    salida = io.BytesIO()
    # Sin exif= ni icc_profile=: el archivo resultante no lleva metadatos
    copia.save(salida, "WEBP", quality=calidad, method=6)
    return salida.getvalue()


def procesar(datos: bytes) -> tuple[bytes, bytes]:
    """Convierte la foto subida en (grande, miniatura) WEBP. Trabajo de CPU: llamar en un hilo aparte."""
    error = ValidacionNegocio(
        "El archivo no es una imagen válida. Use una foto JPG, PNG, WEBP o HEIC.", codigo="imagen_invalida"
    )
    try:
        imagen = Image.open(io.BytesIO(datos))
        formato = imagen.format
        if formato not in FORMATOS_ACEPTADOS:
            raise error
        imagen.load()
    except Image.DecompressionBombError as exc:
        raise ValidacionNegocio(
            "La imagen tiene demasiados píxeles. Use una foto de menor resolución.", codigo="imagen_muy_grande"
        ) from exc
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        raise error from exc

    imagen = ImageOps.exif_transpose(imagen)
    tiene_transparencia = imagen.mode in ("RGBA", "LA") or (imagen.mode == "P" and "transparency" in imagen.info)
    imagen = imagen.convert("RGBA" if tiene_transparencia else "RGB")
    return _a_webp(imagen, LADO_GRANDE, CALIDAD_GRANDE), _a_webp(imagen, LADO_MINIATURA, CALIDAD_MINIATURA)


def _escribir(ruta: Path, datos: bytes) -> None:
    # Se escribe a un temporal y se renombra: nunca queda un archivo a medio escribir
    temporal = ruta.with_suffix(".tmp")
    temporal.write_bytes(datos)
    os.replace(temporal, ruta)


async def guardar(datos: bytes) -> str:
    """Procesa y guarda la foto. Devuelve su nombre (sin extensión) para guardarlo en el producto."""
    if len(datos) > TAMANIO_MAXIMO:
        raise ValidacionNegocio("La foto pesa más de 10 MB", codigo="imagen_muy_pesada")
    grande, miniatura = await asyncio.to_thread(procesar, datos)
    nombre = uuid.uuid4().hex
    destino = carpeta()
    await asyncio.to_thread(_escribir, destino / f"{nombre}.webp", grande)
    await asyncio.to_thread(_escribir, destino / f"{nombre}_m.webp", miniatura)
    return nombre


def borrar(nombre: str | None) -> None:
    """Borra los archivos de una foto (se llama DESPUÉS del commit, para no perder la foto si algo falla)."""
    if not nombre or not NOMBRE_VALIDO.match(nombre):
        return
    for sufijo in ("", "_m"):
        (carpeta() / f"{nombre}{sufijo}.webp").unlink(missing_ok=True)


def ruta_archivo(nombre_archivo: str) -> Path | None:
    """Ruta segura de un archivo pedido por URL (evita salir de la carpeta con ../)."""
    base = nombre_archivo.removesuffix(".webp")
    if not nombre_archivo.endswith(".webp") or not NOMBRE_VALIDO.match(base):
        return None
    ruta = carpeta() / nombre_archivo
    return ruta if ruta.is_file() else None


def urls(nombre: str | None) -> tuple[str | None, str | None]:
    if not nombre:
        return None, None
    base = f"{settings.API_PREFIX}/media/productos/{nombre}"
    return f"{base}.webp", f"{base}_m.webp"
