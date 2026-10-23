from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import CERO, Cantidad, CostoUnitario, EnumTexto, FechaHora, TimestampMixin
from app.models.enums import EstadoTransferencia

if TYPE_CHECKING:
    from app.models.lote import Lote
    from app.models.producto import Producto
    from app.models.sucursal import Almacen


class Transferencia(TimestampMixin, Base):
    """Traslado de mercadería entre almacenes (de la misma o de distinta sucursal).

    Al enviar se descuenta del origen y la mercadería queda "en tránsito" (valorizada con los detalles de las
    transferencias EN_TRANSITO); al recibir se suma al destino lo efectivamente recibido y lo que no llegó
    se registra como merma.
    """

    __tablename__ = "transferencias"
    __table_args__ = (
        CheckConstraint("almacen_origen_id <> almacen_destino_id", name="origen_distinto_destino"),
        Index("ix_transferencias_origen_estado", "almacen_origen_id", "estado"),
        Index("ix_transferencias_destino_estado", "almacen_destino_id", "estado"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True)  # TR-000001
    almacen_origen_id: Mapped[int] = mapped_column(ForeignKey("almacenes.id", ondelete="RESTRICT"))
    almacen_destino_id: Mapped[int] = mapped_column(ForeignKey("almacenes.id", ondelete="RESTRICT"))
    estado: Mapped[EstadoTransferencia] = mapped_column(
        EnumTexto(EstadoTransferencia),
        default=EstadoTransferencia.PENDIENTE,
        server_default=EstadoTransferencia.PENDIENTE.value,
    )
    observaciones: Mapped[str | None] = mapped_column(String(300))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    usuario_recibe_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    fecha_envio: Mapped[datetime | None] = mapped_column(FechaHora(), index=True)
    fecha_recepcion: Mapped[datetime | None] = mapped_column(FechaHora())

    almacen_origen: Mapped[Almacen] = relationship(foreign_keys=[almacen_origen_id], lazy="joined")
    almacen_destino: Mapped[Almacen] = relationship(foreign_keys=[almacen_destino_id], lazy="joined")
    detalles: Mapped[list[DetalleTransferencia]] = relationship(
        back_populates="transferencia", cascade="all, delete-orphan", order_by="DetalleTransferencia.id"
    )


class DetalleTransferencia(Base):
    """Una línea por producto, o por lote de origen si maneja lotes (un producto puede ir en varios lotes)."""

    __tablename__ = "detalles_transferencia"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="cantidad_positiva"),
        CheckConstraint("cantidad_recibida >= 0", name="cantidad_recibida_no_negativa"),
        CheckConstraint("cantidad_recibida <= cantidad", name="recibida_no_excede"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    transferencia_id: Mapped[int] = mapped_column(ForeignKey("transferencias.id", ondelete="CASCADE"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="RESTRICT"), index=True)
    lote_id: Mapped[int | None] = mapped_column(ForeignKey("lotes.id", ondelete="RESTRICT"))
    cantidad: Mapped[Decimal] = mapped_column(Cantidad)
    cantidad_recibida: Mapped[Decimal] = mapped_column(Cantidad, default=CERO, server_default="0")
    # Costo al enviar: valoriza lo que está en tránsito y la merma de lo que no llegó
    costo_unitario: Mapped[Decimal] = mapped_column(CostoUnitario, default=CERO, server_default="0")
    motivo_faltante: Mapped[str | None] = mapped_column(String(150))

    transferencia: Mapped[Transferencia] = relationship(back_populates="detalles")
    producto: Mapped[Producto] = relationship(lazy="joined")
    lote: Mapped[Lote | None] = relationship(lazy="joined")
