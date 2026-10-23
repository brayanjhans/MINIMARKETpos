import re
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, EmailStr, Field

from app.schemas.base import EsquemaEntrada, EsquemaSalida
from app.schemas.roles import RolResumen
from app.schemas.sucursales import SucursalResumen

_PATRON_USERNAME = re.compile(r"^[a-z0-9._-]{3,50}$")


def validar_password(valor: str) -> str:
    if len(valor) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if len(valor.encode("utf-8")) > 72:
        raise ValueError("La contraseña es demasiado larga")
    if not re.search(r"[A-Za-z]", valor) or not re.search(r"\d", valor):
        raise ValueError("La contraseña debe contener letras y números")
    return valor


def normalizar_username(valor: str) -> str:
    valor = valor.strip().lower()
    if not _PATRON_USERNAME.match(valor):
        raise ValueError("El usuario solo puede tener letras minúsculas, números, punto, guion y guion bajo (3 a 50)")
    return valor


Password = Annotated[str, AfterValidator(validar_password)]
Username = Annotated[str, AfterValidator(normalizar_username)]
NombreCompleto = Annotated[str, Field(min_length=3, max_length=150)]


class UsuarioListado(EsquemaSalida):
    id: int
    nombre_completo: str
    username: str
    email: str | None
    rol: RolResumen
    activo: bool
    bloqueado_hasta: datetime | None
    ultimo_acceso: datetime | None
    sucursales: list[SucursalResumen]
    creado_en: datetime


class UsuarioDetalle(UsuarioListado):
    sucursal_predeterminada_id: int | None
    debe_cambiar_password: bool
    intentos_fallidos: int


class UsuarioCrear(EsquemaEntrada):
    nombre_completo: NombreCompleto
    username: Username
    email: EmailStr | None = None
    password: Password
    rol_id: int
    sucursal_ids: list[int] = Field(min_length=1, description="Sucursales donde puede trabajar")
    sucursal_predeterminada_id: int | None = None
    debe_cambiar_password: bool = True


class UsuarioActualizar(EsquemaEntrada):
    nombre_completo: NombreCompleto | None = None
    email: EmailStr | None = None
    rol_id: int | None = None
    activo: bool | None = None
    sucursal_ids: list[int] | None = Field(default=None, min_length=1)
    sucursal_predeterminada_id: int | None = None


class ResumenUsuarios(EsquemaSalida):
    con_acceso: int
    sin_acceso: int
    bloqueados: int
    ingresaron_hoy: int


class RestablecerPassword(EsquemaEntrada):
    password: Password
    debe_cambiar_password: bool = True
