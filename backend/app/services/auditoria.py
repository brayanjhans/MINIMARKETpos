from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Auditoria, Usuario
from app.utils.paginacion import ParametrosPaginacion, aplicar_orden, paginar
from app.utils.zona_horaria import a_utc


def registrar(
    session: AsyncSession,
    *,
    accion: str,
    modulo: str,
    usuario_id: int | None = None,
    sucursal_id: int | None = None,
    entidad: str | None = None,
    entidad_id: int | str | None = None,
    descripcion: str | None = None,
    datos: dict[str, Any] | None = None,
    ip: str | None = None,
) -> None:
    """Agrega un registro de auditoría a la transacción actual (se guarda junto con la operación)."""
    session.add(
        Auditoria(
            usuario_id=usuario_id,
            sucursal_id=sucursal_id,
            accion=accion,
            modulo=modulo,
            entidad=entidad,
            entidad_id=str(entidad_id) if entidad_id is not None else None,
            descripcion=descripcion[:300] if descripcion else None,
            datos=datos,
            ip=ip,
        )
    )


ACCIONES_INGRESO = {"LOGIN"}
ACCIONES_FALLO = {"LOGIN_FALLIDO", "SESION_REVOCADA"}
ACCIONES_SESION = {"LOGOUT", "CAMBIAR_SUCURSAL"}  # rutina: no cuentan como cambios de administración


def _rango(consulta, desde: date | None, hasta: date | None):
    # Las fechas del filtro son días locales (Lima); se convierten a rango UTC
    if desde:
        consulta = consulta.where(Auditoria.creado_en >= a_utc(datetime.combine(desde, time.min)))
    if hasta:
        consulta = consulta.where(Auditoria.creado_en < a_utc(datetime.combine(hasta + timedelta(days=1), time.min)))
    return consulta


async def resumen(session: AsyncSession, desde: date | None, hasta: date | None) -> dict[str, Any]:
    """Conteos del periodo por tipo de evento y la persona con más ingresos fallidos."""
    por_accion = dict(
        (await session.execute(_rango(select(Auditoria.accion, func.count()), desde, hasta).group_by(Auditoria.accion)))
        .tuples()
        .all()
    )
    total = sum(por_accion.values())
    ingresos = sum(por_accion.get(a, 0) for a in ACCIONES_INGRESO)
    fallos = sum(por_accion.get(a, 0) for a in ACCIONES_FALLO)
    rutina = sum(por_accion.get(a, 0) for a in ACCIONES_SESION)

    consulta_top = (
        select(Usuario.id, Usuario.nombre_completo, func.count().label("n"))
        .select_from(Auditoria)
        .join(Usuario, Usuario.id == Auditoria.usuario_id)
        .where(Auditoria.accion == "LOGIN_FALLIDO")
        .group_by(Usuario.id, Usuario.nombre_completo)
        .order_by(func.count().desc())
        .limit(1)
    )
    top = (await session.execute(_rango(consulta_top, desde, hasta))).first()
    return {
        "total": total,
        "ingresos": ingresos,
        "fallos": fallos,
        "cambios": total - ingresos - fallos - rutina,
        "revisar": {"usuario_id": top[0], "nombre": top[1], "intentos_fallidos": top[2]} if top else None,
    }


async def listar(
    session: AsyncSession,
    params: ParametrosPaginacion,
    *,
    usuario_id: int | None = None,
    sucursal_id: int | None = None,
    modulo: str | None = None,
    accion: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    orden: str | None = None,
) -> tuple[list[tuple[Auditoria, str | None]], int]:
    consulta = select(Auditoria, Usuario.nombre_completo).outerjoin(Usuario, Usuario.id == Auditoria.usuario_id)
    if usuario_id:
        consulta = consulta.where(Auditoria.usuario_id == usuario_id)
    if sucursal_id:
        consulta = consulta.where(Auditoria.sucursal_id == sucursal_id)
    if modulo:
        consulta = consulta.where(Auditoria.modulo == modulo)
    if accion:
        consulta = consulta.where(Auditoria.accion == accion)
    consulta = _rango(consulta, desde, hasta)
    columnas = {"fecha": Auditoria.creado_en, "modulo": Auditoria.modulo, "accion": Auditoria.accion}
    consulta = aplicar_orden(consulta, orden, columnas, "-fecha")
    filas, total = await paginar(session, consulta, params, escalares=False)
    return [(fila[0], fila[1]) for fila in filas], total
