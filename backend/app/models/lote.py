from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Index, String, UniqueConstraint, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import CERO, Cantidad, CostoUnitario, TimestampMixin

if TYPE_CHECKING:
    from app.models.producto import Producto


class Lote(TimestampMixin, Base):
    """Lote de un producto en un almacén. La suma de lotes activos = stock del almacén (si maneja lotes)."""

    __tablename__ = "lotes"
    __table_args__ = (
        UniqueConstraint("producto_id", "almacen_id", "numero_lote"),
        CheckConstraint("cantidad_actual >= 0", name="cantidad_actual_no_negativa"),
        CheckConstraint("cantidad_inicial >= 0", name="cantidad_inicial_no_negativa"),
        # Lotes por vencimiento: salida FEFO y alertas de productos por vencer
        Index("ix_lotes_almacen_producto_vencimiento", "almacen_id", "producto_id", "fecha_vencimiento"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="RESTRICT"), index=True)
    almacen_id: Mapped[int] = mapped_column(ForeignKey("almacenes.id", ondelete="RESTRICT"))
    numero_lote: Mapped[str] = mapped_column(String(50))
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date, index=True)
    cantidad_inicial: Mapped[Decimal] = mapped_column(Cantidad, default=CERO)
    cantidad_actual: Mapped[Decimal] = mapped_column(Cantidad, default=CERO)
    costo_unitario: Mapped[Decimal] = mapped_column(CostoUnitario, default=CERO, server_default="0")
    compra_id: Mapped[int | None] = mapped_column(ForeignKey("compras.id", ondelete="SET NULL"))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    producto: Mapped[Producto] = relationship(back_populates="lotes")
