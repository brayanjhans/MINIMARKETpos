from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Cantidad, EnumTexto, FechaHora, TimestampMixin
from app.models.enums import EstadoInventarioFisico


class InventarioFisico(TimestampMixin, Base):
    """Toma de inventario de un almacén: se cuenta el stock real y al aplicarlo se generan ajustes en el kardex."""

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
    fecha_aplicacion: Mapped[datetime | None] = mapped_column(FechaHora())

    detalles: Mapped[list[DetalleInventarioFisico]] = relationship(
        back_populates="inventario", cascade="all, delete-orphan"
    )


class DetalleInventarioFisico(Base):
    __tablename__ = "detalles_inventario_fisico"
    __table_args__ = (UniqueConstraint("inventario_id", "producto_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    inventario_id: Mapped[int] = mapped_column(
        ForeignKey("inventarios_fisicos.id", ondelete="CASCADE"), index=True
    )
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="RESTRICT"))
    stock_sistema: Mapped[Decimal] = mapped_column(Cantidad)
    stock_contado: Mapped[Decimal | None] = mapped_column(Cantidad)
    diferencia: Mapped[Decimal | None] = mapped_column(Cantidad)

    inventario: Mapped[InventarioFisico] = relationship(back_populates="detalles")
