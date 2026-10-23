from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import DB, ConPermiso
from app.schemas.usuarios import (
    RestablecerPassword,
    ResumenUsuarios,
    UsuarioActualizar,
    UsuarioCrear,
    UsuarioDetalle,
    UsuarioListado,
)
from app.services import usuarios as servicio
from app.utils.paginacion import Pagina, ParametrosPaginacion, construir_pagina, parametros_paginacion
from app.utils.respuestas import Mensaje
from app.utils.zona_horaria import inicio_de_hoy_utc

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

Paginacion = Annotated[ParametrosPaginacion, Depends(parametros_paginacion)]


@router.get("", summary="Listar usuarios")
async def listar(
    session: DB,
    _: ConPermiso("usuarios.ver"),
    params: Paginacion,
    busqueda: Annotated[str | None, Query(max_length=100, description="Nombre, usuario o correo")] = None,
    rol_id: int | None = None,
    activo: bool | None = None,
    sucursal_id: int | None = None,
    orden: Annotated[str | None, Query(description="nombre, username, ultimo_acceso, creado (- = desc)")] = None,
) -> Pagina[UsuarioListado]:
    items, total = await servicio.listar(
        session, params, busqueda=busqueda, rol_id=rol_id, activo=activo, sucursal_id=sucursal_id, orden=orden
    )
    return construir_pagina([UsuarioListado.model_validate(u) for u in items], total, params)


@router.get("/resumen", summary="Conteos: con acceso, sin acceso, bloqueados e ingresaron hoy")
async def resumen(session: DB, _: ConPermiso("usuarios.ver")) -> ResumenUsuarios:
    datos = await servicio.resumen(session, inicio_de_hoy_utc())
    return ResumenUsuarios(**datos)


@router.get("/{usuario_id}", summary="Detalle de un usuario")
async def obtener(usuario_id: int, session: DB, _: ConPermiso("usuarios.ver")) -> UsuarioDetalle:
    return UsuarioDetalle.model_validate(await servicio.obtener(session, usuario_id))


@router.post("", summary="Crear usuario", status_code=status.HTTP_201_CREATED)
async def crear(datos: UsuarioCrear, session: DB, ctx: ConPermiso("usuarios.crear")) -> UsuarioDetalle:
    return UsuarioDetalle.model_validate(await servicio.crear(session, ctx, datos))


@router.patch("/{usuario_id}", summary="Editar usuario (incluye activar/desactivar)")
async def actualizar(
    usuario_id: int, datos: UsuarioActualizar, session: DB, ctx: ConPermiso("usuarios.editar")
) -> UsuarioDetalle:
    return UsuarioDetalle.model_validate(await servicio.actualizar(session, ctx, usuario_id, datos))


@router.post("/{usuario_id}/restablecer-password", summary="Asignar una nueva contraseña")
async def restablecer_password(
    usuario_id: int, datos: RestablecerPassword, session: DB, ctx: ConPermiso("usuarios.editar")
) -> Mensaje:
    await servicio.restablecer_password(session, ctx, usuario_id, datos)
    return Mensaje(mensaje="Contraseña restablecida. Se cerraron las sesiones abiertas del usuario.")


@router.post("/{usuario_id}/desbloquear", summary="Desbloquear usuario bloqueado por intentos fallidos")
async def desbloquear(usuario_id: int, session: DB, ctx: ConPermiso("usuarios.editar")) -> UsuarioDetalle:
    return UsuarioDetalle.model_validate(await servicio.desbloquear(session, ctx, usuario_id))


@router.post("/{usuario_id}/cerrar-sesiones", summary="Cerrar todas las sesiones del usuario")
async def cerrar_sesiones(usuario_id: int, session: DB, ctx: ConPermiso("usuarios.editar")) -> Mensaje:
    await servicio.cerrar_sesiones(session, ctx, usuario_id)
    return Mensaje(mensaje="Se cerraron todas las sesiones del usuario")
