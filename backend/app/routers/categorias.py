from fastapi import APIRouter, status

from app.dependencies import DB, ConPermiso
from app.models import Categoria, Marca
from app.schemas.productos import (
    CategoriaActualizar,
    CategoriaCrear,
    CategoriaSalida,
    MarcaActualizar,
    MarcaCrear,
    MarcaSalida,
)
from app.services import categorias as servicio
from app.utils.respuestas import Mensaje

router = APIRouter(tags=["Categorías y marcas"])


async def _categoria(session, id_: int) -> CategoriaSalida:
    return next(c for c in await servicio.listar_categorias(session) if c.id == id_)


async def _marca(session, id_: int) -> MarcaSalida:
    return next(m for m in await servicio.listar_marcas(session) if m.id == id_)


@router.get("/categorias", summary="Categorías con número de productos y valor de inventario")
async def listar_categorias(session: DB, _: ConPermiso("categorias.ver"), activo: bool | None = None) -> list[
    CategoriaSalida
]:
    return await servicio.listar_categorias(session, activo=activo)


@router.post("/categorias", summary="Crear categoría", status_code=status.HTTP_201_CREATED)
async def crear_categoria(datos: CategoriaCrear, session: DB, ctx: ConPermiso("categorias.crear")) -> CategoriaSalida:
    return await _categoria(session, await servicio.crear(session, ctx, Categoria, datos))


@router.patch("/categorias/{categoria_id}", summary="Editar o activar/desactivar categoría")
async def actualizar_categoria(
    categoria_id: int, datos: CategoriaActualizar, session: DB, ctx: ConPermiso("categorias.editar")
) -> CategoriaSalida:
    return await _categoria(session, await servicio.actualizar(session, ctx, Categoria, categoria_id, datos))


@router.delete("/categorias/{categoria_id}", summary="Eliminar categoría sin productos")
async def eliminar_categoria(categoria_id: int, session: DB, ctx: ConPermiso("categorias.eliminar")) -> Mensaje:
    await servicio.eliminar(session, ctx, Categoria, categoria_id)
    return Mensaje(mensaje="Categoría eliminada")


@router.get("/marcas", summary="Marcas con número de productos")
async def listar_marcas(session: DB, _: ConPermiso("marcas.ver"), activo: bool | None = None) -> list[MarcaSalida]:
    return await servicio.listar_marcas(session, activo=activo)


@router.post("/marcas", summary="Crear marca", status_code=status.HTTP_201_CREATED)
async def crear_marca(datos: MarcaCrear, session: DB, ctx: ConPermiso("marcas.crear")) -> MarcaSalida:
    return await _marca(session, await servicio.crear(session, ctx, Marca, datos))


@router.patch("/marcas/{marca_id}", summary="Editar o activar/desactivar marca")
async def actualizar_marca(
    marca_id: int, datos: MarcaActualizar, session: DB, ctx: ConPermiso("marcas.editar")
) -> MarcaSalida:
    return await _marca(session, await servicio.actualizar(session, ctx, Marca, marca_id, datos))


@router.delete("/marcas/{marca_id}", summary="Eliminar marca sin productos")
async def eliminar_marca(marca_id: int, session: DB, ctx: ConPermiso("marcas.eliminar")) -> Mensaje:
    await servicio.eliminar(session, ctx, Marca, marca_id)
    return Mensaje(mensaje="Marca eliminada")
