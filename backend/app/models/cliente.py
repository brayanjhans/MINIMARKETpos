from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Index, String, UniqueConstraint, false, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import CERO, Dinero, EnumTexto, TimestampMixin
from app.models.enums import TipoDocumentoIdentidad


class Cliente(TimestampMixin, Base):
    __tablename__ = "clientes"
    __table_args__ = (
        UniqueConstraint("tipo_documento", "numero_documento"),
        CheckConstraint("limite_credito >= 0", name="limite_credito_no_negativo"),
        Index("ftx_clientes_nombre", "nombre", mysql_prefix="FULLTEXT", mysql_with_parser="ngram"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_documento: Mapped[TipoDocumentoIdentidad] = mapped_column(EnumTexto(TipoDocumentoIdentidad))
    numero_documento: Mapped[str | None] = mapped_column(String(15), index=True)
    nombre: Mapped[str] = mapped_column(String(200))  # nombre completo o razón social
    direccion: Mapped[str | None] = mapped_column(String(250))
    telefono: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(150))
    # Venta al fiado: solo si permite_credito; limite_credito = 0 significa sin tope
    permite_credito: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    limite_credito: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
