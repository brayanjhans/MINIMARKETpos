from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.rol import Rol

rol_permisos = Table(
    "rol_permisos",
    Base.metadata,
    Column("rol_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permiso_id", ForeignKey("permisos.id", ondelete="CASCADE"), primary_key=True),
)


class Permiso(Base):
    __tablename__ = "permisos"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(80), unique=True)  # ej. "productos.crear"
    modulo: Mapped[str] = mapped_column(String(40), index=True)
    accion: Mapped[str] = mapped_column(String(40))
    descripcion: Mapped[str] = mapped_column(String(200))

    roles: Mapped[list[Rol]] = relationship(secondary=rol_permisos, back_populates="permisos")
