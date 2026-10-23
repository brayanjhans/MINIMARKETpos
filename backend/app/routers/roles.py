from fastapi import APIRouter, status

from app.dependencies import DB, ConPermiso
from app.schemas.roles import ModuloPermisos, RolActualizar, RolCrear, RolDetalle, RolListado
from app.services import roles as servicio
from app.utils.respuestas import Mensaje

router = APIRouter(prefix="/roles", tags=["Roles y permisos"])


@router.get("", summary="Listar roles")
async def listar(session: DB, _: ConPermiso("roles.ver")) -> list[RolListado]:
    return await servicio.listar(session)


@router.get("/permisos", summary="Catálogo de permisos agrupados por módulo")
async def catalogo_permisos(_: ConPermiso("roles.ver")) -> list[ModuloPermisos]:
    return servicio.catalogo()


@router.get("/{rol_id}", summary="Detalle de un rol con sus permisos")
async def obtener(rol_id: int, session: DB, _: ConPermiso("roles.ver")) -> RolDetalle:
    return await servicio.obtener(session, rol_id)


@router.post("", summary="Crear rol", status_code=status.HTTP_201_CREATED)
async def crear(datos: RolCrear, session: DB, ctx: ConPermiso("roles.gestionar")) -> RolDetalle:
    return await servicio.crear(session, ctx, datos)


@router.patch("/{rol_id}", summary="Editar rol y sus permisos")
async def actualizar(rol_id: int, datos: RolActualizar, session: DB, ctx: ConPermiso("roles.gestionar")) -> RolDetalle:
    return await servicio.actualizar(session, ctx, rol_id, datos)


@router.delete("/{rol_id}", summary="Eliminar rol (solo si no tiene usuarios)")
async def eliminar(rol_id: int, session: DB, ctx: ConPermiso("roles.gestionar")) -> Mensaje:
    await servicio.eliminar(session, ctx, rol_id)
    return Mensaje(mensaje="Rol eliminado")
