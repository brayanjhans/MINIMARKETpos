from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.core.config import settings

ZONA_LOCAL = ZoneInfo(settings.ZONA_HORARIA)


def ahora_utc() -> datetime:
    return datetime.now(UTC)


def a_utc(fecha: datetime) -> datetime:
    """Convierte una fecha/hora local del negocio (sin zona) a UTC."""
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=ZONA_LOCAL)
    return fecha.astimezone(UTC)


def inicio_de_hoy_utc() -> datetime:
    """Medianoche de hoy en la hora del negocio (Lima), expresada en UTC."""
    local = datetime.now(ZONA_LOCAL).replace(hour=0, minute=0, second=0, microsecond=0)
    return local.astimezone(UTC)


def a_local(fecha: datetime) -> datetime:
    return fecha.astimezone(ZONA_LOCAL)
