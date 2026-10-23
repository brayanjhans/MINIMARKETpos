from typing import Any

from sqlalchemy import JSON, Boolean, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import EnumTexto, TimestampMixin
from app.models.enums import TipoParametro


class ParametroSistema(TimestampMixin, Base):
    """Ajustes del negocio modificables sin tocar código (clave/valor)."""

    __tablename__ = "parametros_sistema"

    clave: Mapped[str] = mapped_column(String(80), primary_key=True)
    valor: Mapped[Any] = mapped_column(JSON)
    tipo: Mapped[TipoParametro] = mapped_column(EnumTexto(TipoParametro))
    modulo: Mapped[str] = mapped_column(String(40), index=True)
    descripcion: Mapped[str] = mapped_column(String(250))
    editable: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
