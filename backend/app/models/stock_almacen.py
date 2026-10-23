from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import CERO, Cantidad, FechaHora


class StockAlmacen(Base):
    """Stock en tiempo real por producto y almacén.

    Toda modificación se hace con SELECT ... FOR UPDATE sobre esta fila y deja un registro en el kardex.
    """

    __tablename__ = "stock_almacen"
    __table_args__ = (
        UniqueConstraint("producto_id", "almacen_id"),
        CheckConstraint("cantidad >= 0", name="cantidad_no_negativa"),
        CheckConstraint("stock_minimo IS NULL OR stock_minimo >= 0", name="stock_minimo_no_negativo"),
        Index("ix_stock_almacen_almacen_producto", "almacen_id", "producto_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="RESTRICT"))
    almacen_id: Mapped[int] = mapped_column(ForeignKey("almacenes.id", ondelete="RESTRICT"))
    cantidad: Mapped[Decimal] = mapped_column(Cantidad, default=CERO, server_default="0")
    # Si es NULL se usa el stock mínimo general del producto
    stock_minimo: Mapped[Decimal | None] = mapped_column(Cantidad)
    actualizado_en: Mapped[datetime] = mapped_column(
        FechaHora(), server_default=func.now(), onupdate=func.now()
    )
