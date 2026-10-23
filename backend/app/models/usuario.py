from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, false, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import FechaHora, TimestampMixin
from app.models.sucursal import usuario_sucursales

if TYPE_CHECKING:
    from app.models.rol import Rol
    from app.models.sucursal import Sucursal


class Usuario(TimestampMixin, Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre_completo: Mapped[str] = mapped_column(String(150))
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str | None] = mapped_column(String(150), unique=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), index=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    ultimo_acceso: Mapped[datetime | None] = mapped_column(FechaHora())
    # Seguridad del login: bloqueo temporal tras varios intentos fallidos
    intentos_fallidos: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(FechaHora())
    debe_cambiar_password: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    password_actualizado_en: Mapped[datetime | None] = mapped_column(FechaHora())
    # Sucursal con la que inicia sesión por defecto (debe estar entre sus sucursales permitidas)
    sucursal_predeterminada_id: Mapped[int | None] = mapped_column(
        ForeignKey("sucursales.id", ondelete="SET NULL")
    )

    rol: Mapped[Rol] = relationship(back_populates="usuarios", lazy="joined")
    sucursales: Mapped[list[Sucursal]] = relationship(
        secondary=usuario_sucursales, back_populates="usuarios", lazy="selectin"
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    """Sesiones activas. Se guarda el hash del jti para poder revocar tokens.

    Cada uso rota el token (se revoca y se emite uno nuevo). Si se reutiliza un token ya rotado
    fuera del periodo de gracia, se asume robo y se revocan todas las sesiones del usuario.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    # Sucursal con la que está trabajando esta sesión
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id", ondelete="CASCADE"))
    jti_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expira_en: Mapped[datetime] = mapped_column(FechaHora(), index=True)
    revocado: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    revocado_en: Mapped[datetime | None] = mapped_column(FechaHora())
    motivo_revocacion: Mapped[str | None] = mapped_column(String(20))  # ROTACION, LOGOUT, ROBO, ADMIN...
    ip: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(300))
    creado_en: Mapped[datetime] = mapped_column(FechaHora(), server_default=func.now())

    usuario: Mapped[Usuario] = relationship(back_populates="refresh_tokens")
