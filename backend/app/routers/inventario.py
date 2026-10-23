from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import DB, ConPermiso
from app.dependencies.idempotencia import ClaveIdempotencia
from app.models.enums import EstadoDocumento, EstadoInventarioFisico, EstadoTransferencia, TipoMovimientoInventario
from app.schemas.inventario import (
    AjusteActualizar,
    AjusteCrear,
    AjusteDetalle,
    AjusteListado,
    AlmacenSalida,
    ConteoEntrada,
    FisicoDetalle,
    FisicoListado,
    InventarioFisicoCrear,
    LoteSalida,
    MotivoAjusteSalida,
    MovimientoSalida,
    ProductoCargable,
    RecepcionEntrada,
    Rechazo,
    ReporteIntegridad,
    ResumenInventario,
    StockFila,
    StockInicialEntrada,
    StockInicialResultado,
    TransferenciaCrear,
    TransferenciaDetalle,
    TransferenciaListado,
)
from app.services import ajustes, inventario, inventario_fisico, transferencias
from app.utils.paginacion import Pagina, ParametrosPaginacion, construir_pagina, parametros_paginacion

router = APIRouter(prefix="/inventario", tags=["Inventario"])

Paginacion = Annotated[ParametrosPaginacion, Depends(parametros_paginacion)]
AlmacenId = Annotated[int | None, Query(description="Vacío = almacén de venta de la sucursal actual")]


# --- Consultas ---------------------------------------------------------------------------------------------


@router.get("/almacenes", summary="Almacenes activos (los de la sucursal actual primero)")
async def almacenes(session: DB, ctx: ConPermiso("inventario.ver")) -> list[AlmacenSalida]:
    return [AlmacenSalida(**a) for a in await inventario.almacenes(session, ctx)]


@router.get("/resumen", summary="Valor, alertas, mermas del mes, por aprobar y en tránsito")
async def resumen(session: DB, ctx: ConPermiso("inventario.ver"), almacen_id: AlmacenId = None) -> ResumenInventario:
    return ResumenInventario(**await inventario.resumen(session, ctx, almacen_id))


@router.get("/stock", summary="Stock por producto en un almacén")
async def stock(
    session: DB,
    ctx: ConPermiso("inventario.ver"),
    params: Paginacion,
    almacen_id: AlmacenId = None,
    busqueda: Annotated[str | None, Query(max_length=100)] = None,
    categoria_id: int | None = None,
    estado: Annotated[str | None, Query(pattern="^(bajo|sin_stock|con_stock|por_regularizar)$")] = None,
    orden: Annotated[str | None, Query(description="nombre, stock, valor (- = desc)")] = None,
) -> Pagina[StockFila]:
    items, total = await inventario.listar_stock(
        session,
        ctx,
        params,
        almacen_id=almacen_id,
        busqueda=busqueda,
        categoria_id=categoria_id,
        estado=estado,
        orden=orden,
    )
    return construir_pagina([StockFila(**i) for i in items], total, params)


@router.get("/lotes", summary="Lotes con saldo (por vencimiento)")
async def lotes(
    session: DB,
    ctx: ConPermiso("inventario.ver"),
    almacen_id: AlmacenId = None,
    producto_id: int | None = None,
    por_vencer_dias: Annotated[int | None, Query(ge=0, le=3650)] = None,
    vencidos: bool = False,
) -> list[LoteSalida]:
    filas = await inventario.listar_lotes(
        session,
        ctx,
        almacen_id=almacen_id,
        producto_id=producto_id,
        por_vencer_dias=por_vencer_dias,
        solo_vencidos=vencidos,
    )
    return [LoteSalida(**f) for f in filas]


@router.get("/kardex", summary="Movimientos de stock (kardex) con saldo")
async def kardex(
    session: DB,
    ctx: ConPermiso("inventario.kardex"),
    params: Paginacion,
    almacen_id: AlmacenId = None,
    producto_id: int | None = None,
    tipo: TipoMovimientoInventario | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> Pagina[MovimientoSalida]:
    items, total = await inventario.kardex(
        session, ctx, params, almacen_id=almacen_id, producto_id=producto_id, tipo=tipo, desde=desde, hasta=hasta
    )
    return construir_pagina([MovimientoSalida(**i) for i in items], total, params)


@router.get("/integridad", summary="Revisa que stock = kardex = lotes (debe dar cero problemas)")
async def integridad(session: DB, ctx: ConPermiso("inventario.integridad")) -> ReporteIntegridad:
    reporte = await inventario.revisar_integridad(session)
    await inventario.registrar_revision(session, ctx, reporte)
    return ReporteIntegridad(**reporte)


@router.get("/motivos-ajuste", summary="Motivos de ajuste y merma")
async def motivos(session: DB, _: ConPermiso("inventario.ver")) -> list[MotivoAjusteSalida]:
    return [MotivoAjusteSalida.model_validate(m) for m in await inventario.motivos_ajuste(session)]


# --- Stock inicial -----------------------------------------------------------------------------------------


@router.get("/stock-inicial/cargables", summary="Qué productos pueden recibir stock inicial en el almacén")
async def cargables(
    session: DB,
    ctx: ConPermiso("inventario.stock_inicial"),
    producto_ids: Annotated[list[int], Query(max_length=500)],
    almacen_id: AlmacenId = None,
) -> list[ProductoCargable]:
    return [ProductoCargable(**f) for f in await inventario.cargables(session, ctx, producto_ids, almacen_id)]


@router.post("/stock-inicial", summary="Cargar stock inicial (una vez por producto y almacén)")
async def stock_inicial(
    datos: StockInicialEntrada,
    session: DB,
    ctx: ConPermiso("inventario.stock_inicial"),
    clave: ClaveIdempotencia = None,
) -> StockInicialResultado:
    return StockInicialResultado(**await inventario.cargar_stock_inicial(session, ctx, datos, clave))


# --- Ajustes -----------------------------------------------------------------------------------------------


@router.get("/ajustes", summary="Ajustes y mermas del almacén")
async def listar_ajustes(
    session: DB,
    ctx: ConPermiso("inventario.ver"),
    params: Paginacion,
    almacen_id: AlmacenId = None,
    estado: EstadoDocumento | None = None,
) -> Pagina[AjusteListado]:
    items, total = await ajustes.listar(session, ctx, params, almacen_id=almacen_id, estado=estado)
    return construir_pagina([AjusteListado(**i) for i in items], total, params)


@router.get("/ajustes/{ajuste_id}", summary="Detalle de un ajuste")
async def obtener_ajuste(ajuste_id: int, session: DB, ctx: ConPermiso("inventario.ver")) -> AjusteDetalle:
    return AjusteDetalle(**await ajustes.obtener(session, ctx, ajuste_id))


@router.post("/ajustes", summary="Registrar ajuste o merma (queda por aprobar)", status_code=status.HTTP_201_CREATED)
async def crear_ajuste(
    datos: AjusteCrear, session: DB, ctx: ConPermiso("inventario.ajustar"), clave: ClaveIdempotencia = None
) -> AjusteDetalle:
    ajuste_id = await ajustes.crear(session, ctx, datos, clave)
    return AjusteDetalle(**await ajustes.obtener(session, ctx, ajuste_id))


@router.put("/ajustes/{ajuste_id}", summary="Editar un ajuste en borrador")
async def editar_ajuste(
    ajuste_id: int, datos: AjusteActualizar, session: DB, ctx: ConPermiso("inventario.ajustar")
) -> AjusteDetalle:
    await ajustes.actualizar(session, ctx, ajuste_id, datos)
    return AjusteDetalle(**await ajustes.obtener(session, ctx, ajuste_id))


@router.post("/ajustes/{ajuste_id}/enviar", summary="Enviar borrador a aprobación")
async def enviar_ajuste(ajuste_id: int, session: DB, ctx: ConPermiso("inventario.ajustar")) -> AjusteDetalle:
    await ajustes.enviar(session, ctx, ajuste_id)
    return AjusteDetalle(**await ajustes.obtener(session, ctx, ajuste_id))


@router.post("/ajustes/{ajuste_id}/aprobar", summary="Aprobar y aplicar al stock")
async def aprobar_ajuste(ajuste_id: int, session: DB, ctx: ConPermiso("inventario.aprobar_ajustes")) -> AjusteDetalle:
    await ajustes.aprobar(session, ctx, ajuste_id)
    return AjusteDetalle(**await ajustes.obtener(session, ctx, ajuste_id))


@router.post("/ajustes/{ajuste_id}/rechazar", summary="Rechazar (no cambia el stock)")
async def rechazar_ajuste(
    ajuste_id: int, datos: Rechazo, session: DB, ctx: ConPermiso("inventario.aprobar_ajustes")
) -> AjusteDetalle:
    await ajustes.rechazar(session, ctx, ajuste_id, datos.motivo)
    return AjusteDetalle(**await ajustes.obtener(session, ctx, ajuste_id))


@router.post("/ajustes/{ajuste_id}/anular", summary="Anular un borrador o un ajuste por aprobar")
async def anular_ajuste(ajuste_id: int, session: DB, ctx: ConPermiso("inventario.ajustar")) -> AjusteDetalle:
    await ajustes.anular(session, ctx, ajuste_id)
    return AjusteDetalle(**await ajustes.obtener(session, ctx, ajuste_id))


# --- Transferencias ----------------------------------------------------------------------------------------


@router.get("/transferencias", summary="Transferencias que salen de o llegan a la sucursal actual")
async def listar_transferencias(
    session: DB, ctx: ConPermiso("inventario.ver"), params: Paginacion, estado: EstadoTransferencia | None = None
) -> Pagina[TransferenciaListado]:
    items, total = await transferencias.listar(session, ctx, params, estado=estado)
    return construir_pagina([TransferenciaListado(**i) for i in items], total, params)


@router.get("/transferencias/{transferencia_id}", summary="Detalle de una transferencia")
async def obtener_transferencia(
    transferencia_id: int, session: DB, ctx: ConPermiso("inventario.ver")
) -> TransferenciaDetalle:
    return TransferenciaDetalle(**await transferencias.obtener(session, ctx, transferencia_id))


@router.post("/transferencias", summary="Crear (y enviar) una transferencia", status_code=status.HTTP_201_CREATED)
async def crear_transferencia(
    datos: TransferenciaCrear, session: DB, ctx: ConPermiso("inventario.transferir"), clave: ClaveIdempotencia = None
) -> TransferenciaDetalle:
    transferencia_id = await transferencias.crear(session, ctx, datos, clave)
    return TransferenciaDetalle(**await transferencias.obtener(session, ctx, transferencia_id))


@router.post("/transferencias/{transferencia_id}/enviar", summary="Enviar una transferencia preparada")
async def enviar_transferencia(
    transferencia_id: int, session: DB, ctx: ConPermiso("inventario.transferir")
) -> TransferenciaDetalle:
    await transferencias.enviar(session, ctx, transferencia_id)
    return TransferenciaDetalle(**await transferencias.obtener(session, ctx, transferencia_id))


@router.post("/transferencias/{transferencia_id}/recibir", summary="Confirmar lo que llegó (lo demás es faltante)")
async def recibir_transferencia(
    transferencia_id: int, datos: RecepcionEntrada, session: DB, ctx: ConPermiso("inventario.recibir_transferencia")
) -> TransferenciaDetalle:
    await transferencias.recibir(session, ctx, transferencia_id, datos)
    return TransferenciaDetalle(**await transferencias.obtener(session, ctx, transferencia_id))


@router.post("/transferencias/{transferencia_id}/anular", summary="Anular (si estaba en tránsito, vuelve al origen)")
async def anular_transferencia(
    transferencia_id: int, session: DB, ctx: ConPermiso("inventario.transferir")
) -> TransferenciaDetalle:
    await transferencias.anular(session, ctx, transferencia_id)
    return TransferenciaDetalle(**await transferencias.obtener(session, ctx, transferencia_id))


# --- Inventario físico -------------------------------------------------------------------------------------


@router.get("/fisicos", summary="Inventarios físicos del almacén")
async def listar_fisicos(
    session: DB,
    ctx: ConPermiso("inventario.ver"),
    params: Paginacion,
    almacen_id: AlmacenId = None,
    estado: EstadoInventarioFisico | None = None,
) -> Pagina[FisicoListado]:
    items, total = await inventario_fisico.listar(session, ctx, params, almacen_id=almacen_id, estado=estado)
    return construir_pagina([FisicoListado(**i) for i in items], total, params)


@router.get("/fisicos/{inventario_id}", summary="Detalle de un inventario físico")
async def obtener_fisico(inventario_id: int, session: DB, ctx: ConPermiso("inventario.ver")) -> FisicoDetalle:
    return FisicoDetalle(**await inventario_fisico.obtener(session, ctx, inventario_id))


@router.post(
    "/fisicos", summary="Iniciar un inventario físico (guarda el stock actual)", status_code=status.HTTP_201_CREATED
)
async def crear_fisico(
    datos: InventarioFisicoCrear,
    session: DB,
    ctx: ConPermiso("inventario.inventario_fisico"),
    clave: ClaveIdempotencia = None,
) -> FisicoDetalle:
    inventario_id = await inventario_fisico.crear(session, ctx, datos, clave)
    return FisicoDetalle(**await inventario_fisico.obtener(session, ctx, inventario_id))


@router.put("/fisicos/{inventario_id}/conteos", summary="Guardar cantidades contadas (avance)")
async def guardar_conteo(
    inventario_id: int, datos: ConteoEntrada, session: DB, ctx: ConPermiso("inventario.inventario_fisico")
) -> FisicoDetalle:
    await inventario_fisico.registrar_conteo(session, ctx, inventario_id, datos)
    return FisicoDetalle(**await inventario_fisico.obtener(session, ctx, inventario_id))


@router.post("/fisicos/{inventario_id}/enviar", summary="Enviar el conteo a aprobación")
async def enviar_fisico(
    inventario_id: int, session: DB, ctx: ConPermiso("inventario.inventario_fisico")
) -> FisicoDetalle:
    await inventario_fisico.enviar(session, ctx, inventario_id)
    return FisicoDetalle(**await inventario_fisico.obtener(session, ctx, inventario_id))


@router.post("/fisicos/{inventario_id}/aprobar", summary="Aprobar y aplicar solo las diferencias")
async def aprobar_fisico(
    inventario_id: int, session: DB, ctx: ConPermiso("inventario.aprobar_ajustes")
) -> FisicoDetalle:
    await inventario_fisico.aprobar(session, ctx, inventario_id)
    return FisicoDetalle(**await inventario_fisico.obtener(session, ctx, inventario_id))


@router.post("/fisicos/{inventario_id}/rechazar", summary="Devolver para recontar")
async def rechazar_fisico(
    inventario_id: int, datos: Rechazo, session: DB, ctx: ConPermiso("inventario.aprobar_ajustes")
) -> FisicoDetalle:
    await inventario_fisico.rechazar(session, ctx, inventario_id, datos.motivo)
    return FisicoDetalle(**await inventario_fisico.obtener(session, ctx, inventario_id))


@router.post("/fisicos/{inventario_id}/cancelar", summary="Cancelar un conteo abierto")
async def cancelar_fisico(
    inventario_id: int, session: DB, ctx: ConPermiso("inventario.inventario_fisico")
) -> FisicoDetalle:
    await inventario_fisico.cancelar(session, ctx, inventario_id)
    return FisicoDetalle(**await inventario_fisico.obtener(session, ctx, inventario_id))
