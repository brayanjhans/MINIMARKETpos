from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constantes import PARAMETROS_SISTEMA
from app.models import ParametroSistema
from app.models.enums import TipoParametro


def _convertir(valor: Any, tipo: TipoParametro) -> Any:
    match tipo:
        case TipoParametro.ENTERO:
            return int(valor)
        case TipoParametro.DECIMAL:
            return Decimal(str(valor))
        case TipoParametro.BOOLEANO:
            return bool(valor)
        case TipoParametro.TEXTO:
            return str(valor)
        case _:
            return valor


async def obtener(session: AsyncSession, clave: str) -> Any:
    """Valor tipado de un parámetro. Si no existe en BD se usa el valor por defecto del catálogo."""
    parametro = await session.get(ParametroSistema, clave)
    if parametro is not None:
        return _convertir(parametro.valor, parametro.tipo)
    valor, tipo, _, _ = PARAMETROS_SISTEMA[clave]
    return _convertir(valor, TipoParametro(tipo))
