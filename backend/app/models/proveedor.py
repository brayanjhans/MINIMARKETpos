from sqlalchemy import Boolean, Index, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class Proveedor(TimestampMixin, Base):
    __tablename__ = "proveedores"
    __table_args__ = (
        Index(
            "ftx_proveedores_razon_social", "razon_social", mysql_prefix="FULLTEXT", mysql_with_parser="ngram"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ruc: Mapped[str] = mapped_column(String(11), unique=True)
    razon_social: Mapped[str] = mapped_column(String(200))
    nombre_comercial: Mapped[str | None] = mapped_column(String(200))
    direccion: Mapped[str | None] = mapped_column(String(250))
    telefono: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(150))
    contacto: Mapped[str | None] = mapped_column(String(150))
    dias_credito: Mapped[int] = mapped_column(default=0, server_default="0")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
