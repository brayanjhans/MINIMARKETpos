from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Index, String, false, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Cantidad, CostoUnitario, EnumTexto, FechaHora, TimestampMixin
from app.models.enums import EstadoDocumento, TipoMotivoAjuste

if TYPE_CHECKING:
    from app.models.lote import Lote
    from app.models.producto import Producto
    from app.models.sucursal import Almacen


class MotivoAjuste(TimestampMixin, Base):
    """Catálogo de motivos: vencido, roto, robo, consumo interno, sobrante, etc."""

    __tablename__ = "motivos_ajuste"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    tipo: Mapped[TipoMotivoAjuste] = mapped_column(EnumTexto(TipoMotivoAjuste))
    # Las mermas se reportan como pérdida en el reporte de ganancias
    es_merma: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())


class AjusteInventario(TimestampMixin, Base):
    """Documento de ajuste de stock: BORRADOR -> PENDIENTE_APROBACION -> APLICADO / RECHAZADO (o ANULADO).

    El stock solo cambia al aprobarlo, y quien lo crea no puede aprobarlo.
    """

    __tablename__ = "ajustes_inventario"
    __table_args__ = (Index("ix_ajustes_inventario_almacen_estado", "almacen_id", "estado"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True)  # AJ-000001
    almacen_id: Mapped[int] = mapped_column(ForeignKey("almacenes.id", ondelete="RESTRICT"))
    motivo_id: Mapped[int] = mapped_column(ForeignKey("motivos_ajuste.id", ondelete="RESTRICT"))
    estado: Mapped[EstadoDocumento] = mapped_column(
        EnumTexto(EstadoDocumento), default=EstadoDocumento.BORRADOR, server_default=EstadoDocumento.BORRADOR.value
    )
    observaciones: Mapped[str | None] = mapped_column(String(300))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    aprobado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    motivo_rechazo: Mapped[str | None] = mapped_column(String(300))
    fecha_envio: Mapped[datetime | None] = mapped_column(FechaHora())
    fecha_aplicacion: Mapped[datetime | None] = mapped_column(FechaHora(), index=True)

    almacen: Mapped[Almacen] = relationship(lazy="joined")
    motivo: Mapped[MotivoAjuste] = relationship(lazy="joined")
    detalles: Mapped[list[DetalleAjusteInventario]] = relationship(
        back_populates="ajuste", cascade="all, delete-orphan", order_by="DetalleAjusteInventario.id"
    )


class DetalleAjusteInventario(Base):
    __tablename__ = "detalles_ajuste_inventario"
    __table_args__ = (CheckConstraint("cantidad <> 0", name="cantidad_no_cero"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ajuste_id: Mapped[int] = mapped_column(ForeignKey("ajustes_inventario.id", ondelete="CASCADE"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="RESTRICT"), index=True)
    lote_id: Mapped[int | None] = mapped_column(ForeignKey("lotes.id", ondelete="RESTRICT"))
    cantidad: Mapped[Decimal] = mapped_column(Cantidad)  # positivo = entrada, negativo = salida
    costo_unitario: Mapped[Decimal] = mapped_column(CostoUnitario)  # para valorizar la merma
    # Entrada de un producto con lotes: lote nuevo (o existente con ese número) donde se guarda
    numero_lote: Mapped[str | None] = mapped_column(String(50))
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date)

    ajuste: Mapped[AjusteInventario] = relationship(back_populates="detalles")
    producto: Mapped[Producto] = relationship(lazy="joined")
    lote: Mapped[Lote | None] = relationship(lazy="joined")
