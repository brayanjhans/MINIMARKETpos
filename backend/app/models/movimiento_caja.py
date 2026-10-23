from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Dinero, EnumTexto, FechaHora
from app.models.enums import TipoMovimientoCaja

if TYPE_CHECKING:
    from app.models.caja import SesionCaja


class MovimientoCaja(Base):
    """Ingresos y egresos manuales de efectivo (pago a proveedor, retiro, sencillo, etc.)."""

    __tablename__ = "movimientos_caja"
    __table_args__ = (CheckConstraint("monto > 0", name="monto_positivo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sesion_caja_id: Mapped[int] = mapped_column(
        ForeignKey("sesiones_caja.id", ondelete="RESTRICT"), index=True
    )
    tipo: Mapped[TipoMovimientoCaja] = mapped_column(EnumTexto(TipoMovimientoCaja))
    monto: Mapped[Decimal] = mapped_column(Dinero)
    concepto: Mapped[str] = mapped_column(String(200))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    creado_en: Mapped[datetime] = mapped_column(
        FechaHora(), server_default=func.now(), index=True
    )

    sesion: Mapped[SesionCaja] = relationship(back_populates="movimientos")
