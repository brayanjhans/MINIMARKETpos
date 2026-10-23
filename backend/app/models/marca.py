from sqlalchemy import Boolean, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class Marca(TimestampMixin, Base):
    __tablename__ = "marcas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
