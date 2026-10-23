from typing import Annotated

from fastapi import APIRouter, Depends, Query, UploadFile, status

from app.core.excepciones import ValidacionNegocio
from app.dependencies import DB, ConPermiso
from app.schemas.productos import (
    HistorialPrecioSalida,
    ProductoActualizar,
    ProductoCrear,
    ProductoDetalle,
    ProductoListado,
    ProductoPorCodigo,
    ResumenProductos,
)
from app.services import imagenes
from app.services import productos as servicio
from app.utils.paginacion import Pagina, ParametrosPaginacion, construir_pagina, parametros_paginacion
from app.utils.respuestas import Mensaje

router = APIRouter(prefix="/productos", tags=["Productos"])

Paginacion = Annotated[ParametrosPaginacion, Depends(parametros_paginacion)]


@router.get("", summary="Listar productos (con stock del almacén de venta de la sucursal actual)")
async def listar(
    session: DB,
    ctx: ConPermiso("productos.ver"),
    params: Paginacion,
    busqueda: Annotated[str | None, Query(max_length=100, description="Nombre (palabras) o código exacto")] = None,
    categoria_id: int | None = None,
    marca_id: int | None = None,
    activo: bool | None = True,
    estado: Annotated[str | None, Query(pattern="^(bajo|sin_stock|negativo|sin_codigo)$")] = None,
    orden: Annotated[str | None, Query(description="nombre, precio, stock, creado (- = desc)")] = None,
) -> Pagina[ProductoListado]:
    items, total = await servicio.listar(
        session, ctx, params, busqueda=busqueda, categoria_id=categoria_id, marca_id=marca_id, activo=activo,
        estado=estado, orden=orden,
    )
    return construir_pagina(items, total, params)


@router.get("/resumen", summary="Conteos: activos, stock bajo, sin stock, negativos, sin código")
async def resumen(session: DB, ctx: ConPermiso("productos.ver")) -> ResumenProductos:
    return ResumenProductos(**await servicio.resumen(session, ctx))


@router.get("/codigo/{codigo}", summary="Buscar por código de barras o código interno (escáner)")
async def por_codigo(codigo: str, session: DB, ctx: ConPermiso("productos.ver")) -> ProductoPorCodigo:
    return ProductoPorCodigo(**await servicio.buscar_por_codigo(session, ctx, codigo[:50]))


@router.get("/{producto_id}", summary="Detalle del producto con stock por almacén")
async def obtener(producto_id: int, session: DB, ctx: ConPermiso("productos.ver")) -> ProductoDetalle:
    return await servicio.obtener(session, ctx, producto_id)


@router.get("/{producto_id}/historial-precios", summary="Cambios de precio de venta y de costo")
async def historial_precios(
    producto_id: int, session: DB, _: ConPermiso("productos.editar")
) -> list[HistorialPrecioSalida]:
    return [HistorialPrecioSalida(**h) for h in await servicio.historial_precios(session, producto_id)]


@router.post("", summary="Crear producto", status_code=status.HTTP_201_CREATED)
async def crear(datos: ProductoCrear, session: DB, ctx: ConPermiso("productos.crear")) -> ProductoDetalle:
    return await servicio.crear(session, ctx, datos)


@router.patch("/{producto_id}", summary="Editar producto (envíe la `version` que tenía en pantalla)")
async def actualizar(
    producto_id: int, datos: ProductoActualizar, session: DB, ctx: ConPermiso("productos.editar")
) -> ProductoDetalle:
    return await servicio.actualizar(session, ctx, producto_id, datos)


@router.delete("/{producto_id}", summary="Eliminar producto sin movimientos (si tiene, desactívelo)")
async def eliminar(producto_id: int, session: DB, ctx: ConPermiso("productos.eliminar")) -> Mensaje:
    await servicio.eliminar(session, ctx, producto_id)
    return Mensaje(mensaje="Producto eliminado")


async def _leer_limitado(archivo: UploadFile) -> bytes:
    """Lee el archivo sin cargar en memoria más de lo permitido."""
    partes: list[bytes] = []
    leido = 0
    while bloque := await archivo.read(256 * 1024):
        leido += len(bloque)
        if leido > imagenes.TAMANIO_MAXIMO:
            raise ValidacionNegocio("La foto pesa más de 10 MB", codigo="imagen_muy_pesada")
        partes.append(bloque)
    if not leido:
        raise ValidacionNegocio("El archivo está vacío", codigo="imagen_invalida")
    return b"".join(partes)


@router.put("/{producto_id}/imagen", summary="Subir o reemplazar la foto (se convierte a WEBP liviano)")
async def subir_imagen(
    producto_id: int, archivo: UploadFile, session: DB, ctx: ConPermiso("productos.editar")
) -> ProductoDetalle:
    return await servicio.cambiar_imagen(session, ctx, producto_id, await _leer_limitado(archivo))


@router.delete("/{producto_id}/imagen", summary="Quitar la foto")
async def quitar_imagen(producto_id: int, session: DB, ctx: ConPermiso("productos.editar")) -> ProductoDetalle:
    return await servicio.cambiar_imagen(session, ctx, producto_id, None)
