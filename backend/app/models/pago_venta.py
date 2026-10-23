from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Dinero, EnumTexto
from app.models.enums import MetodoPago

if TYPE_CHECKING:
    from app.models.venta import Venta


class PagoVenta(Base):
    """Una venta puede tener varios pagos (pago mixto)."""

    __tablename__ = "pagos_venta"
    __table_args__ = (
        CheckConstraint("monto > 0", name="monto_positivo"),
        Index("ix_pagos_venta_metodo", "metodo"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id", ondelete="CASCADE"), index=True)
    metodo: Mapped[MetodoPago] = mapped_column(EnumTexto(MetodoPago))
    monto: Mapped[Decimal] = mapped_column(Dinero)  # monto aplicado a la venta
    monto_recibido: Mapped[Decimal | None] = mapped_column(Dinero)  # solo efectivo
    referencia: Mapped[str | None] = mapped_column(String(100))  # n° operación tarjeta/Yape/Plin

    venta: Mapped[Venta] = relationship(back_populates="pagos")
