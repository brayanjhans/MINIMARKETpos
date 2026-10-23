from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.core.excepciones import NoEncontrado
from app.services import imagenes

router = APIRouter(prefix="/media", tags=["Archivos"])


@router.get("/productos/{nombre}", summary="Foto de producto (WEBP, caché de un año)", include_in_schema=False)
async def foto_producto(nombre: str) -> FileResponse:
    # Pública para que la use <img>, pero con nombre aleatorio de 32 caracteres (no se puede adivinar).
    # Cada foto nueva tiene otro nombre, así que el archivo nunca cambia: caché "immutable".
    ruta = imagenes.ruta_archivo(nombre)
    if ruta is None:
        raise NoEncontrado("La imagen no existe")
    return FileResponse(
        ruta, media_type="image/webp", headers={"Cache-Control": "public, max-age=31536000, immutable"}
    )
