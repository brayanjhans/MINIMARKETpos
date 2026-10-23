from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import CostoUnitario, EnumTexto, FechaHora
from app.models.enums import TipoPrecio


class HistorialPrecio(Base):
    """Registro inmutable de cada cambio de precio de costo o de venta."""

    __tablename__ = "historial_precios"
    __table_args__ = (Index("ix_historial_precios_producto_fecha", "producto_id", "creado_en"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"))
    # Si el cambio fue en una presentación (six-pack, caja...) y no en la unidad base
    presentacion_id: Mapped[int | None] = mapped_column(
        ForeignKey("producto_presentaciones.id", ondelete="SET NULL")
    )
    tipo: Mapped[TipoPrecio] = mapped_column(EnumTexto(TipoPrecio))
    precio_anterior: Mapped[Decimal] = mapped_column(CostoUnitario)
    precio_nuevo: Mapped[Decimal] = mapped_column(CostoUnitario)
    # Origen del cambio: edición manual, compra (costo promedio), importación Excel
    origen: Mapped[str] = mapped_column(String(30))
    referencia_id: Mapped[int | None] = mapped_column(BigInteger)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    creado_en: Mapped[datetime] = mapped_column(FechaHora(), server_default=func.now(), index=True)
