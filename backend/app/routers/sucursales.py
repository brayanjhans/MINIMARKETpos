from fastapi import APIRouter
from sqlalchemy import select

from app.dependencies import DB, Contexto
from app.models import Sucursal
from app.schemas.sucursales import SucursalResumen

router = APIRouter(prefix="/sucursales", tags=["Sucursales"])


@router.get("", summary="Sucursales activas (para selectores)")
async def listar(session: DB, _: Contexto) -> list[SucursalResumen]:
    # La gestión completa de sucursales (crear/editar) se implementa en la fase de configuración
    sucursales = await session.scalars(select(Sucursal).where(Sucursal.activo.is_(True)).order_by(Sucursal.nombre))
    return [SucursalResumen.model_validate(s) for s in sucursales]
