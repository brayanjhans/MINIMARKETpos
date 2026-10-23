from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import CERO, Cantidad, CostoUnitario, Dinero, EnumTexto, FechaHora, TimestampMixin
from app.models.enums import EstadoVenta, TipoAfectacionIGV, TipoComprobante

if TYPE_CHECKING:
    from app.models.cliente import Cliente
    from app.models.pago_venta import PagoVenta
    from app.models.usuario import Usuario


class Venta(TimestampMixin, Base):
    """Comprobante de venta.

    total = op_gravadas + op_exoneradas + op_inafectas + igv + icbper (descuentos ya aplicados).
    """

    __tablename__ = "ventas"
    __table_args__ = (
        UniqueConstraint("serie", "numero"),
        CheckConstraint("total >= 0", name="total_no_negativo"),
        CheckConstraint("descuento >= 0", name="descuento_no_negativo"),
        CheckConstraint("total_devuelto >= 0 AND total_devuelto <= total", name="devuelto_valido"),
        Index("ix_ventas_sucursal_fecha_estado", "sucursal_id", "fecha", "estado"),
        Index("ix_ventas_fecha_estado", "fecha", "estado"),
        Index("ix_ventas_usuario_fecha", "usuario_id", "fecha"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id", ondelete="RESTRICT"))
    almacen_id: Mapped[int] = mapped_column(ForeignKey("almacenes.id", ondelete="RESTRICT"))
    tipo_comprobante: Mapped[TipoComprobante] = mapped_column(EnumTexto(TipoComprobante))
    serie: Mapped[str] = mapped_column(String(4))
    numero: Mapped[int] = mapped_column(Integer)
    fecha: Mapped[datetime] = mapped_column(FechaHora(), server_default=func.now(), index=True)
    sesion_caja_id: Mapped[int] = mapped_column(ForeignKey("sesiones_caja.id", ondelete="RESTRICT"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id", ondelete="RESTRICT"), index=True)
    # Totales desglosados por afectación (requeridos en boletas y facturas)
    op_gravadas: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    op_exoneradas: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    op_inafectas: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    igv: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    icbper: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    descuento: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    total: Mapped[Decimal] = mapped_column(Dinero)
    redondeo: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    vuelto: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    total_devuelto: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    es_credito: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    estado: Mapped[EstadoVenta] = mapped_column(
        EnumTexto(EstadoVenta), default=EstadoVenta.COMPLETADA, server_default=EstadoVenta.COMPLETADA.value
    )
    observaciones: Mapped[str | None] = mapped_column(String(300))
    # Anulación (venta completa)
    anulada_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    fecha_anulacion: Mapped[datetime | None] = mapped_column(FechaHora())
    motivo_anulacion: Mapped[str | None] = mapped_column(String(300))

    usuario: Mapped[Usuario] = relationship(foreign_keys=[usuario_id])
    cliente: Mapped[Cliente | None] = relationship()
    detalles: Mapped[list[DetalleVenta]] = relationship(back_populates="venta", cascade="all, delete-orphan")
    pagos: Mapped[list[PagoVenta]] = relationship(back_populates="venta", cascade="all, delete-orphan")


class DetalleVenta(Base):
    __tablename__ = "detalles_venta"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="cantidad_positiva"),
        CheckConstraint("factor > 0", name="factor_positivo"),
        CheckConstraint("precio_unitario >= 0", name="precio_unitario_no_negativo"),
        CheckConstraint("descuento >= 0", name="descuento_no_negativo"),
        # La BD impide devolver más de lo vendido
        CheckConstraint("cantidad_devuelta >= 0 AND cantidad_devuelta <= cantidad", name="devuelta_valida"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    venta_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ventas.id", ondelete="CASCADE"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="RESTRICT"), index=True)
    presentacion_id: Mapped[int | None] = mapped_column(
        ForeignKey("producto_presentaciones.id", ondelete="RESTRICT")
    )
    # Copia del nombre al momento de la venta (el ticket no cambia si se edita el producto)
    descripcion: Mapped[str] = mapped_column(String(200))
    cantidad: Mapped[Decimal] = mapped_column(Cantidad)  # en la presentación vendida
    factor: Mapped[Decimal] = mapped_column(Cantidad, default=Decimal("1"), server_default="1")  # unidades base
    precio_unitario: Mapped[Decimal] = mapped_column(Dinero)
    costo_unitario: Mapped[Decimal] = mapped_column(CostoUnitario)  # costo por unidad base, para ganancias
    descuento: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    tipo_afectacion_igv: Mapped[TipoAfectacionIGV] = mapped_column(EnumTexto(TipoAfectacionIGV))
    igv: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    icbper: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    total: Mapped[Decimal] = mapped_column(Dinero)
    cantidad_devuelta: Mapped[Decimal] = mapped_column(Cantidad, default=CERO, server_default="0")

    venta: Mapped[Venta] = relationship(back_populates="detalles")
