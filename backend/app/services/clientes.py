"""Clientes: búsqueda y alta rápida desde el POS (el módulo completo y las cobranzas llegan en la Fase 5)."""

from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import Conflicto, PermisoDenegado
from app.dependencies.auth import ContextoUsuario
from app.models import Cliente, CuentaPorCobrar
from app.models.enums import EstadoCuenta
from app.schemas.clientes import ClienteCrear
from app.services import auditoria
from app.services.productos import _escapar_like

MODULO = "clientes"


async def _deudas(session: AsyncSession, ids: list[int]) -> dict[int, Decimal]:
    if not ids:
        return {}
    filas = await session.execute(
        select(CuentaPorCobrar.cliente_id, func.sum(CuentaPorCobrar.saldo))
        .where(
            CuentaPorCobrar.cliente_id.in_(ids),
            CuentaPorCobrar.estado.in_([EstadoCuenta.PENDIENTE, EstadoCuenta.PARCIAL]),
        )
        .group_by(CuentaPorCobrar.cliente_id)
    )
    return {i: Decimal(s) for i, s in filas.tuples()}


def _salida(c: Cliente, deuda: Decimal) -> dict[str, Any]:
    return {
        "id": c.id,
        "tipo_documento": c.tipo_documento,
        "numero_documento": c.numero_documento,
        "nombre": c.nombre,
        "telefono": c.telefono,
        "permite_credito": c.permite_credito,
        "limite_credito": c.limite_credito,
        "deuda": deuda,
        "activo": c.activo,
    }


async def buscar(session: AsyncSession, texto: str | None, limite: int = 15) -> list[dict[str, Any]]:
    """Por número de documento exacto o por nombre (todas las palabras, en cualquier orden)."""
    consulta = select(Cliente).where(Cliente.activo.is_(True)).order_by(Cliente.nombre).limit(limite)
    palabras = (texto or "").split()[:5]
    if palabras:
        por_nombre = and_(*[Cliente.nombre.like(f"%{_escapar_like(p)}%", escape="\\") for p in palabras])
        consulta = consulta.where(or_(Cliente.numero_documento == texto.strip().upper(), por_nombre))
    clientes = list(await session.scalars(consulta))
    deudas = await _deudas(session, [c.id for c in clientes])
    return [_salida(c, deudas.get(c.id, Decimal("0"))) for c in clientes]


async def crear(session: AsyncSession, ctx: ContextoUsuario, datos: ClienteCrear) -> dict[str, Any]:
    if (datos.permite_credito or datos.limite_credito > 0) and not ctx.tiene("clientes.editar"):
        raise PermisoDenegado("Habilitar el fiado a un cliente requiere permiso para editar clientes")
    if datos.numero_documento:
        existente = await session.scalar(
            select(Cliente).where(
                Cliente.tipo_documento == datos.tipo_documento, Cliente.numero_documento == datos.numero_documento
            )
        )
        if existente is not None:
            raise Conflicto(
                f"Ya existe el cliente {existente.nombre} con ese documento",
                codigo="cliente_duplicado",
                datos={"cliente_id": existente.id},
            )
    cliente = Cliente(**datos.model_dump())
    session.add(cliente)
    await session.flush()
    auditoria.registrar(
        session,
        accion="CREAR",
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad="cliente",
        entidad_id=cliente.id,
        descripcion=f"Creó el cliente {cliente.nombre}",
        ip=ctx.ip,
    )
    await session.commit()
    return _salida(cliente, Decimal("0"))
