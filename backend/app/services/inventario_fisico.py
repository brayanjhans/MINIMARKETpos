"""Inventario físico: EN_PROCESO -> PENDIENTE_APROBACION -> APLICADO (o CANCELADO).

- Al crearlo se guarda el stock del sistema de cada producto, o de cada lote si maneja lotes.
- Al aprobarlo se aplica SOLO la diferencia (contado - stock al contar) sobre el stock actual, así las ventas
  hechas mientras se contaba se respetan. Las líneas no contadas no cambian nada.
- Un producto no puede estar en dos conteos abiertos del mismo almacén.
- Si se rechaza, vuelve a EN_PROCESO para recontar.
"""

from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.excepciones import Conflicto, NoEncontrado, ValidacionNegocio
from app.dependencies.auth import ContextoUsuario
from app.models import (
    CodigoBarras,
    DetalleInventarioFisico,
    InventarioFisico,
    Lote,
    Producto,
    StockAlmacen,
)
from app.models.base import CERO
from app.models.enums import EstadoInventarioFisico, TipoMovimientoInventario
from app.schemas.inventario import ConteoEntrada, InventarioFisicoCrear
from app.services import auditoria, correlativos, stock, transacciones
from app.services.inventario import (
    almacen_de_trabajo,
    almacen_visible,
    exigir_aprobador,
    nombres_usuarios,
    puede_aprobar,
    redondear,
)
from app.services.productos import puede_ver_costos
from app.utils.paginacion import ParametrosPaginacion, paginar
from app.utils.zona_horaria import ahora_utc

MODULO = "inventario"
ABIERTOS = (EstadoInventarioFisico.EN_PROCESO, EstadoInventarioFisico.PENDIENTE_APROBACION)


async def _cargar(session: AsyncSession, inventario_id: int, *, bloquear: bool = False) -> InventarioFisico:
    consulta = select(InventarioFisico).where(InventarioFisico.id == inventario_id)
    if bloquear:
        consulta = consulta.with_for_update(of=InventarioFisico)
    consulta = consulta.options(selectinload(InventarioFisico.detalles)).execution_options(populate_existing=True)
    inventario = await session.scalar(consulta)
    if inventario is None:
        raise NoEncontrado("El inventario físico no existe")
    return inventario


def _auditar(session, ctx: ContextoUsuario, inv: InventarioFisico, accion: str, descripcion: str, **datos) -> None:
    auditoria.registrar(
        session,
        accion=accion,
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad="inventario_fisico",
        entidad_id=inv.id,
        descripcion=descripcion,
        datos=datos or None,
        ip=ctx.ip,
    )


async def crear(session: AsyncSession, ctx: ContextoUsuario, datos: InventarioFisicoCrear, clave: str | None) -> int:
    async def accion() -> int:
        # Bloquear el almacén serializa la creación de conteos: dos personas no abren el mismo producto a la vez
        almacen = await almacen_de_trabajo(session, ctx, datos.almacen_id, bloquear=True)
        consulta = select(Producto).where(Producto.activo.is_(True)).order_by(Producto.nombre)
        if datos.categoria_id is not None:
            consulta = consulta.where(Producto.categoria_id == datos.categoria_id)
        if datos.producto_ids:
            consulta = consulta.where(Producto.id.in_(set(datos.producto_ids)))
        productos = list(await session.scalars(consulta))
        if not productos:
            raise ValidacionNegocio("No hay productos activos para contar con ese filtro", codigo="sin_productos")
        ids = [p.id for p in productos]

        ocupados = await session.execute(
            select(DetalleInventarioFisico.producto_id, InventarioFisico.numero)
            .join(InventarioFisico, InventarioFisico.id == DetalleInventarioFisico.inventario_id)
            .where(
                InventarioFisico.almacen_id == almacen.id,
                InventarioFisico.estado.in_(ABIERTOS),
                DetalleInventarioFisico.producto_id.in_(ids),
            )
            .limit(1)
        )
        fila = ocupados.first()
        if fila:
            nombre = next(p.nombre for p in productos if p.id == fila[0])
            raise Conflicto(
                f"«{nombre}» ya está en el conteo abierto {fila[1]}. Termínelo o cancélelo antes de abrir otro.",
                codigo="conteo_abierto",
            )

        cantidades = dict(
            (
                await session.execute(
                    select(StockAlmacen.producto_id, StockAlmacen.cantidad).where(
                        StockAlmacen.almacen_id == almacen.id, StockAlmacen.producto_id.in_(ids)
                    )
                )
            )
            .tuples()
            .all()
        )
        lotes: dict[int, list[Lote]] = {}
        for lote in await session.scalars(
            select(Lote)
            .where(Lote.almacen_id == almacen.id, Lote.producto_id.in_(ids), Lote.cantidad_actual > 0)
            .order_by(Lote.fecha_vencimiento.is_(None), Lote.fecha_vencimiento, Lote.id)
        ):
            lotes.setdefault(lote.producto_id, []).append(lote)

        detalles = []
        for p in productos:
            if p.maneja_lotes:
                # Por lote. Si no tiene lotes con saldo, no se cuenta aquí (lo nuevo entra con un ajuste con lote)
                detalles.extend(
                    DetalleInventarioFisico(producto_id=p.id, lote_id=lote.id, stock_sistema=lote.cantidad_actual)
                    for lote in lotes.get(p.id, [])
                )
            else:
                detalles.append(DetalleInventarioFisico(producto_id=p.id, stock_sistema=cantidades.get(p.id, CERO)))
        if not detalles:
            raise ValidacionNegocio("No hay nada que contar con ese filtro", codigo="sin_productos")

        inv = InventarioFisico(
            numero=await correlativos.siguiente(session, "INVENTARIO_FISICO"),
            almacen_id=almacen.id,
            descripcion=datos.descripcion,
            categoria_id=datos.categoria_id,
            usuario_id=ctx.usuario_id,
            detalles=detalles,
        )
        session.add(inv)
        await session.flush()
        _auditar(session, ctx, inv, "CREAR", f"Inició el inventario físico {inv.numero} ({len(detalles)} líneas)")
        return inv.id

    return await transacciones.ejecutar(
        session, accion, usuario_id=ctx.usuario_id, operacion="crear_inventario_fisico", clave=clave
    )


async def registrar_conteo(
    session: AsyncSession, ctx: ContextoUsuario, inventario_id: int, datos: ConteoEntrada
) -> int:
    inv = await _cargar(session, inventario_id, bloquear=True)
    if inv.estado != EstadoInventarioFisico.EN_PROCESO:
        raise Conflicto("El conteo ya fue enviado a aprobación o cerrado", codigo="estado_invalido")
    await almacen_de_trabajo(session, ctx, inv.almacen_id)
    por_id = {d.id: d for d in inv.detalles}
    for item in datos.items:
        detalle = por_id.get(item.detalle_id)
        if detalle is None:
            raise ValidacionNegocio("Alguna línea no pertenece a este conteo", codigo="detalle_invalido")
        if item.stock_contado is not None:
            stock.validar_cantidad(detalle.producto, item.stock_contado)
        detalle.stock_contado = item.stock_contado
        detalle.diferencia = None if item.stock_contado is None else item.stock_contado - detalle.stock_sistema
    await session.commit()
    return inv.id


async def enviar(session: AsyncSession, ctx: ContextoUsuario, inventario_id: int) -> int:
    inv = await _cargar(session, inventario_id, bloquear=True)
    if inv.estado == EstadoInventarioFisico.PENDIENTE_APROBACION:
        return inv.id
    if inv.estado != EstadoInventarioFisico.EN_PROCESO:
        raise Conflicto("Solo se puede enviar un conteo en proceso", codigo="estado_invalido")
    if not any(d.stock_contado is not None for d in inv.detalles):
        raise ValidacionNegocio("No se ha contado ningún producto", codigo="sin_conteo")
    inv.estado = EstadoInventarioFisico.PENDIENTE_APROBACION
    inv.fecha_envio = ahora_utc()
    inv.motivo_rechazo = None
    _auditar(session, ctx, inv, "ENVIAR", f"Envió a aprobación el inventario físico {inv.numero}")
    await session.commit()
    return inv.id


async def aprobar(session: AsyncSession, ctx: ContextoUsuario, inventario_id: int) -> int:
    async def accion() -> int:
        inv = await _cargar(session, inventario_id, bloquear=True)
        if inv.estado == EstadoInventarioFisico.APLICADO:
            raise Conflicto(f"El inventario {inv.numero} ya fue aplicado", codigo="ya_aplicado")
        if inv.estado != EstadoInventarioFisico.PENDIENTE_APROBACION:
            raise Conflicto("Solo se puede aprobar un conteo pendiente de aprobación", codigo="estado_invalido")
        await exigir_aprobador(session, ctx, inv.usuario_id)
        almacen = await almacen_de_trabajo(session, ctx, inv.almacen_id)
        con_diferencia = [d for d in inv.detalles if d.diferencia is not None and d.diferencia != 0]
        bloqueo = await stock.bloquear(session, [d.producto_id for d in con_diferencia], [almacen.id])
        for d in sorted(con_diferencia, key=lambda x: (x.producto_id, x.id)):
            producto = bloqueo.productos[d.producto_id]
            lote = await stock.bloquear_lote(session, d.lote_id, d.producto_id, almacen.id) if d.lote_id else None
            costo = lote.costo_unitario if lote and lote.costo_unitario > 0 else producto.precio_costo
            try:
                stock.mover(
                    session,
                    producto=producto,
                    stock=bloqueo.stock(d.producto_id, almacen.id),
                    cantidad=d.diferencia,
                    tipo=TipoMovimientoInventario.INVENTARIO_FISICO,
                    costo_unitario=costo,
                    usuario_id=ctx.usuario_id,
                    referencia_tipo="inventario_fisico",
                    referencia_id=inv.id,
                    motivo=f"Inventario físico {inv.numero}",
                    lote=lote,
                )
            except ValidacionNegocio as exc:
                raise ValidacionNegocio(
                    f"{exc.mensaje}. Se vendió o movió mercadería durante el conteo: rechace el conteo para "
                    "recontar este producto.",
                    codigo="recontar",
                    datos={"producto_id": d.producto_id},
                ) from exc
        inv.estado = EstadoInventarioFisico.APLICADO
        inv.aprobado_por_id = ctx.usuario_id
        inv.fecha_aplicacion = ahora_utc()
        _auditar(
            session,
            ctx,
            inv,
            "APROBAR",
            f"Aprobó el inventario físico {inv.numero} ({len(con_diferencia)} diferencias)",
        )
        return inv.id

    return await transacciones.ejecutar(session, accion, usuario_id=ctx.usuario_id, operacion="aprobar_fisico")


async def rechazar(session: AsyncSession, ctx: ContextoUsuario, inventario_id: int, motivo: str) -> int:
    inv = await _cargar(session, inventario_id, bloquear=True)
    if inv.estado != EstadoInventarioFisico.PENDIENTE_APROBACION:
        raise Conflicto("Solo se puede rechazar un conteo pendiente de aprobación", codigo="estado_invalido")
    ctx.exigir("inventario.aprobar_ajustes")
    inv.estado = EstadoInventarioFisico.EN_PROCESO  # vuelve para recontar
    inv.motivo_rechazo = motivo
    _auditar(session, ctx, inv, "RECHAZAR", f"Devolvió para recontar el inventario físico {inv.numero}", motivo=motivo)
    await session.commit()
    return inv.id


async def cancelar(session: AsyncSession, ctx: ContextoUsuario, inventario_id: int) -> int:
    inv = await _cargar(session, inventario_id, bloquear=True)
    if inv.estado == EstadoInventarioFisico.CANCELADO:
        return inv.id
    if inv.estado not in ABIERTOS:
        raise Conflicto("Un inventario aplicado no se puede cancelar", codigo="estado_invalido")
    if inv.usuario_id != ctx.usuario_id and not ctx.tiene("inventario.aprobar_ajustes"):
        raise ValidacionNegocio("Solo quien lo inició o un aprobador puede cancelarlo", codigo="no_es_el_autor")
    inv.estado = EstadoInventarioFisico.CANCELADO
    _auditar(session, ctx, inv, "CANCELAR", f"Canceló el inventario físico {inv.numero}")
    await session.commit()
    return inv.id


# --- Consultas ---------------------------------------------------------------------------------------------


def _costo(d: DetalleInventarioFisico) -> Decimal:
    if d.lote and d.lote.costo_unitario > 0:
        return d.lote.costo_unitario
    return d.producto.precio_costo


def _totales(inv: InventarioFisico) -> dict[str, Any]:
    faltante = sobrante = CERO
    for d in inv.detalles:
        if d.diferencia:
            valor = d.diferencia * _costo(d)
            if valor < 0:
                faltante += -valor
            else:
                sobrante += valor
    return {
        "total_lineas": len(inv.detalles),
        "contadas": sum(1 for d in inv.detalles if d.stock_contado is not None),
        "con_diferencia": sum(1 for d in inv.detalles if d.diferencia),
        "valor_faltante": redondear(faltante),
        "valor_sobrante": redondear(sobrante),
    }


def _listado(inv: InventarioFisico, nombres: dict[int, str], ver: bool) -> dict[str, Any]:
    totales = _totales(inv)
    if not ver:
        totales["valor_faltante"] = totales["valor_sobrante"] = None
    return {
        "id": inv.id,
        "numero": inv.numero,
        "almacen_id": inv.almacen_id,
        "almacen": inv.almacen.nombre,
        "descripcion": inv.descripcion,
        "estado": inv.estado,
        "usuario": nombres.get(inv.usuario_id),
        "aprobado_por": nombres.get(inv.aprobado_por_id) if inv.aprobado_por_id else None,
        "creado_en": inv.creado_en,
        "fecha_envio": inv.fecha_envio,
        "fecha_aplicacion": inv.fecha_aplicacion,
        **totales,
    }


async def listar(
    session: AsyncSession,
    ctx: ContextoUsuario,
    params: ParametrosPaginacion,
    *,
    almacen_id: int | None,
    estado: EstadoInventarioFisico | None = None,
) -> tuple[list[dict[str, Any]], int]:
    almacen = await almacen_visible(session, ctx, almacen_id)
    consulta = (
        select(InventarioFisico)
        .where(InventarioFisico.almacen_id == almacen.id)
        .options(selectinload(InventarioFisico.detalles))
        .order_by(InventarioFisico.creado_en.desc(), InventarioFisico.id.desc())
    )
    if estado:
        consulta = consulta.where(InventarioFisico.estado == estado)
    items, total = await paginar(session, consulta, params)
    nombres = await nombres_usuarios(session, [i for x in items for i in (x.usuario_id, x.aprobado_por_id)])
    ver = puede_ver_costos(ctx)
    return [_listado(x, nombres, ver) for x in items], total


async def obtener(session: AsyncSession, ctx: ContextoUsuario, inventario_id: int) -> dict[str, Any]:
    inv = await _cargar(session, inventario_id)
    await almacen_visible(session, ctx, inv.almacen_id)
    nombres = await nombres_usuarios(session, [inv.usuario_id, inv.aprobado_por_id])
    ver = puede_ver_costos(ctx)
    ids = {d.producto_id for d in inv.detalles}
    codigos = (
        dict(
            (
                await session.execute(
                    select(CodigoBarras.producto_id, func.min(CodigoBarras.codigo))
                    .where(and_(CodigoBarras.producto_id.in_(ids), CodigoBarras.presentacion_id.is_(None)))
                    .group_by(CodigoBarras.producto_id)
                )
            )
            .tuples()
            .all()
        )
        if ids
        else {}
    )
    datos = _listado(inv, nombres, ver)
    datos.update(
        usuario_id=inv.usuario_id,
        categoria_id=inv.categoria_id,
        motivo_rechazo=inv.motivo_rechazo,
        puede_aprobar=inv.estado == EstadoInventarioFisico.PENDIENTE_APROBACION
        and await puede_aprobar(session, ctx, inv.usuario_id),
        detalles=[
            {
                "id": d.id,
                "producto_id": d.producto_id,
                "producto": d.producto.nombre,
                "codigo_barras": codigos.get(d.producto_id),
                "lote_id": d.lote_id,
                "lote": d.lote.numero_lote if d.lote else None,
                "fecha_vencimiento": d.lote.fecha_vencimiento if d.lote else None,
                "stock_sistema": d.stock_sistema,
                "stock_contado": d.stock_contado,
                "diferencia": d.diferencia,
                "costo_unitario": _costo(d) if ver else None,
                "valor_diferencia": redondear(d.diferencia * _costo(d)) if ver and d.diferencia is not None else None,
            }
            for d in inv.detalles
        ],
    )
    return datos
