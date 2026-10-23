"""Ajustes y mermas: BORRADOR -> PENDIENTE_APROBACION -> APLICADO / RECHAZADO (o ANULADO).

El stock solo cambia al APROBAR, con todo bloqueado y revalidado en ese momento. Quien crea el ajuste no lo
puede aprobar (salvo que sea la única persona con ese permiso en la sucursal).
"""

from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.excepciones import Conflicto, NoEncontrado, ValidacionNegocio
from app.dependencies.auth import ContextoUsuario
from app.models import AjusteInventario, DetalleAjusteInventario, Lote, MotivoAjuste, Producto, StockAlmacen
from app.models.base import CERO
from app.models.enums import EstadoDocumento, TipoMotivoAjuste, TipoMovimientoInventario
from app.schemas.inventario import AjusteActualizar, AjusteCrear, AjusteDetalleEntrada
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


async def _cargar(session: AsyncSession, ajuste_id: int, *, bloquear: bool = False) -> AjusteInventario:
    consulta = select(AjusteInventario).where(AjusteInventario.id == ajuste_id)
    if bloquear:
        # Solo la fila del ajuste: sin JOIN (FOR UPDATE bloquearía también almacén y motivo)
        consulta = select(AjusteInventario).where(AjusteInventario.id == ajuste_id).with_for_update(of=AjusteInventario)
    consulta = consulta.options(selectinload(AjusteInventario.detalles)).execution_options(populate_existing=True)
    ajuste = await session.scalar(consulta)
    if ajuste is None:
        raise NoEncontrado("El ajuste no existe")
    return ajuste


async def _motivo(session: AsyncSession, motivo_id: int) -> MotivoAjuste:
    motivo = await session.get(MotivoAjuste, motivo_id)
    if motivo is None or not motivo.activo:
        raise ValidacionNegocio("El motivo no existe o está inactivo", codigo="motivo_invalido")
    return motivo


async def _validar_detalles(
    session: AsyncSession, almacen_id: int, motivo: MotivoAjuste, detalles: list[AjusteDetalleEntrada]
) -> list[DetalleAjusteInventario]:
    """Valida las líneas y las convierte en detalles (con el costo actual para valorizar)."""
    ids = {d.producto_id for d in detalles}
    productos = {p.id: p for p in await session.scalars(select(Producto).where(Producto.id.in_(ids)))}
    if len(productos) != len(ids):
        raise ValidacionNegocio("Alguno de los productos no existe", codigo="producto_invalido")
    disponibles = dict(
        (
            await session.execute(
                select(StockAlmacen.producto_id, StockAlmacen.cantidad).where(
                    StockAlmacen.producto_id.in_(ids), StockAlmacen.almacen_id == almacen_id
                )
            )
        )
        .tuples()
        .all()
    )
    vistos: set[tuple[int, Any]] = set()
    resultado = []
    for d in detalles:
        producto = productos[d.producto_id]
        if not producto.activo:
            raise ValidacionNegocio(f"«{producto.nombre}» está inactivo", codigo="producto_inactivo")
        stock.validar_cantidad(producto, abs(d.cantidad))
        if motivo.tipo == TipoMotivoAjuste.ENTRADA and d.cantidad < 0:
            raise ValidacionNegocio(f"El motivo «{motivo.nombre}» solo permite entradas", codigo="signo_invalido")
        if motivo.tipo == TipoMotivoAjuste.SALIDA and d.cantidad > 0:
            raise ValidacionNegocio(f"El motivo «{motivo.nombre}» solo permite salidas", codigo="signo_invalido")

        lote: Lote | None = None
        numero = d.numero_lote.strip().upper() if d.numero_lote else None
        if producto.maneja_lotes:
            if d.lote_id is not None:
                lote = await session.get(Lote, d.lote_id)
                if lote is None or lote.producto_id != producto.id or lote.almacen_id != almacen_id:
                    raise ValidacionNegocio(
                        f"El lote no corresponde a «{producto.nombre}» en este almacén", codigo="lote_invalido"
                    )
                if d.cantidad < 0 and lote.cantidad_actual < -d.cantidad:
                    raise ValidacionNegocio(
                        f"El lote {lote.numero_lote} de «{producto.nombre}» solo tiene "
                        f"{stock.fmt(lote.cantidad_actual)}",
                        codigo="lote_insuficiente",
                    )
                numero = None
            elif d.cantidad < 0:
                raise ValidacionNegocio(f"Indique de qué lote sale «{producto.nombre}»", codigo="lote_requerido")
            elif not numero:
                raise ValidacionNegocio(f"Indique el lote donde entra «{producto.nombre}»", codigo="lote_requerido")
        elif d.lote_id or numero or d.fecha_vencimiento:
            raise ValidacionNegocio(f"«{producto.nombre}» no maneja lotes", codigo="lote_invalido")
        elif d.cantidad < 0 and disponibles.get(producto.id, CERO) < -d.cantidad:
            raise ValidacionNegocio(
                f"Stock insuficiente de «{producto.nombre}»: "
                f"hay {stock.fmt(max(disponibles.get(producto.id, CERO), CERO))}",
                codigo="stock_insuficiente",
            )

        clave = (producto.id, lote.id if lote else numero)
        if clave in vistos:
            raise ValidacionNegocio(f"«{producto.nombre}» está repetido en el ajuste", codigo="producto_repetido")
        vistos.add(clave)
        resultado.append(
            DetalleAjusteInventario(
                producto_id=producto.id,
                lote_id=lote.id if lote else None,
                cantidad=d.cantidad,
                costo_unitario=lote.costo_unitario if lote and lote.costo_unitario > 0 else producto.precio_costo,
                numero_lote=numero,
                fecha_vencimiento=d.fecha_vencimiento if numero else None,
            )
        )
    return resultado


def _auditar(session, ctx: ContextoUsuario, ajuste: AjusteInventario, accion: str, descripcion: str, **datos):
    auditoria.registrar(
        session,
        accion=accion,
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad="ajuste",
        entidad_id=ajuste.id,
        descripcion=descripcion,
        datos=datos or None,
        ip=ctx.ip,
    )


async def crear(session: AsyncSession, ctx: ContextoUsuario, datos: AjusteCrear, clave: str | None) -> int:
    async def accion() -> int:
        almacen = await almacen_de_trabajo(session, ctx, datos.almacen_id)
        motivo = await _motivo(session, datos.motivo_id)
        detalles = await _validar_detalles(session, almacen.id, motivo, datos.detalles)
        ajuste = AjusteInventario(
            numero=await correlativos.siguiente(session, "AJUSTE"),
            almacen_id=almacen.id,
            motivo_id=motivo.id,
            observaciones=datos.observaciones,
            usuario_id=ctx.usuario_id,
            estado=EstadoDocumento.PENDIENTE_APROBACION if datos.enviar else EstadoDocumento.BORRADOR,
            fecha_envio=ahora_utc() if datos.enviar else None,
            detalles=detalles,
        )
        session.add(ajuste)
        await session.flush()
        _auditar(
            session,
            ctx,
            ajuste,
            "CREAR",
            f"Registró el ajuste {ajuste.numero} ({motivo.nombre})"
            + (" y lo envió a aprobación" if datos.enviar else " como borrador"),
        )
        return ajuste.id

    return await transacciones.ejecutar(
        session, accion, usuario_id=ctx.usuario_id, operacion="crear_ajuste", clave=clave
    )


async def actualizar(session: AsyncSession, ctx: ContextoUsuario, ajuste_id: int, datos: AjusteActualizar) -> int:
    ajuste = await _cargar(session, ajuste_id, bloquear=True)
    if ajuste.estado != EstadoDocumento.BORRADOR:
        raise Conflicto("Solo se puede editar un ajuste en borrador", codigo="estado_invalido")
    if ajuste.usuario_id != ctx.usuario_id:
        raise ValidacionNegocio("Solo quien creó el borrador puede editarlo", codigo="no_es_el_autor")
    motivo = await _motivo(session, datos.motivo_id)
    ajuste.detalles = await _validar_detalles(session, ajuste.almacen_id, motivo, datos.detalles)
    ajuste.motivo_id = motivo.id
    ajuste.observaciones = datos.observaciones
    _auditar(session, ctx, ajuste, "EDITAR", f"Editó el borrador {ajuste.numero}")
    await session.commit()
    return ajuste.id


async def enviar(session: AsyncSession, ctx: ContextoUsuario, ajuste_id: int) -> int:
    ajuste = await _cargar(session, ajuste_id, bloquear=True)
    if ajuste.estado == EstadoDocumento.PENDIENTE_APROBACION:
        return ajuste.id  # ya enviado (doble clic)
    if ajuste.estado != EstadoDocumento.BORRADOR:
        raise Conflicto("Solo se puede enviar un ajuste en borrador", codigo="estado_invalido")
    ajuste.estado = EstadoDocumento.PENDIENTE_APROBACION
    ajuste.fecha_envio = ahora_utc()
    _auditar(session, ctx, ajuste, "ENVIAR", f"Envió a aprobación el ajuste {ajuste.numero}")
    await session.commit()
    return ajuste.id


async def aprobar(session: AsyncSession, ctx: ContextoUsuario, ajuste_id: int) -> int:
    async def accion() -> int:
        ajuste = await _cargar(session, ajuste_id, bloquear=True)
        if ajuste.estado == EstadoDocumento.APLICADO:
            raise Conflicto(f"El ajuste {ajuste.numero} ya fue aplicado", codigo="ya_aplicado")
        if ajuste.estado != EstadoDocumento.PENDIENTE_APROBACION:
            raise Conflicto("Solo se puede aprobar un ajuste pendiente de aprobación", codigo="estado_invalido")
        await exigir_aprobador(session, ctx, ajuste.usuario_id)
        almacen = await almacen_de_trabajo(session, ctx, ajuste.almacen_id)
        motivo = await session.get(MotivoAjuste, ajuste.motivo_id)
        bloqueo = await stock.bloquear(session, [d.producto_id for d in ajuste.detalles], [almacen.id])
        tipo_texto = f"{motivo.nombre} ({ajuste.numero})"
        for d in sorted(ajuste.detalles, key=lambda x: (x.producto_id, x.id)):
            producto = bloqueo.productos[d.producto_id]
            if not producto.activo:
                raise ValidacionNegocio(f"«{producto.nombre}» fue desactivado", codigo="producto_inactivo")
            lote = None
            if d.lote_id is not None:
                lote = await stock.bloquear_lote(session, d.lote_id, d.producto_id, almacen.id)
            elif d.numero_lote:
                lote = await stock.lote_para_entrada(
                    session, d.producto_id, almacen.id, d.numero_lote, d.fecha_vencimiento, producto.precio_costo
                )
                d.lote_id = lote.id
            # Se valoriza con el costo vigente al momento de aplicar
            d.costo_unitario = lote.costo_unitario if lote and lote.costo_unitario > 0 else producto.precio_costo
            stock.mover(
                session,
                producto=producto,
                stock=bloqueo.stock(d.producto_id, almacen.id),
                cantidad=d.cantidad,
                tipo=TipoMovimientoInventario.AJUSTE_ENTRADA
                if d.cantidad > 0
                else TipoMovimientoInventario.AJUSTE_SALIDA,
                costo_unitario=d.costo_unitario,
                usuario_id=ctx.usuario_id,
                referencia_tipo="ajuste",
                referencia_id=ajuste.id,
                motivo=tipo_texto,
                lote=lote,
            )
        ajuste.estado = EstadoDocumento.APLICADO
        ajuste.aprobado_por_id = ctx.usuario_id
        ajuste.fecha_aplicacion = ahora_utc()
        _auditar(session, ctx, ajuste, "APROBAR", f"Aprobó y aplicó el ajuste {ajuste.numero}")
        return ajuste.id

    return await transacciones.ejecutar(session, accion, usuario_id=ctx.usuario_id, operacion="aprobar_ajuste")


async def rechazar(session: AsyncSession, ctx: ContextoUsuario, ajuste_id: int, motivo: str) -> int:
    ajuste = await _cargar(session, ajuste_id, bloquear=True)
    if ajuste.estado != EstadoDocumento.PENDIENTE_APROBACION:
        raise Conflicto("Solo se puede rechazar un ajuste pendiente de aprobación", codigo="estado_invalido")
    ctx.exigir("inventario.aprobar_ajustes")
    ajuste.estado = EstadoDocumento.RECHAZADO
    ajuste.motivo_rechazo = motivo
    ajuste.aprobado_por_id = ctx.usuario_id
    _auditar(session, ctx, ajuste, "RECHAZAR", f"Rechazó el ajuste {ajuste.numero}", motivo=motivo)
    await session.commit()
    return ajuste.id


async def anular(session: AsyncSession, ctx: ContextoUsuario, ajuste_id: int) -> int:
    ajuste = await _cargar(session, ajuste_id, bloquear=True)
    if ajuste.estado not in (EstadoDocumento.BORRADOR, EstadoDocumento.PENDIENTE_APROBACION):
        raise Conflicto(
            "Un ajuste aplicado no se anula: registre otro ajuste en sentido contrario", codigo="estado_invalido"
        )
    if ajuste.usuario_id != ctx.usuario_id and not ctx.tiene("inventario.aprobar_ajustes"):
        raise ValidacionNegocio("Solo quien lo creó o un aprobador puede anularlo", codigo="no_es_el_autor")
    ajuste.estado = EstadoDocumento.ANULADO
    _auditar(session, ctx, ajuste, "ANULAR", f"Anuló el ajuste {ajuste.numero}")
    await session.commit()
    return ajuste.id


# --- Consultas ---------------------------------------------------------------------------------------------


def _valor(detalles: list[DetalleAjusteInventario]) -> Decimal:
    return redondear(sum((d.cantidad * d.costo_unitario for d in detalles), CERO))


async def listar(
    session: AsyncSession,
    ctx: ContextoUsuario,
    params: ParametrosPaginacion,
    *,
    almacen_id: int | None,
    estado: EstadoDocumento | None = None,
) -> tuple[list[dict[str, Any]], int]:
    almacen = await almacen_visible(session, ctx, almacen_id)
    consulta = (
        select(AjusteInventario)
        .where(AjusteInventario.almacen_id == almacen.id)
        .options(selectinload(AjusteInventario.detalles))
        .order_by(AjusteInventario.creado_en.desc(), AjusteInventario.id.desc())
    )
    if estado:
        consulta = consulta.where(AjusteInventario.estado == estado)
    ajustes, total = await paginar(session, consulta, params)
    nombres = await nombres_usuarios(session, [i for a in ajustes for i in (a.usuario_id, a.aprobado_por_id)])
    ver = puede_ver_costos(ctx)
    return [_listado(a, nombres, ver) for a in ajustes], total


def _listado(a: AjusteInventario, nombres: dict[int, str], ver: bool) -> dict[str, Any]:
    return {
        "id": a.id,
        "numero": a.numero,
        "almacen_id": a.almacen_id,
        "almacen": a.almacen.nombre,
        "motivo": a.motivo.nombre,
        "es_merma": a.motivo.es_merma,
        "estado": a.estado,
        "observaciones": a.observaciones,
        "usuario": nombres.get(a.usuario_id),
        "aprobado_por": nombres.get(a.aprobado_por_id) if a.aprobado_por_id else None,
        "total_unidades": sum((d.cantidad for d in a.detalles), CERO),
        "valor": _valor(a.detalles) if ver else None,
        "creado_en": a.creado_en,
        "fecha_envio": a.fecha_envio,
        "fecha_aplicacion": a.fecha_aplicacion,
    }


async def obtener(session: AsyncSession, ctx: ContextoUsuario, ajuste_id: int) -> dict[str, Any]:
    ajuste = await _cargar(session, ajuste_id)
    await almacen_visible(session, ctx, ajuste.almacen_id)
    nombres = await nombres_usuarios(session, [ajuste.usuario_id, ajuste.aprobado_por_id])
    ver = puede_ver_costos(ctx)
    datos = _listado(ajuste, nombres, ver)
    datos.update(
        usuario_id=ajuste.usuario_id,
        motivo_id=ajuste.motivo_id,
        motivo_rechazo=ajuste.motivo_rechazo,
        puede_aprobar=ajuste.estado == EstadoDocumento.PENDIENTE_APROBACION
        and await puede_aprobar(session, ctx, ajuste.usuario_id),
        detalles=[
            {
                "id": d.id,
                "producto_id": d.producto_id,
                "producto": d.producto.nombre,
                "lote_id": d.lote_id,
                "lote": d.lote.numero_lote if d.lote else d.numero_lote,
                "fecha_vencimiento": d.lote.fecha_vencimiento if d.lote else d.fecha_vencimiento,
                "cantidad": d.cantidad,
                "costo_unitario": d.costo_unitario if ver else None,
                "valor": redondear(d.cantidad * d.costo_unitario) if ver else None,
            }
            for d in ajuste.detalles
        ],
    )
    return datos


async def contar_pendientes(session: AsyncSession, almacen_id: int) -> int:
    return int(
        await session.scalar(
            select(func.count(AjusteInventario.id)).where(
                AjusteInventario.almacen_id == almacen_id,
                AjusteInventario.estado == EstadoDocumento.PENDIENTE_APROBACION,
            )
        )
        or 0
    )
