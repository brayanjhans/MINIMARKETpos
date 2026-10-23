from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Computed, ForeignKey, Integer, String, Table, UniqueConstraint, false, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.usuario import Usuario

# Sucursales a las que tiene acceso cada usuario
usuario_sucursales = Table(
    "usuario_sucursales",
    Base.metadata,
    Column("usuario_id", ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
    Column("sucursal_id", ForeignKey("sucursales.id", ondelete="CASCADE"), primary_key=True),
)


class Sucursal(TimestampMixin, Base):
    """Local / establecimiento del negocio (todas pertenecen a la misma empresa/RUC)."""

    __tablename__ = "sucursales"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(10), unique=True)  # código de establecimiento SUNAT, ej. 0000
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    direccion: Mapped[str | None] = mapped_column(String(250))
    telefono: Mapped[str | None] = mapped_column(String(20))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    almacenes: Mapped[list[Almacen]] = relationship(back_populates="sucursal")
    usuarios: Mapped[list[Usuario]] = relationship(secondary=usuario_sucursales, back_populates="sucursales")


class Almacen(TimestampMixin, Base):
    """Almacén físico de una sucursal. El almacén de venta es del que descuenta el POS."""

    __tablename__ = "almacenes"
    __table_args__ = (UniqueConstraint("sucursal_id", "nombre"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id", ondelete="RESTRICT"), index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    es_almacen_venta: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    # Un solo almacén de venta por sucursal (NULL cuando no lo es)
    sucursal_venta_id: Mapped[int | None] = mapped_column(
        Integer, Computed("CASE WHEN es_almacen_venta THEN sucursal_id END", persisted=True), unique=True
    )

    sucursal: Mapped[Sucursal] = relationship(back_populates="almacenes", lazy="joined")
