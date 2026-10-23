from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.excepciones import ValidacionNegocio
from app.dependencies import DB, ConPermiso
from app.dependencies.idempotencia import ClaveIdempotencia
from app.models.enums import EstadoVenta, MetodoPago
from app.schemas.ventas import (
    AnulacionEntrada,
    AutorizacionEntrada,
    AutorizacionSalida,
    CatalogoPos,
    VentaCrear,
    VentaDetalle,
    VentaListado,
    VerificacionTicket,
)
from app.services import autorizaciones
from app.services import ventas as servicio
from app.utils.paginacion import Pagina, ParametrosPaginacion, construir_pagina, parametros_paginacion

router = APIRouter(prefix="/ventas", tags=["Ventas"])

Paginacion = Annotated[ParametrosPaginacion, Depends(parametros_paginacion)]


@router.get("/catalogo", summary="Productos activos con códigos, presentaciones, precio y stock (para el POS)")
async def catalogo(session: DB, ctx: ConPermiso("pos.vender")) -> CatalogoPos:
    return CatalogoPos(**await servicio.catalogo(session, ctx))


@router.get("/resumen-hoy", summary="Ventas de hoy: total, tickets, promedio, por método y por hora")
async def resumen_hoy(session: DB, ctx: ConPermiso("pos.vender")) -> dict:
    return await servicio.resumen_hoy(session, ctx)


@router.get("/verificar", summary="Verificar un ticket por su QR o su número")
async def verificar(
    session: DB, ctx: ConPermiso("pos.vender"), texto: Annotated[str, Query(min_length=3, max_length=300)]
) -> VerificacionTicket:
    return VerificacionTicket(**await servicio.verificar(session, ctx, texto))


@router.post("", status_code=status.HTTP_201_CREATED, summary="Registrar una venta (requiere Idempotency-Key)")
async def registrar(
    datos: VentaCrear, session: DB, ctx: ConPermiso("pos.vender"), clave: ClaveIdempotencia = None
) -> VentaDetalle:
    if not clave:
        # Una venta nunca debe duplicarse por un doble clic o un reintento de red
        raise ValidacionNegocio("Falta la clave de la operación (Idempotency-Key)", codigo="sin_clave")
    venta_id = await servicio.registrar(session, ctx, datos, clave)
    return VentaDetalle(**await servicio.detalle(session, ctx, venta_id))


@router.post("/autorizar", summary="Clave del supervisor para una acción en esta caja")
async def autorizar(datos: AutorizacionEntrada, session: DB, ctx: ConPermiso("pos.vender")) -> AutorizacionSalida:
    token, nombre = await autorizaciones.autorizar(session, ctx, datos.username, datos.password, datos.permiso)
    return AutorizacionSalida(
        token=token, supervisor=nombre, permiso=datos.permiso, expira_en_segundos=autorizaciones.MINUTOS_VALIDEZ * 60
    )


@router.post("/{venta_id}/anular", summary="Anular una venta (mientras su turno de caja siga abierto)")
async def anular(
    venta_id: int, datos: AnulacionEntrada, session: DB, ctx: ConPermiso("pos.vender"), clave: ClaveIdempotencia = None
) -> VentaDetalle:
    await servicio.anular(session, ctx, venta_id, datos, clave)
    return VentaDetalle(**await servicio.detalle(session, ctx, venta_id))


@router.get("", summary="Ventas (las propias, o de todos con caja.ver_todas)")
async def listar(
    session: DB,
    ctx: ConPermiso("pos.vender"),
    params: Paginacion,
    sesion_caja_id: int | None = None,
    usuario_id: int | None = None,
    estado: EstadoVenta | None = None,
    metodo: MetodoPago | None = None,
    busqueda: Annotated[str | None, Query(max_length=100)] = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> Pagina[VentaListado]:
    items, total = await servicio.listar(
        session,
        ctx,
        params,
        sesion_caja_id=sesion_caja_id,
        usuario_id=usuario_id,
        estado=estado,
        metodo=metodo,
        busqueda=busqueda,
        desde=desde,
        hasta=hasta,
    )
    return construir_pagina([VentaListado(**i) for i in items], total, params)


@router.get("/{venta_id}", summary="Detalle de la venta con los datos para el ticket")
async def detalle(venta_id: int, session: DB, ctx: ConPermiso("pos.vender")) -> VentaDetalle:
    return VentaDetalle(**await servicio.detalle(session, ctx, venta_id))
