from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import CERO, Cantidad, CostoUnitario, Dinero, EnumTexto, FechaHora, TimestampMixin
from app.models.enums import CondicionPago, EstadoCompra, EstadoCuenta, MetodoPago

if TYPE_CHECKING:
    from app.models.proveedor import Proveedor


class Compra(TimestampMixin, Base):
    """Orden de compra. Al recepcionarse actualiza el stock (total o parcialmente)."""

    __tablename__ = "compras"
    __table_args__ = (
        CheckConstraint("total >= 0", name="total_no_negativo"),
        Index("ix_compras_proveedor_fecha", "proveedor_id", "fecha_emision"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True)  # correlativo interno OC-000001
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id", ondelete="RESTRICT"))
    # Almacén que recibe la mercadería (define la sucursal)
    almacen_id: Mapped[int] = mapped_column(ForeignKey("almacenes.id", ondelete="RESTRICT"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    # Documento del proveedor (factura/boleta/guía)
    tipo_documento: Mapped[str | None] = mapped_column(String(20))
    numero_documento: Mapped[str | None] = mapped_column(String(30))
    fecha_emision: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    fecha_recepcion: Mapped[datetime | None] = mapped_column(FechaHora(), index=True)
    estado: Mapped[EstadoCompra] = mapped_column(
        EnumTexto(EstadoCompra), default=EstadoCompra.PENDIENTE, server_default=EstadoCompra.PENDIENTE.value, index=True
    )
    condicion_pago: Mapped[CondicionPago] = mapped_column(
        EnumTexto(CondicionPago), default=CondicionPago.CONTADO, server_default=CondicionPago.CONTADO.value
    )
    subtotal: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    igv: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    total: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    observaciones: Mapped[str | None] = mapped_column(String(300))

    proveedor: Mapped[Proveedor] = relationship(lazy="joined")
    detalles: Mapped[list[DetalleCompra]] = relationship(
        back_populates="compra", cascade="all, delete-orphan"
    )
    cuenta_por_pagar: Mapped[CuentaPorPagar | None] = relationship(back_populates="compra")


class DetalleCompra(Base):
    __tablename__ = "detalles_compra"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="cantidad_positiva"),
        CheckConstraint("cantidad_recibida >= 0", name="cantidad_recibida_no_negativa"),
        CheckConstraint("cantidad_recibida <= cantidad", name="recibida_no_excede"),
        CheckConstraint("costo_unitario >= 0", name="costo_no_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    compra_id: Mapped[int] = mapped_column(ForeignKey("compras.id", ondelete="CASCADE"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="RESTRICT"), index=True)
    cantidad: Mapped[Decimal] = mapped_column(Cantidad)
    cantidad_recibida: Mapped[Decimal] = mapped_column(Cantidad, default=CERO, server_default="0")
    costo_unitario: Mapped[Decimal] = mapped_column(CostoUnitario)
    total: Mapped[Decimal] = mapped_column(Dinero)
    numero_lote: Mapped[str | None] = mapped_column(String(50))
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date)

    compra: Mapped[Compra] = relationship(back_populates="detalles")


class CuentaPorPagar(TimestampMixin, Base):
    __tablename__ = "cuentas_por_pagar"
    __table_args__ = (
        CheckConstraint("saldo >= 0", name="saldo_no_negativo"),
        CheckConstraint("saldo <= monto_total", name="saldo_no_excede_total"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    compra_id: Mapped[int] = mapped_column(ForeignKey("compras.id", ondelete="RESTRICT"), unique=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id", ondelete="RESTRICT"), index=True)
    monto_total: Mapped[Decimal] = mapped_column(Dinero)
    saldo: Mapped[Decimal] = mapped_column(Dinero)
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date, index=True)
    estado: Mapped[EstadoCuenta] = mapped_column(
        EnumTexto(EstadoCuenta), default=EstadoCuenta.PENDIENTE, server_default=EstadoCuenta.PENDIENTE.value, index=True
    )

    compra: Mapped[Compra] = relationship(back_populates="cuenta_por_pagar")
    pagos: Mapped[list[PagoProveedor]] = relationship(back_populates="cuenta")


class PagoProveedor(Base):
    __tablename__ = "pagos_proveedor"
    __table_args__ = (CheckConstraint("monto > 0", name="monto_positivo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cuenta_por_pagar_id: Mapped[int] = mapped_column(
        ForeignKey("cuentas_por_pagar.id", ondelete="RESTRICT"), index=True
    )
    monto: Mapped[Decimal] = mapped_column(Dinero)
    metodo: Mapped[MetodoPago] = mapped_column(EnumTexto(MetodoPago))
    referencia: Mapped[str | None] = mapped_column(String(100))
    # Si se paga en efectivo desde la caja, se registra también como egreso
    sesion_caja_id: Mapped[int | None] = mapped_column(ForeignKey("sesiones_caja.id", ondelete="RESTRICT"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    fecha: Mapped[datetime] = mapped_column(FechaHora(), server_default=func.now(), index=True)

    cuenta: Mapped[CuentaPorPagar] = relationship(back_populates="pagos")
