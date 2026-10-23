from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import Cantidad, CostoUnitario, EnumTexto, FechaHora
from app.models.enums import TipoMovimientoInventario


class MovimientoInventario(Base):
    """Kardex: cada cambio de stock deja un registro inmutable (por almacén y, si aplica, por lote)."""

    __tablename__ = "movimientos_inventario"
    __table_args__ = (
        Index("ix_movimientos_inventario_producto_almacen_fecha", "producto_id", "almacen_id", "creado_en"),
        Index("ix_movimientos_inventario_referencia", "referencia_tipo", "referencia_id"),
        Index("ix_movimientos_inventario_almacen_fecha", "almacen_id", "creado_en"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="RESTRICT"))
    almacen_id: Mapped[int] = mapped_column(ForeignKey("almacenes.id", ondelete="RESTRICT"))
    lote_id: Mapped[int | None] = mapped_column(ForeignKey("lotes.id", ondelete="RESTRICT"))
    tipo: Mapped[TipoMovimientoInventario] = mapped_column(EnumTexto(TipoMovimientoInventario), index=True)
    # Positivo = entrada, negativo = salida (siempre en unidades base)
    cantidad: Mapped[Decimal] = mapped_column(Cantidad)
    # Stock del almacén antes y después del movimiento
    stock_anterior: Mapped[Decimal] = mapped_column(Cantidad)
    stock_nuevo: Mapped[Decimal] = mapped_column(Cantidad)
    costo_unitario: Mapped[Decimal] = mapped_column(CostoUnitario, server_default="0")
    # Documento que originó el movimiento: venta, devolucion, compra, ajuste, transferencia, inventario_fisico
    referencia_tipo: Mapped[str | None] = mapped_column(String(30))
    referencia_id: Mapped[int | None] = mapped_column(BigInteger)
    motivo: Mapped[str | None] = mapped_column(String(300))
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    creado_en: Mapped[datetime] = mapped_column(FechaHora(), server_default=func.now(), index=True)
