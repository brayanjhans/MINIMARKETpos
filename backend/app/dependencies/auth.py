from dataclasses import dataclass, field
from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.excepciones import NoAutenticado, PermisoDenegado
from app.core.security import decodificar_token
from app.models import Rol, Usuario

_bearer = HTTPBearer(auto_error=False, description="Access token JWT")

DB = Annotated[AsyncSession, Depends(get_db)]


@dataclass(slots=True)
class ContextoUsuario:
    """Quién hace la petición, en qué sucursal trabaja y qué puede hacer."""

    usuario: Usuario
    sucursal_id: int
    permisos: frozenset[str]
    ip: str | None = None
    user_agent: str | None = field(default=None, repr=False)

    @property
    def usuario_id(self) -> int:
        return self.usuario.id

    def tiene(self, permiso: str) -> bool:
        return permiso in self.permisos

    def exigir(self, permiso: str) -> None:
        if permiso not in self.permisos:
            raise PermisoDenegado("No tiene permiso para realizar esta acción", datos={"permiso": permiso})


def ip_cliente(request: Request) -> str | None:
    return request.client.host if request.client else None


async def cargar_usuario(session: AsyncSession, usuario_id: int) -> Usuario | None:
    consulta = (
        select(Usuario)
        .where(Usuario.id == usuario_id)
        .options(selectinload(Usuario.rol).selectinload(Rol.permisos), selectinload(Usuario.sucursales))
    )
    return await session.scalar(consulta)


def _no_autenticado(mensaje: str = "Sesión inválida o expirada. Inicie sesión nuevamente.") -> NoAutenticado:
    return NoAutenticado(mensaje, codigo="token_invalido")


async def get_contexto(
    request: Request,
    session: DB,
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> ContextoUsuario:
    if credenciales is None or credenciales.scheme.lower() != "bearer":
        raise NoAutenticado("Debe iniciar sesión", codigo="sin_token")
    try:
        payload = decodificar_token(credenciales.credentials, "access")
        usuario_id = int(payload["sub"])
        sucursal_id = int(payload["suc"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise _no_autenticado() from exc

    usuario = await cargar_usuario(session, usuario_id)
    if usuario is None or not usuario.activo or not usuario.rol.activo:
        raise _no_autenticado("Su usuario está inactivo. Contacte al administrador.")
    # Tokens emitidos antes de un cambio de contraseña dejan de ser válidos
    if usuario.password_actualizado_en and payload["iat"] < int(usuario.password_actualizado_en.timestamp()):
        raise _no_autenticado()
    if sucursal_id not in {s.id for s in usuario.sucursales if s.activo}:
        raise _no_autenticado("Ya no tiene acceso a esta sucursal. Inicie sesión nuevamente.")

    return ContextoUsuario(
        usuario=usuario,
        sucursal_id=sucursal_id,
        permisos=frozenset(p.codigo for p in usuario.rol.permisos),
        ip=ip_cliente(request),
        user_agent=request.headers.get("user-agent"),
    )


Contexto = Annotated[ContextoUsuario, Depends(get_contexto)]
