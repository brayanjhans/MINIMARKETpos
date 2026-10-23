"""Transferencias entre almacenes: PENDIENTE -> EN_TRANSITO -> RECIBIDA (o ANULADA).

- Al enviar, la mercadería sale del origen (FEFO si maneja lotes, una línea por lote) y queda "en tránsito".
- Al recibir, entra al destino lo que realmente llegó, en un lote con el mismo número y vencimiento.
  Lo que no llegó queda registrado como faltante (merma valorizada del almacén de origen).
- Una transferencia en tránsito se puede anular: la mercadería vuelve al origen, a sus mismos lotes.
"""

from decimal import Decimal
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.excepciones import Conflicto, NoEncontrado, ValidacionNegocio
from app.dependencies.auth import ContextoUsuario
from app.models import Almacen, DetalleTransferencia, Lote, Producto, Sucursal, Transferencia
from app.models.base import CERO
from app.models.enums import EstadoTransferencia, TipoMovimientoInventario
from app.schemas.inventario import RecepcionEntrada, TransferenciaCrear
from app.services import auditoria, correlativos, stock, transacciones
from app.services.inventario import almacen_de_trabajo, nombres_usuarios, redondear
from app.services.productos import puede_ver_costos
from app.utils.paginacion import ParametrosPaginacion, paginar
from app.utils.zona_horaria import ahora_utc

MODULO = "inventario"


async def _cargar(session: AsyncSession, transferencia_id: int, *, bloquear: bool = False) -> Transferencia:
    consulta = select(Transferencia).where(Transferencia.id == transferencia_id)
    if bloquear:
        consulta = consulta.with_for_update(of=Transferencia)
    consulta = consulta.options(selectinload(Transferencia.detalles)).execution_options(populate_existing=True)
    transferencia = await session.scalar(consulta)
    if transferencia is None:
        raise NoEncontrado("La transferencia no existe")
    return transferencia


def _auditar(session, ctx: ContextoUsuario, t: Transferencia, accion: str, descripcion: str, **datos) -> None:
    auditoria.registrar(
        session,
        accion=accion,
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad="transferencia",
        entidad_id=t.id,
        descripcion=descripcion,
        datos=datos or None,
        ip=ctx.ip,
    )


async def _enviar(session: AsyncSession, ctx: ContextoUsuario, t: Transferencia) -> None:
    """Saca la mercadería del origen. Las líneas sin lote de productos con lotes se reparten por FEFO."""
    bloqueo = await stock.bloquear(session, [d.producto_id for d in t.detalles], [t.almacen_origen_id])
    nuevas: list[DetalleTransferencia] = []
    for d in sorted(list(t.detalles), key=lambda x: (x.producto_id, x.id)):
        producto = bloqueo.productos[d.producto_id]
        if not producto.activo:
            raise ValidacionNegocio(f"«{producto.nombre}» está inactivo", codigo="producto_inactivo")
        fila = bloqueo.stock(d.producto_id, t.almacen_origen_id)
        comunes = dict(
            tipo=TipoMovimientoInventario.TRANSFERENCIA_SALIDA,
            usuario_id=ctx.usuario_id,
            referencia_tipo="transferencia",
            referencia_id=t.id,
            motivo=f"Envío {t.numero}",
        )
        if producto.maneja_lotes and d.lote_id is None:
            t.detalles.remove(d)
            usados = await stock.salida_fefo(
                session,
                producto=producto,
                stock=fila,
                cantidad=d.cantidad,
                costo_unitario=producto.precio_costo,
                **comunes,
            )
            for lote, cantidad in usados:
                nuevas.append(
                    DetalleTransferencia(
                        producto_id=producto.id,
                        lote_id=lote.id,
                        cantidad=cantidad,
                        costo_unitario=lote.costo_unitario if lote.costo_unitario > 0 else producto.precio_costo,
                    )
                )
            continue
        lote = None
        if d.lote_id is not None:
            lote = await stock.bloquear_lote(session, d.lote_id, d.producto_id, t.almacen_origen_id)
        d.costo_unitario = lote.costo_unitario if lote and lote.costo_unitario > 0 else producto.precio_costo
        stock.mover(
            session,
            producto=producto,
            stock=fila,
            cantidad=-d.cantidad,
            costo_unitario=d.costo_unitario,
            lote=lote,
            **comunes,
        )
    t.detalles.extend(nuevas)
    t.estado = EstadoTransferencia.EN_TRANSITO
    t.fecha_envio = ahora_utc()


async def crear(session: AsyncSession, ctx: ContextoUsuario, datos: TransferenciaCrear, clave: str | None) -> int:
    async def accion() -> int:
        origen = await almacen_de_trabajo(session, ctx, datos.almacen_origen_id)
        destino = await session.get(Almacen, datos.almacen_destino_id)
        if destino is None or not destino.activo:
            raise ValidacionNegocio("El almacén de destino no existe o está inactivo", codigo="almacen_invalido")
        if destino.id == origen.id:
            raise ValidacionNegocio("El origen y el destino deben ser distintos", codigo="mismo_almacen")
        vistos: set[tuple[int, int | None]] = set()
        ids = {d.producto_id for d in datos.detalles}
        productos = {p.id: p for p in await session.scalars(select(Producto).where(Producto.id.in_(ids)))}
        if len(productos) != len(ids):
            raise ValidacionNegocio("Alguno de los productos no existe", codigo="producto_invalido")
        for d in datos.detalles:
            producto = productos[d.producto_id]
            stock.validar_cantidad(producto, d.cantidad)
            if d.lote_id is not None and not producto.maneja_lotes:
                raise ValidacionNegocio(f"«{producto.nombre}» no maneja lotes", codigo="lote_invalido")
            if (d.producto_id, d.lote_id) in vistos:
                raise ValidacionNegocio(f"«{producto.nombre}» está repetido", codigo="producto_repetido")
            vistos.add((d.producto_id, d.lote_id))
        t = Transferencia(
            numero=await correlativos.siguiente(session, "TRANSFERENCIA"),
            almacen_origen_id=origen.id,
            almacen_destino_id=destino.id,
            observaciones=datos.observaciones,
            usuario_id=ctx.usuario_id,
            detalles=[
                DetalleTransferencia(producto_id=d.producto_id, lote_id=d.lote_id, cantidad=d.cantidad)
                for d in datos.detalles
            ],
        )
        session.add(t)
        await session.flush()
        if datos.enviar:
            await _enviar(session, ctx, t)
        _auditar(
            session,
            ctx,
            t,
            "CREAR",
            f"{'Envió' if datos.enviar else 'Preparó'} la transferencia {t.numero} a {destino.nombre}",
        )
        return t.id

    return await transacciones.ejecutar(
        session, accion, usuario_id=ctx.usuario_id, operacion="crear_transferencia", clave=clave
    )


async def enviar(session: AsyncSession, ctx: ContextoUsuario, transferencia_id: int) -> int:
    async def accion() -> int:
        t = await _cargar(session, transferencia_id, bloquear=True)
        if t.estado == EstadoTransferencia.EN_TRANSITO:
            return t.id  # ya enviada (doble clic)
        if t.estado != EstadoTransferencia.PENDIENTE:
            raise Conflicto("Solo se puede enviar una transferencia preparada", codigo="estado_invalido")
        await almacen_de_trabajo(session, ctx, t.almacen_origen_id)
        await _enviar(session, ctx, t)
        _auditar(session, ctx, t, "ENVIAR", f"Envió la transferencia {t.numero}")
        return t.id

    return await transacciones.ejecutar(session, accion, usuario_id=ctx.usuario_id, operacion="enviar_transferencia")


async def recibir(session: AsyncSession, ctx: ContextoUsuario, transferencia_id: int, datos: RecepcionEntrada) -> int:
    async def accion() -> int:
        t = await _cargar(session, transferencia_id, bloquear=True)
        if t.estado == EstadoTransferencia.RECIBIDA:
            raise Conflicto(f"La transferencia {t.numero} ya fue recibida", codigo="ya_recibida")
        if t.estado != EstadoTransferencia.EN_TRANSITO:
            raise Conflicto("Solo se puede recibir una transferencia en tránsito", codigo="estado_invalido")
        destino = await almacen_de_trabajo(session, ctx, t.almacen_destino_id)
        por_id = {d.id: d for d in t.detalles}
        indicadas = {r.detalle_id: r for r in datos.detalles}
        if set(indicadas) - set(por_id):
            raise ValidacionNegocio("Alguna línea no pertenece a esta transferencia", codigo="detalle_invalido")

        bloqueo = await stock.bloquear(session, [d.producto_id for d in t.detalles], [destino.id])
        faltantes = CERO
        for d in sorted(t.detalles, key=lambda x: (x.producto_id, x.id)):
            producto = bloqueo.productos[d.producto_id]
            recepcion = indicadas.get(d.id)
            recibida = recepcion.cantidad_recibida if recepcion else d.cantidad
            if recibida > d.cantidad:
                raise ValidacionNegocio(
                    f"De «{producto.nombre}» se enviaron {stock.fmt(d.cantidad)}: no se puede recibir más",
                    codigo="recibe_de_mas",
                )
            stock.validar_cantidad(producto, recibida)
            d.cantidad_recibida = recibida
            if recibida < d.cantidad:
                faltantes += d.cantidad - recibida
                d.motivo_faltante = (recepcion.motivo_faltante if recepcion else None) or "No llegó"
            if recibida == 0:
                continue
            lote_destino = None
            if d.lote_id is not None:
                origen = await session.get(Lote, d.lote_id)
                lote_destino = await stock.lote_para_entrada(
                    session, producto.id, destino.id, origen.numero_lote, origen.fecha_vencimiento, d.costo_unitario
                )
            stock.mover(
                session,
                producto=producto,
                stock=bloqueo.stock(producto.id, destino.id),
                cantidad=recibida,
                tipo=TipoMovimientoInventario.TRANSFERENCIA_ENTRADA,
                costo_unitario=d.costo_unitario,
                usuario_id=ctx.usuario_id,
                referencia_tipo="transferencia",
                referencia_id=t.id,
                motivo=f"Recepción {t.numero}",
                lote=lote_destino,
            )
        t.estado = EstadoTransferencia.RECIBIDA
        t.usuario_recibe_id = ctx.usuario_id
        t.fecha_recepcion = ahora_utc()
        if datos.observaciones:
            t.observaciones = ((t.observaciones + " | ") if t.observaciones else "") + datos.observaciones
            t.observaciones = t.observaciones[:300]
        _auditar(
            session,
            ctx,
            t,
            "RECIBIR",
            f"Recibió la transferencia {t.numero}"
            + (f" con faltantes ({stock.fmt(faltantes)} und)" if faltantes else ""),
        )
        return t.id

    return await transacciones.ejecutar(session, accion, usuario_id=ctx.usuario_id, operacion="recibir_transferencia")


async def anular(session: AsyncSession, ctx: ContextoUsuario, transferencia_id: int) -> int:
    async def accion() -> int:
        t = await _cargar(session, transferencia_id, bloquear=True)
        if t.estado == EstadoTransferencia.ANULADA:
            return t.id
        if t.estado == EstadoTransferencia.RECIBIDA:
            raise Conflicto(
                "Una transferencia recibida no se puede anular: haga una transferencia de regreso",
                codigo="estado_invalido",
            )
        await almacen_de_trabajo(session, ctx, t.almacen_origen_id)
        if t.estado == EstadoTransferencia.EN_TRANSITO:
            bloqueo = await stock.bloquear(session, [d.producto_id for d in t.detalles], [t.almacen_origen_id])
            for d in sorted(t.detalles, key=lambda x: (x.producto_id, x.id)):
                lote = None
                if d.lote_id is not None:
                    lote = await stock.bloquear_lote(session, d.lote_id, d.producto_id, t.almacen_origen_id)
                stock.mover(
                    session,
                    producto=bloqueo.productos[d.producto_id],
                    stock=bloqueo.stock(d.producto_id, t.almacen_origen_id),
                    cantidad=d.cantidad,
                    tipo=TipoMovimientoInventario.TRANSFERENCIA_ANULADA,
                    costo_unitario=d.costo_unitario,
                    usuario_id=ctx.usuario_id,
                    referencia_tipo="transferencia",
                    referencia_id=t.id,
                    motivo=f"Anulación {t.numero}: vuelve al origen",
                    lote=lote,
                )
        t.estado = EstadoTransferencia.ANULADA
        _auditar(session, ctx, t, "ANULAR", f"Anuló la transferencia {t.numero}")
        return t.id

    return await transacciones.ejecutar(session, accion, usuario_id=ctx.usuario_id, operacion="anular_transferencia")


# --- Consultas ---------------------------------------------------------------------------------------------


async def _sucursales(session: AsyncSession, ids: set[int]) -> dict[int, str]:
    return dict(
        (await session.execute(select(Sucursal.id, Sucursal.nombre).where(Sucursal.id.in_(ids)))).tuples().all()
    )


def _listado(t: Transferencia, nombres: dict[int, str], sucursales: dict[int, str], ver: bool) -> dict[str, Any]:
    return {
        "id": t.id,
        "numero": t.numero,
        "estado": t.estado,
        "almacen_origen_id": t.almacen_origen_id,
        "almacen_origen": t.almacen_origen.nombre,
        "sucursal_origen": sucursales.get(t.almacen_origen.sucursal_id, ""),
        "almacen_destino_id": t.almacen_destino_id,
        "almacen_destino": t.almacen_destino.nombre,
        "sucursal_destino": sucursales.get(t.almacen_destino.sucursal_id, ""),
        "observaciones": t.observaciones,
        "usuario": nombres.get(t.usuario_id),
        "usuario_recibe": nombres.get(t.usuario_recibe_id) if t.usuario_recibe_id else None,
        "productos": len({d.producto_id for d in t.detalles}),
        "valor": redondear(sum((d.cantidad * d.costo_unitario for d in t.detalles), CERO)) if ver else None,
        "creado_en": t.creado_en,
        "fecha_envio": t.fecha_envio,
        "fecha_recepcion": t.fecha_recepcion,
    }


async def listar(
    session: AsyncSession,
    ctx: ContextoUsuario,
    params: ParametrosPaginacion,
    *,
    estado: EstadoTransferencia | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Transferencias que salen de o llegan a la sucursal actual."""
    almacenes_suc = select(Almacen.id).where(Almacen.sucursal_id == ctx.sucursal_id)
    consulta = (
        select(Transferencia)
        .where(
            or_(Transferencia.almacen_origen_id.in_(almacenes_suc), Transferencia.almacen_destino_id.in_(almacenes_suc))
        )
        .options(selectinload(Transferencia.detalles))
        .order_by(Transferencia.creado_en.desc(), Transferencia.id.desc())
    )
    if estado:
        consulta = consulta.where(Transferencia.estado == estado)
    items, total = await paginar(session, consulta, params)
    nombres = await nombres_usuarios(session, [i for t in items for i in (t.usuario_id, t.usuario_recibe_id)])
    sucursales = await _sucursales(
        session, {a.sucursal_id for t in items for a in (t.almacen_origen, t.almacen_destino)}
    )
    ver = puede_ver_costos(ctx)
    return [_listado(t, nombres, sucursales, ver) for t in items], total


async def obtener(session: AsyncSession, ctx: ContextoUsuario, transferencia_id: int) -> dict[str, Any]:
    t = await _cargar(session, transferencia_id)
    sucursales_doc = {t.almacen_origen.sucursal_id, t.almacen_destino.sucursal_id}
    if ctx.sucursal_id not in sucursales_doc and not ctx.tiene("sucursales.todas"):
        raise NoEncontrado("La transferencia no existe")
    nombres = await nombres_usuarios(session, [t.usuario_id, t.usuario_recibe_id])
    ver = puede_ver_costos(ctx)
    datos = _listado(t, nombres, await _sucursales(session, sucursales_doc), ver)
    datos.update(
        puede_recibir=t.estado == EstadoTransferencia.EN_TRANSITO
        and t.almacen_destino.sucursal_id == ctx.sucursal_id
        and ctx.tiene("inventario.recibir_transferencia"),
        puede_anular=t.estado in (EstadoTransferencia.PENDIENTE, EstadoTransferencia.EN_TRANSITO)
        and t.almacen_origen.sucursal_id == ctx.sucursal_id
        and ctx.tiene("inventario.transferir"),
        detalles=[
            {
                "id": d.id,
                "producto_id": d.producto_id,
                "producto": d.producto.nombre,
                "lote_id": d.lote_id,
                "lote": d.lote.numero_lote if d.lote else None,
                "fecha_vencimiento": d.lote.fecha_vencimiento if d.lote else None,
                "cantidad": d.cantidad,
                "cantidad_recibida": d.cantidad_recibida,
                "faltante": d.cantidad - d.cantidad_recibida
                if t.estado == EstadoTransferencia.RECIBIDA
                else Decimal(0),
                "motivo_faltante": d.motivo_faltante,
                "costo_unitario": d.costo_unitario if ver else None,
            }
            for d in t.detalles
        ],
    )
    return datos
