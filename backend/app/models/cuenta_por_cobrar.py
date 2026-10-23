from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Dinero, EnumTexto, FechaHora, TimestampMixin
from app.models.enums import EstadoCuenta, MetodoPago

if TYPE_CHECKING:
    from app.models.cliente import Cliente


class CuentaPorCobrar(TimestampMixin, Base):
    """Deuda generada por una venta al fiado."""

    __tablename__ = "cuentas_por_cobrar"
    __table_args__ = (
        CheckConstraint("saldo >= 0", name="saldo_no_negativo"),
        CheckConstraint("saldo <= monto_total", name="saldo_no_excede_total"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ventas.id", ondelete="RESTRICT"), unique=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id", ondelete="RESTRICT"), index=True)
    monto_total: Mapped[Decimal] = mapped_column(Dinero)
    saldo: Mapped[Decimal] = mapped_column(Dinero)
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date, index=True)
    estado: Mapped[EstadoCuenta] = mapped_column(
        EnumTexto(EstadoCuenta), default=EstadoCuenta.PENDIENTE, server_default=EstadoCuenta.PENDIENTE.value, index=True
    )

    cliente: Mapped[Cliente] = relationship(lazy="joined")
    abonos: Mapped[list[Abono]] = relationship(back_populates="cuenta")


class Abono(Base):
    __tablename__ = "abonos"
    __table_args__ = (CheckConstraint("monto > 0", name="monto_positivo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cuenta_por_cobrar_id: Mapped[int] = mapped_column(
        ForeignKey("cuentas_por_cobrar.id", ondelete="RESTRICT"), index=True
    )
    monto: Mapped[Decimal] = mapped_column(Dinero)
    metodo: Mapped[MetodoPago] = mapped_column(EnumTexto(MetodoPago))
    referencia: Mapped[str | None] = mapped_column(String(100))
    # El abono en efectivo entra a la caja abierta del cajero
    sesion_caja_id: Mapped[int | None] = mapped_column(ForeignKey("sesiones_caja.id", ondelete="RESTRICT"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    fecha: Mapped[datetime] = mapped_column(FechaHora(), server_default=func.now(), index=True)

    cuenta: Mapped[CuentaPorCobrar] = relationship(back_populates="abonos")
