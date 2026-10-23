import enum
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Dialect, Enum, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

# Tipos numéricos reutilizables
Dinero = Numeric(12, 2)
CostoUnitario = Numeric(14, 4)
Cantidad = Numeric(12, 3)  # admite productos a granel (kg, litros)
Porcentaje = Numeric(5, 2)

CERO = Decimal("0")


def EnumTexto(clase: type[enum.Enum]) -> Enum:
    """Enum guardado como VARCHAR (sin tipo nativo) para facilitar migraciones."""
    return Enum(clase, native_enum=False, length=30, validate_strings=True)


class FechaHora(TypeDecorator[datetime]):
    """DATETIME guardado en UTC. MySQL no almacena zona horaria, así que se normaliza aquí
    y siempre se devuelve un datetime con tzinfo=UTC.

    Se descartan los microsegundos: MySQL los REDONDEA (no trunca) al guardar en DATETIME, lo que
    podía dejar fechas un segundo "en el futuro" y romper comparaciones (tokens, periodos de gracia).
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is not None:
            value = value.astimezone(UTC)
        return value.replace(tzinfo=None, microsecond=0)

    def process_result_value(self, value: Any, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC)


class TimestampMixin:
    creado_en: Mapped[datetime] = mapped_column(FechaHora(), server_default=func.now(), nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        FechaHora(), server_default=func.now(), onupdate=func.now(), nullable=False
    )
