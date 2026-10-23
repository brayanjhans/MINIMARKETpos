from typing import Annotated, Literal

from pydantic import Field

from app.schemas.base import EsquemaEntrada, EsquemaSalida
from app.schemas.roles import RolResumen
from app.schemas.sucursales import SucursalResumen
from app.schemas.usuarios import Password


class LoginEntrada(EsquemaEntrada):
    username: Annotated[str, Field(min_length=1, max_length=50)]
    password: Annotated[str, Field(min_length=1, max_length=128)]
    sucursal_id: int | None = None


class CambiarSucursalEntrada(EsquemaEntrada):
    sucursal_id: int


class CambiarPasswordEntrada(EsquemaEntrada):
    password_actual: Annotated[str, Field(min_length=1, max_length=128)]
    password_nueva: Password


class UsuarioSesion(EsquemaSalida):
    """Datos del usuario autenticado que necesita el frontend para armar la interfaz."""

    id: int
    nombre_completo: str
    username: str
    email: str | None
    rol: RolResumen
    permisos: list[str]
    sucursales: list[SucursalResumen]
    sucursal_actual: SucursalResumen
    debe_cambiar_password: bool


class TokenRespuesta(EsquemaSalida):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expira_en: int = Field(description="Segundos de validez del access token")
    usuario: UsuarioSesion
