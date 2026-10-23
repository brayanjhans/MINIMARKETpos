from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import FechaHora


class Auditoria(Base):
    __tablename__ = "auditoria"
    __table_args__ = (Index("ix_auditoria_modulo_fecha", "modulo", "creado_en"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    sucursal_id: Mapped[int | None] = mapped_column(ForeignKey("sucursales.id", ondelete="SET NULL"))
    accion: Mapped[str] = mapped_column(String(50))  # CREAR, EDITAR, ELIMINAR, LOGIN, ANULAR...
    modulo: Mapped[str] = mapped_column(String(40))
    entidad: Mapped[str | None] = mapped_column(String(60))
    entidad_id: Mapped[str | None] = mapped_column(String(40))
    descripcion: Mapped[str | None] = mapped_column(String(300))
    datos: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    ip: Mapped[str | None] = mapped_column(String(45))
    creado_en: Mapped[datetime] = mapped_column(
        FechaHora(), server_default=func.now(), index=True
    )
