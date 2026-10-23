from typing import Annotated

from fastapi import APIRouter, Query, status

from app.dependencies import DB, ConPermiso
from app.schemas.clientes import ClienteCrear, ClienteSalida
from app.services import clientes as servicio

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("/buscar", summary="Buscar clientes por documento o nombre")
async def buscar(
    session: DB, ctx: ConPermiso("clientes.ver"), texto: Annotated[str | None, Query(max_length=100)] = None
) -> list[ClienteSalida]:
    return [ClienteSalida(**c) for c in await servicio.buscar(session, texto)]


@router.post("", status_code=status.HTTP_201_CREATED, summary="Crear un cliente (alta rápida desde el POS)")
async def crear(datos: ClienteCrear, session: DB, ctx: ConPermiso("clientes.crear")) -> ClienteSalida:
    return ClienteSalida(**await servicio.crear(session, ctx, datos))
