from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Correlativo


async def siguiente(session: AsyncSession, clave: str) -> str:
    """Siguiente número de documento (AJ-000001...). La fila queda bloqueada hasta el commit:
    dos usuarios nunca reciben el mismo número y, si la operación falla, el número no se pierde."""
    correlativo = await session.scalar(select(Correlativo).where(Correlativo.clave == clave).with_for_update())
    if correlativo is None:
        raise RuntimeError(f"No existe el correlativo {clave}: ejecute el seed")
    correlativo.ultimo_numero += 1
    return f"{correlativo.prefijo}-{correlativo.ultimo_numero:0{correlativo.longitud}d}"
