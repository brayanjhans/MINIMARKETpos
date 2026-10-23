from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies import DB, ConPermiso
from app.dependencies.idempotencia import ClaveIdempotencia
from app.models.enums import EstadoSesionCaja
from app.schemas.caja import (
    AperturaEntrada,
    CajaSalida,
    CierreEntrada,
    EstadoCaja,
    MovimientoCajaEntrada,
    SesionDetalle,
    SesionSalida,
)
from app.services import caja as servicio
from app.utils.paginacion import Pagina, ParametrosPaginacion, construir_pagina, parametros_paginacion

router = APIRouter(prefix="/caja", tags=["Caja"])

Paginacion = Annotated[ParametrosPaginacion, Depends(parametros_paginacion)]


@router.get("/cajas", summary="Cajas de la sucursal y quién tiene abierta cada una")
async def cajas(session: DB, ctx: ConPermiso("caja.ver")) -> list[CajaSalida]:
    return [CajaSalida(**c) for c in await servicio.cajas(session, ctx)]


@router.get("/actual", summary="Turno de caja abierto del usuario (o ninguno)")
async def actual(session: DB, ctx: ConPermiso("caja.ver")) -> EstadoCaja:
    return EstadoCaja(**await servicio.actual(session, ctx))


@router.post("/abrir", status_code=status.HTTP_201_CREATED, summary="Abrir caja con monto inicial")
async def abrir(
    datos: AperturaEntrada, session: DB, ctx: ConPermiso("caja.abrir"), clave: ClaveIdempotencia = None
) -> SesionDetalle:
    sesion_id = await servicio.abrir(session, ctx, datos, clave)
    return SesionDetalle(**await servicio.detalle(session, ctx, sesion_id))


@router.post("/movimientos", status_code=status.HTTP_201_CREATED, summary="Ingreso o egreso de efectivo")
async def movimiento(
    datos: MovimientoCajaEntrada, session: DB, ctx: ConPermiso("caja.movimientos"), clave: ClaveIdempotencia = None
) -> SesionDetalle:
    await servicio.registrar_movimiento(session, ctx, datos, clave)
    abierta = await servicio.sesion_abierta(session, ctx.usuario_id)
    return SesionDetalle(**await servicio.detalle(session, ctx, abierta.id))


@router.post("/sesiones/{sesion_id}/cerrar", summary="Cerrar caja con arqueo (cierre ciego)")
async def cerrar(
    sesion_id: int, datos: CierreEntrada, session: DB, ctx: ConPermiso("caja.cerrar"), clave: ClaveIdempotencia = None
) -> SesionDetalle:
    await servicio.cerrar(session, ctx, sesion_id, datos, clave)
    return SesionDetalle(**await servicio.detalle(session, ctx, sesion_id))


@router.get("/sesiones", summary="Historial de turnos (propios, o de todos con caja.ver_todas)")
async def sesiones(
    session: DB,
    ctx: ConPermiso("caja.ver"),
    params: Paginacion,
    usuario_id: int | None = None,
    estado: EstadoSesionCaja | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> Pagina[SesionSalida]:
    items, total = await servicio.listar(
        session, ctx, params, usuario_id=usuario_id, estado=estado, desde=desde, hasta=hasta
    )
    return construir_pagina([SesionSalida(**i) for i in items], total, params)


@router.get("/sesiones/{sesion_id}", summary="Detalle de un turno: métodos de pago, movimientos y arqueo")
async def sesion(sesion_id: int, session: DB, ctx: ConPermiso("caja.ver")) -> SesionDetalle:
    return SesionDetalle(**await servicio.detalle(session, ctx, sesion_id))


@router.get("/cajeros", summary="Cajeros con turnos en la sucursal")
async def cajeros(session: DB, ctx: ConPermiso("caja.ver_todas")) -> list[dict]:
    return await servicio.cajeros(session, ctx)
