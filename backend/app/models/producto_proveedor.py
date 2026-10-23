from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, String, UniqueConstraint, false
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import CostoUnitario, TimestampMixin


class ProductoProveedor(TimestampMixin, Base):
    """Qué proveedores venden cada producto, con su último costo (sugerencias de compra y comparación)."""

    __tablename__ = "producto_proveedor"
    __table_args__ = (
        UniqueConstraint("producto_id", "proveedor_id"),
        CheckConstraint("ultimo_costo IS NULL OR ultimo_costo >= 0", name="ultimo_costo_no_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"), index=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id", ondelete="CASCADE"), index=True)
    codigo_proveedor: Mapped[str | None] = mapped_column(String(50))  # código del producto en su catálogo
    ultimo_costo: Mapped[Decimal | None] = mapped_column(CostoUnitario)
    fecha_ultima_compra: Mapped[date | None] = mapped_column(Date)
    es_principal: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
