from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.producto import Producto


class Categoria(TimestampMixin, Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(250))
    color: Mapped[str | None] = mapped_column(String(7))  # hex para la interfaz, ej. #22c55e
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    productos: Mapped[list[Producto]] = relationship(back_populates="categoria")
