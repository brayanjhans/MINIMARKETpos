"""Ejecución robusta de operaciones que cambian el stock.

- Reintento automático si MySQL detecta un interbloqueo (1213) o una espera de bloqueo excesiva (1205):
  la operación se repite desde cero con datos frescos.
- Idempotencia: si el cliente manda una clave (cabecera Idempotency-Key) y la operación ya se hizo, se devuelve
  el resultado de la primera vez en lugar de repetirla (doble clic, reintento de red, pestaña duplicada).
"""

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import Conflicto
from app.models import OperacionIdempotente

logger = logging.getLogger("minimarket.transacciones")

INTENTOS = 3
_REINTENTABLES = {1213, 1205}


def _codigo_mysql(exc: DBAPIError) -> int | None:
    args = getattr(exc.orig, "args", ())
    return args[0] if args and isinstance(args[0], int) else None


async def _previa(session: AsyncSession, usuario_id: int, clave: str, operacion: str) -> int | None:
    fila = await session.scalar(
        select(OperacionIdempotente).where(
            OperacionIdempotente.usuario_id == usuario_id, OperacionIdempotente.clave == clave
        )
    )
    if fila is None:
        return None
    if fila.operacion != operacion:
        raise Conflicto("Esta clave de operación ya se usó para otra acción", codigo="idempotencia")
    return fila.referencia_id if fila.referencia_id is not None else 0


async def ejecutar(
    session: AsyncSession,
    accion: Callable[[], Awaitable[int]],
    *,
    usuario_id: int,
    operacion: str,
    clave: str | None = None,
) -> int:
    """Ejecuta `accion` (que NO hace commit y devuelve el id del documento) y confirma la transacción.

    Devuelve ese id, o el de la ejecución anterior si la clave ya se había usado.
    """
    for intento in range(1, INTENTOS + 1):
        if clave:
            previa = await _previa(session, usuario_id, clave, operacion)
            if previa is not None:
                await session.rollback()
                return previa
        try:
            referencia = await accion()
            if clave:
                session.add(
                    OperacionIdempotente(
                        usuario_id=usuario_id, clave=clave, operacion=operacion, referencia_id=referencia
                    )
                )
            await session.commit()
            return referencia
        except DBAPIError as exc:
            await session.rollback()
            codigo = _codigo_mysql(exc)
            if clave and codigo == 1062:
                # Otra petición con la misma clave terminó primero: su resultado es el válido
                previa = await _previa(session, usuario_id, clave, operacion)
                if previa is not None:
                    await session.rollback()
                    return previa
            if codigo in _REINTENTABLES and intento < INTENTOS:
                logger.warning("Conflicto de concurrencia en %s (intento %d): se reintenta", operacion, intento)
                await asyncio.sleep(0.05 * intento + random.random() * 0.05)
                continue
            raise
        except BaseException:
            await session.rollback()
            raise
    raise AssertionError("inalcanzable")
