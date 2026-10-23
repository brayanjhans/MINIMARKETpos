from datetime import datetime
from typing import Annotated

from pydantic import Field

from app.schemas.base import EsquemaEntrada, EsquemaSalida

NombreRol = Annotated[str, Field(min_length=3, max_length=50)]


class RolResumen(EsquemaSalida):
    id: int
    nombre: str


class RolListado(EsquemaSalida):
    id: int
    nombre: str
    descripcion: str | None
    es_sistema: bool
    activo: bool
    total_usuarios: int = 0
    total_permisos: int = 0


class RolDetalle(EsquemaSalida):
    id: int
    nombre: str
    descripcion: str | None
    es_sistema: bool
    activo: bool
    permisos: list[str]
    creado_en: datetime


class RolCrear(EsquemaEntrada):
    nombre: NombreRol
    descripcion: Annotated[str | None, Field(max_length=200)] = None
    permisos: list[str] = Field(default_factory=list, description="Códigos de permiso, ej. productos.crear")


class RolActualizar(EsquemaEntrada):
    nombre: NombreRol | None = None
    descripcion: Annotated[str | None, Field(max_length=200)] = None
    activo: bool | None = None
    permisos: list[str] | None = None


class PermisoItem(EsquemaSalida):
    codigo: str
    accion: str
    descripcion: str


class ModuloPermisos(EsquemaSalida):
    modulo: str
    etiqueta: str
    permisos: list[PermisoItem]
