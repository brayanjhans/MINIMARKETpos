from datetime import datetime
from typing import Any

from app.schemas.base import EsquemaSalida


class PersonaARevisar(EsquemaSalida):
    usuario_id: int
    nombre: str
    intentos_fallidos: int


class ResumenAuditoria(EsquemaSalida):
    total: int
    ingresos: int
    fallos: int
    cambios: int
    revisar: PersonaARevisar | None


class AuditoriaItem(EsquemaSalida):
    id: int
    usuario_id: int | None
    usuario_nombre: str | None = None
    sucursal_id: int | None
    accion: str
    modulo: str
    entidad: str | None
    entidad_id: str | None
    descripcion: str | None
    datos: dict[str, Any] | None
    ip: str | None
    creado_en: datetime
