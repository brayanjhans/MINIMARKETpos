import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import ColumnElement, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

TAMANIO_MAXIMO = 100


@dataclass(frozen=True, slots=True)
class ParametrosPaginacion:
    pagina: int
    tamanio: int

    @property
    def offset(self) -> int:
        return (self.pagina - 1) * self.tamanio


def parametros_paginacion(
    pagina: Annotated[int, Query(ge=1, description="Número de página")] = 1,
    tamanio: Annotated[int, Query(ge=1, le=TAMANIO_MAXIMO, description="Registros por página")] = 20,
) -> ParametrosPaginacion:
    return ParametrosPaginacion(pagina=pagina, tamanio=tamanio)


class Pagina[T](BaseModel):
    items: list[T]
    total: int
    pagina: int
    tamanio: int
    paginas: int


async def paginar(
    session: AsyncSession,
    consulta: Select[Any],
    params: ParametrosPaginacion,
    *,
    escalares: bool = True,
) -> tuple[list[Any], int]:
    """Ejecuta la consulta paginada y devuelve (items, total).

    `escalares=False` devuelve filas completas (para consultas con varias columnas).
    """
    consulta_total = select(func.count()).select_from(consulta.order_by(None).subquery())
    total = (await session.execute(consulta_total)).scalar_one()
    paginada = consulta.limit(params.tamanio).offset(params.offset)
    resultado = await session.execute(paginada)
    items = list(resultado.unique().scalars().all()) if escalares else list(resultado.all())
    return items, total


def aplicar_orden(
    consulta: Select[Any],
    orden: str | None,
    columnas: Mapping[str, ColumnElement[Any] | InstrumentedAttribute[Any]],
    defecto: str,
) -> Select[Any]:
    """Ordena por un campo permitido. Formato: "campo" (ascendente) o "-campo" (descendente).

    Los campos no permitidos se ignoran y se usa el orden por defecto (evita ordenar por columnas arbitrarias).
    """
    valor = orden if orden and orden.lstrip("-") in columnas else defecto
    descendente = valor.startswith("-")
    columna = columnas[valor.lstrip("-")]
    return consulta.order_by(columna.desc() if descendente else columna.asc())


def construir_pagina[T](items: list[T], total: int, params: ParametrosPaginacion) -> Pagina[T]:
    return Pagina[T](
        items=items,
        total=total,
        pagina=params.pagina,
        tamanio=params.tamanio,
        paginas=math.ceil(total / params.tamanio) if total else 0,
    )
