from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import DB, ConPermiso
from app.schemas.auditoria import AuditoriaItem, ResumenAuditoria
from app.services import auditoria as servicio
from app.utils.paginacion import Pagina, ParametrosPaginacion, construir_pagina, parametros_paginacion

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])


@router.get("/resumen", summary="Conteos del periodo y la persona con más ingresos fallidos")
async def resumen(
    session: DB,
    _: ConPermiso("auditoria.ver"),
    desde: Annotated[date | None, Query(description="Fecha inicial (AAAA-MM-DD)")] = None,
    hasta: Annotated[date | None, Query(description="Fecha final (AAAA-MM-DD)")] = None,
) -> ResumenAuditoria:
    return ResumenAuditoria(**await servicio.resumen(session, desde, hasta))


@router.get("", summary="Historial de acciones de los usuarios")
async def listar(
    session: DB,
    _: ConPermiso("auditoria.ver"),
    params: Annotated[ParametrosPaginacion, Depends(parametros_paginacion)],
    usuario_id: int | None = None,
    sucursal_id: int | None = None,
    modulo: str | None = None,
    accion: str | None = None,
    desde: Annotated[date | None, Query(description="Fecha inicial (AAAA-MM-DD)")] = None,
    hasta: Annotated[date | None, Query(description="Fecha final (AAAA-MM-DD)")] = None,
    orden: str | None = None,
) -> Pagina[AuditoriaItem]:
    filas, total = await servicio.listar(
        session,
        params,
        usuario_id=usuario_id,
        sucursal_id=sucursal_id,
        modulo=modulo,
        accion=accion,
        desde=desde,
        hasta=hasta,
        orden=orden,
    )
    items = [
        AuditoriaItem.model_validate(registro).model_copy(update={"usuario_nombre": nombre})
        for registro, nombre in filas
    ]
    return construir_pagina(items, total, params)
