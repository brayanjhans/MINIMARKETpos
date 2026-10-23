from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, false, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.permiso import rol_permisos

if TYPE_CHECKING:
    from app.models.permiso import Permiso
    from app.models.usuario import Usuario


class Rol(TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(200))
    # Los roles del sistema no se pueden eliminar ni renombrar
    es_sistema: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    permisos: Mapped[list[Permiso]] = relationship(
        secondary=rol_permisos, back_populates="roles", lazy="selectin"
    )
    usuarios: Mapped[list[Usuario]] = relationship(back_populates="rol")
