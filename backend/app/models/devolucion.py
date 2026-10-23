from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Index, String, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Cantidad, Dinero, EnumTexto, FechaHora
from app.models.enums import MetodoPago


class Devolucion(Base):
    """Devolución parcial o total de una venta. Reingresa stock y registra el reembolso."""

    __tablename__ = "devoluciones"
    __table_args__ = (
        CheckConstraint("total > 0", name="total_positivo"),
        Index("ix_devoluciones_sucursal_fecha", "sucursal_id", "fecha"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True)  # DV-000001
    venta_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ventas.id", ondelete="RESTRICT"), index=True)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id", ondelete="RESTRICT"))
    # Caja desde la que se entrega el reembolso (si es en efectivo, se descuenta del arqueo)
    sesion_caja_id: Mapped[int | None] = mapped_column(ForeignKey("sesiones_caja.id", ondelete="RESTRICT"))
    metodo_reembolso: Mapped[MetodoPago] = mapped_column(EnumTexto(MetodoPago))
    total: Mapped[Decimal] = mapped_column(Dinero)
    motivo: Mapped[str] = mapped_column(String(300))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    fecha: Mapped[datetime] = mapped_column(FechaHora(), server_default=func.now(), index=True)

    detalles: Mapped[list[DetalleDevolucion]] = relationship(
        back_populates="devolucion", cascade="all, delete-orphan"
    )


class DetalleDevolucion(Base):
    __tablename__ = "detalles_devolucion"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="cantidad_positiva"),
        CheckConstraint("total >= 0", name="total_no_negativo"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    devolucion_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("devoluciones.id", ondelete="CASCADE"), index=True
    )
    detalle_venta_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("detalles_venta.id", ondelete="RESTRICT"), index=True
    )
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="RESTRICT"))
    cantidad: Mapped[Decimal] = mapped_column(Cantidad)  # en la presentación vendida
    total: Mapped[Decimal] = mapped_column(Dinero)
    # False si el producto vuelve dañado/vencido y no debe regresar al stock vendible
    reingresa_stock: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    devolucion: Mapped[Devolucion] = relationship(back_populates="detalles")
