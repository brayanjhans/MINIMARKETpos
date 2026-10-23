from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Computed, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Cantidad, EnumTexto, FechaHora, TimestampMixin
from app.models.enums import EstadoInventarioFisico

if TYPE_CHECKING:
    from app.models.lote import Lote
    from app.models.producto import Producto
    from app.models.sucursal import Almacen


class InventarioFisico(TimestampMixin, Base):
    """Toma de inventario de un almacén.

    Al crearla se guarda el stock del sistema de cada producto (o lote). Al aprobarla se aplica SOLO la
    diferencia (contado - stock al contar) sobre el stock actual: las ventas hechas durante el conteo se respetan.
    """

    __tablename__ = "inventarios_fisicos"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True)  # IF-000001
    almacen_id: Mapped[int] = mapped_column(ForeignKey("almacenes.id", ondelete="RESTRICT"), index=True)
    descripcion: Mapped[str | None] = mapped_column(String(200))
    estado: Mapped[EstadoInventarioFisico] = mapped_column(
        EnumTexto(EstadoInventarioFisico),
        default=EstadoInventarioFisico.EN_PROCESO,
        server_default=EstadoInventarioFisico.EN_PROCESO.value,
        index=True,
    )
    # Si se indica, el conteo se limita a una categoría
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias.id", ondelete="SET NULL"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    aprobado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    motivo_rechazo: Mapped[str | None] = mapped_column(String(300))
    fecha_envio: Mapped[datetime | None] = mapped_column(FechaHora())
    fecha_aplicacion: Mapped[datetime | None] = mapped_column(FechaHora())

    almacen: Mapped[Almacen] = relationship(lazy="joined")
    detalles: Mapped[list[DetalleInventarioFisico]] = relationship(
        back_populates="inventario", cascade="all, delete-orphan", order_by="DetalleInventarioFisico.id"
    )


class DetalleInventarioFisico(Base):
    """Una línea por producto, o por lote si el producto maneja lotes."""

    __tablename__ = "detalles_inventario_fisico"
    __table_args__ = (UniqueConstraint("inventario_id", "producto_id", "lote_clave"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    inventario_id: Mapped[int] = mapped_column(
        ForeignKey("inventarios_fisicos.id", ondelete="CASCADE"), index=True
    )
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="RESTRICT"), index=True)
    lote_id: Mapped[int | None] = mapped_column(ForeignKey("lotes.id", ondelete="RESTRICT"))
    # UNIQUE con NULL no impide duplicados en MySQL: se usa 0 cuando no hay lote
    lote_clave: Mapped[int] = mapped_column(Integer, Computed("COALESCE(lote_id, 0)", persisted=True))
    stock_sistema: Mapped[Decimal] = mapped_column(Cantidad)
    stock_contado: Mapped[Decimal | None] = mapped_column(Cantidad)
    diferencia: Mapped[Decimal | None] = mapped_column(Cantidad)

    inventario: Mapped[InventarioFisico] = relationship(back_populates="detalles")
    producto: Mapped[Producto] = relationship(lazy="joined")
    lote: Mapped[Lote | None] = relationship(lazy="joined")
