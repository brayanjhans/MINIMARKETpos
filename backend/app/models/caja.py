from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Dinero, EnumTexto, FechaHora, TimestampMixin
from app.models.enums import EstadoSesionCaja, MetodoPago, TipoDenominacion

if TYPE_CHECKING:
    from app.models.movimiento_caja import MovimientoCaja
    from app.models.sucursal import Sucursal
    from app.models.usuario import Usuario


class Caja(TimestampMixin, Base):
    """Caja física / terminal de venta de una sucursal (ej. "Caja 1")."""

    __tablename__ = "cajas"
    __table_args__ = (UniqueConstraint("sucursal_id", "nombre"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id", ondelete="RESTRICT"), index=True)
    nombre: Mapped[str] = mapped_column(String(50))
    descripcion: Mapped[str | None] = mapped_column(String(200))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    sucursal: Mapped[Sucursal] = relationship(lazy="joined")
    sesiones: Mapped[list[SesionCaja]] = relationship(back_populates="caja")


class SesionCaja(TimestampMixin, Base):
    """Turno de caja: apertura con monto inicial y cierre con arqueo."""

    __tablename__ = "sesiones_caja"
    __table_args__ = (
        CheckConstraint("monto_inicial >= 0", name="monto_inicial_no_negativo"),
        CheckConstraint("monto_contado IS NULL OR monto_contado >= 0", name="monto_contado_no_negativo"),
        Index("ix_sesiones_caja_usuario_apertura", "usuario_id", "fecha_apertura"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    caja_id: Mapped[int] = mapped_column(ForeignKey("cajas.id", ondelete="RESTRICT"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    estado: Mapped[EstadoSesionCaja] = mapped_column(
        EnumTexto(EstadoSesionCaja),
        default=EstadoSesionCaja.ABIERTA,
        server_default=EstadoSesionCaja.ABIERTA.value,
        index=True,
    )
    monto_inicial: Mapped[Decimal] = mapped_column(Dinero)
    fecha_apertura: Mapped[datetime] = mapped_column(FechaHora(), server_default=func.now(), index=True)
    fecha_cierre: Mapped[datetime | None] = mapped_column(FechaHora(), index=True)
    # Arqueo de efectivo: esperado = inicial + ventas efectivo + abonos efectivo + ingresos - egresos - reembolsos
    monto_esperado: Mapped[Decimal | None] = mapped_column(Dinero)
    monto_contado: Mapped[Decimal | None] = mapped_column(Dinero)
    diferencia: Mapped[Decimal | None] = mapped_column(Dinero)
    observaciones_apertura: Mapped[str | None] = mapped_column(String(300))
    observaciones_cierre: Mapped[str | None] = mapped_column(String(300))

    # Columnas generadas con índice único: valen NULL cuando la sesión está cerrada (MySQL
    # permite varios NULL), así la BD garantiza una sola caja abierta por cajero y por caja.
    usuario_abierta_id: Mapped[int | None] = mapped_column(
        Integer, Computed("CASE WHEN estado = 'ABIERTA' THEN usuario_id END", persisted=True), unique=True
    )
    caja_abierta_id: Mapped[int | None] = mapped_column(
        Integer, Computed("CASE WHEN estado = 'ABIERTA' THEN caja_id END", persisted=True), unique=True
    )

    caja: Mapped[Caja] = relationship(back_populates="sesiones", lazy="joined")
    usuario: Mapped[Usuario] = relationship(lazy="joined")
    movimientos: Mapped[list[MovimientoCaja]] = relationship(back_populates="sesion")
    arqueo: Mapped[list[ArqueoDenominacion]] = relationship(back_populates="sesion", cascade="all, delete-orphan")
    resumen_cierre: Mapped[list[ResumenCierreCaja]] = relationship(
        back_populates="sesion", cascade="all, delete-orphan"
    )


class ArqueoDenominacion(Base):
    """Conteo del efectivo al cierre, billete por billete y moneda por moneda."""

    __tablename__ = "arqueos_denominacion"
    __table_args__ = (
        UniqueConstraint("sesion_caja_id", "denominacion"),
        CheckConstraint("denominacion > 0", name="denominacion_positiva"),
        CheckConstraint("cantidad >= 0", name="cantidad_no_negativa"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sesion_caja_id: Mapped[int] = mapped_column(ForeignKey("sesiones_caja.id", ondelete="CASCADE"))
    tipo: Mapped[TipoDenominacion] = mapped_column(EnumTexto(TipoDenominacion))
    denominacion: Mapped[Decimal] = mapped_column(Dinero)  # 200.00, 100.00 ... 0.10
    cantidad: Mapped[int] = mapped_column(Integer)
    subtotal: Mapped[Decimal] = mapped_column(Dinero)

    sesion: Mapped[SesionCaja] = relationship(back_populates="arqueo")


class ResumenCierreCaja(Base):
    """Totales del turno por método de pago (efectivo, tarjeta, Yape, Plin...) calculados al cerrar."""

    __tablename__ = "resumen_cierre_caja"
    __table_args__ = (UniqueConstraint("sesion_caja_id", "metodo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sesion_caja_id: Mapped[int] = mapped_column(ForeignKey("sesiones_caja.id", ondelete="CASCADE"))
    metodo: Mapped[MetodoPago] = mapped_column(EnumTexto(MetodoPago))
    cantidad_operaciones: Mapped[int] = mapped_column(Integer)
    monto_sistema: Mapped[Decimal] = mapped_column(Dinero)  # lo que registró el sistema
    monto_declarado: Mapped[Decimal | None] = mapped_column(Dinero)  # lo que declara el cajero (vouchers, app)
    diferencia: Mapped[Decimal | None] = mapped_column(Dinero)

    sesion: Mapped[SesionCaja] = relationship(back_populates="resumen_cierre")
