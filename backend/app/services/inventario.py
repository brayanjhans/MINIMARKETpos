"""Consultas de inventario, stock inicial, revisión de integridad y utilidades comunes de los documentos."""

from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import NoEncontrado, ValidacionNegocio
from app.dependencies.auth import ContextoUsuario
from app.models import (
    AjusteInventario,
    Almacen,
    Categoria,
    CodigoBarras,
    DetalleAjusteInventario,
    DetalleTransferencia,
    InventarioFisico,
    Lote,
    MotivoAjuste,
    MovimientoInventario,
    Permiso,
    Producto,
    Rol,
    StockAlmacen,
    Sucursal,
    Transferencia,
    Usuario,
    rol_permisos,
    usuario_sucursales,
)
from app.models.base import CERO
from app.models.enums import EstadoDocumento, EstadoTransferencia, TipoMovimientoInventario
from app.schemas.inventario import StockInicialEntrada
from app.services import auditoria, imagenes, parametros, stock, transacciones
from app.services.productos import almacen_venta_id, estado_stock, filtro_busqueda, puede_ver_costos
from app.utils.paginacion import ParametrosPaginacion, aplicar_orden, paginar
from app.utils.zona_horaria import a_utc, hoy_local

MODULO = "inventario"
DOS = Decimal("0.01")
PERMISO_APROBAR = "inventario.aprobar_ajustes"


# --- Almacenes y usuarios ----------------------------------------------------------------------------------


async def almacenes(session: AsyncSession, ctx: ContextoUsuario) -> list[dict[str, Any]]:
    filas = await session.execute(
        select(Almacen, Sucursal)
        .join(Sucursal, Sucursal.id == Almacen.sucursal_id)
        .where(Almacen.activo.is_(True), Sucursal.activo.is_(True))
        .order_by(Sucursal.id != ctx.sucursal_id, Sucursal.nombre, Almacen.es_almacen_venta.desc(), Almacen.nombre)
    )
    return [
        {
            "id": a.id,
            "nombre": a.nombre,
            "sucursal_id": s.id,
            "sucursal": s.nombre,
            "es_almacen_venta": a.es_almacen_venta,
            "es_sucursal_actual": s.id == ctx.sucursal_id,
        }
        for a, s in filas.tuples()
    ]


async def almacen_de_trabajo(
    session: AsyncSession, ctx: ContextoUsuario, almacen_id: int | None, *, bloquear: bool = False
) -> Almacen:
    """Almacén donde se OPERA: debe ser de la sucursal actual (por defecto, su almacén de venta)."""
    if almacen_id is None:
        almacen_id = await almacen_venta_id(session, ctx.sucursal_id)
        if almacen_id is None:
            raise ValidacionNegocio("La sucursal no tiene un almacén de venta configurado", codigo="sin_almacen")
    consulta = select(Almacen).where(Almacen.id == almacen_id)
    if bloquear:
        consulta = consulta.with_for_update()
    almacen = await session.scalar(consulta)
    if almacen is None or not almacen.activo:
        raise NoEncontrado("El almacén no existe o está inactivo")
    if almacen.sucursal_id != ctx.sucursal_id:
        raise ValidacionNegocio(
            "Solo puede operar almacenes de la sucursal en la que trabaja", codigo="almacen_de_otra_sucursal"
        )
    return almacen


async def almacen_visible(session: AsyncSession, ctx: ContextoUsuario, almacen_id: int | None) -> Almacen:
    """Almacén que se puede CONSULTAR: el de la sucursal actual, o cualquiera con el permiso sucursales.todas."""
    if almacen_id is None:
        return await almacen_de_trabajo(session, ctx, None)
    almacen = await session.get(Almacen, almacen_id)
    if almacen is None:
        raise NoEncontrado("El almacén no existe")
    if almacen.sucursal_id != ctx.sucursal_id and not ctx.tiene("sucursales.todas"):
        raise ValidacionNegocio("No tiene acceso a los almacenes de otra sucursal", codigo="almacen_de_otra_sucursal")
    return almacen


async def nombres_usuarios(session: AsyncSession, ids: Iterable[int | None]) -> dict[int, str]:
    validos = {i for i in ids if i}
    if not validos:
        return {}
    filas = await session.execute(select(Usuario.id, Usuario.nombre_completo).where(Usuario.id.in_(validos)))
    return dict(filas.tuples().all())


async def puede_aprobar(session: AsyncSession, ctx: ContextoUsuario, creador_id: int) -> bool:
    """Quien crea un ajuste o conteo no puede aprobarlo, salvo que no haya OTRA persona activa con permiso de
    aprobar en la sucursal (negocios de una sola persona)."""
    if not ctx.tiene(PERMISO_APROBAR):
        return False
    if creador_id != ctx.usuario_id:
        return True
    otros = await session.scalar(
        select(func.count(func.distinct(Usuario.id)))
        .join(Rol, Rol.id == Usuario.rol_id)
        .join(rol_permisos, rol_permisos.c.rol_id == Rol.id)
        .join(Permiso, Permiso.id == rol_permisos.c.permiso_id)
        .join(usuario_sucursales, usuario_sucursales.c.usuario_id == Usuario.id)
        .where(
            Permiso.codigo == PERMISO_APROBAR,
            Usuario.activo.is_(True),
            Rol.activo.is_(True),
            Usuario.id != ctx.usuario_id,
            usuario_sucursales.c.sucursal_id == ctx.sucursal_id,
        )
    )
    return otros == 0


async def exigir_aprobador(session: AsyncSession, ctx: ContextoUsuario, creador_id: int) -> None:
    ctx.exigir(PERMISO_APROBAR)
    if not await puede_aprobar(session, ctx, creador_id):
        raise ValidacionNegocio(
            "No puede aprobar un documento que usted mismo creó: debe aprobarlo otra persona", codigo="autoaprobacion"
        )


def redondear(valor: Decimal) -> Decimal:
    return valor.quantize(DOS)


# --- Consultas ---------------------------------------------------------------------------------------------


def _columnas(almacen_id: int):
    cantidad = func.coalesce(StockAlmacen.cantidad, 0)
    pendiente = func.coalesce(StockAlmacen.pendiente_lote, 0)
    minimo = func.coalesce(StockAlmacen.stock_minimo, Producto.stock_minimo)
    union = and_(StockAlmacen.producto_id == Producto.id, StockAlmacen.almacen_id == almacen_id)
    return cantidad, pendiente, minimo, union


async def listar_stock(
    session: AsyncSession,
    ctx: ContextoUsuario,
    params: ParametrosPaginacion,
    *,
    almacen_id: int | None,
    busqueda: str | None = None,
    categoria_id: int | None = None,
    estado: str | None = None,
    orden: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    almacen = await almacen_visible(session, ctx, almacen_id)
    cantidad, pendiente, minimo, union = _columnas(almacen.id)
    codigo = (
        select(CodigoBarras.codigo)
        .where(CodigoBarras.producto_id == Producto.id, CodigoBarras.presentacion_id.is_(None))
        .order_by(CodigoBarras.id)
        .limit(1)
        .scalar_subquery()
    )
    valor = func.greatest(cantidad, 0) * Producto.precio_costo
    consulta = (
        select(Producto, cantidad, pendiente, minimo, codigo, Categoria.nombre, Categoria.color)
        .outerjoin(StockAlmacen, union)
        .outerjoin(Categoria, Categoria.id == Producto.categoria_id)
        .where(Producto.activo.is_(True))
    )
    if busqueda and busqueda.strip():
        consulta = consulta.where(filtro_busqueda(busqueda))
    if categoria_id:
        consulta = consulta.where(Producto.categoria_id == categoria_id)
    match estado:
        case "bajo":
            consulta = consulta.where(cantidad > 0, minimo > 0, cantidad <= minimo)
        case "sin_stock":
            consulta = consulta.where(cantidad == 0)
        case "con_stock":
            consulta = consulta.where(cantidad > 0)
        case "por_regularizar":
            consulta = consulta.where(or_(cantidad < 0, pendiente > 0))
    columnas = {"nombre": Producto.nombre, "stock": cantidad, "valor": valor}
    consulta = aplicar_orden(consulta, orden, columnas, "nombre").order_by(Producto.id)
    filas, total = await paginar(session, consulta, params, escalares=False)
    ver_costos = puede_ver_costos(ctx)
    items = []
    for producto, cant, pend, mini, cod, cat, color in filas:
        cant, pend, mini = Decimal(cant), Decimal(pend), Decimal(mini)
        _, miniatura = imagenes.urls(producto.imagen)
        items.append(
            {
                "producto_id": producto.id,
                "nombre": producto.nombre,
                "codigo_barras": cod,
                "categoria": cat,
                "categoria_color": color,
                "unidad_medida": producto.unidad_medida,
                "maneja_lotes": producto.maneja_lotes,
                "cantidad": cant,
                "pendiente_lote": pend,
                "stock_minimo": mini,
                "estado": "por_regularizar" if pend > 0 and cant >= 0 else estado_stock(cant, mini),
                "costo_unitario": producto.precio_costo if ver_costos else None,
                "valor": redondear(max(cant, CERO) * producto.precio_costo) if ver_costos else None,
                "miniatura_url": miniatura,
            }
        )
    return items, total


def _inicio_mes_utc() -> datetime:
    hoy = hoy_local()
    return a_utc(datetime.combine(hoy.replace(day=1), time.min))


async def resumen(session: AsyncSession, ctx: ContextoUsuario, almacen_id: int | None) -> dict[str, Any]:
    almacen = await almacen_visible(session, ctx, almacen_id)
    cantidad, pendiente, minimo, union = _columnas(almacen.id)
    activo = Producto.activo.is_(True)

    def contar(*condiciones):
        return func.coalesce(func.sum(case((and_(*condiciones), 1), else_=0)), 0)

    fila = (
        await session.execute(
            select(
                func.coalesce(func.sum(func.greatest(cantidad, 0) * Producto.precio_costo), 0),
                contar(cantidad > 0),
                func.coalesce(func.sum(func.greatest(cantidad, 0)), 0),
                contar(cantidad > 0, minimo > 0, cantidad <= minimo),
                contar(cantidad == 0),
                contar(or_(cantidad < 0, pendiente > 0)),
            )
            .select_from(Producto)
            .outerjoin(StockAlmacen, union)
            .where(activo)
        )
    ).one()

    dias = int(await parametros.obtener(session, "inventario.dias_alerta_vencimiento"))
    hoy = hoy_local()
    lotes = (
        await session.execute(
            select(
                contar(Lote.fecha_vencimiento >= hoy, Lote.fecha_vencimiento <= hoy + timedelta(days=dias)),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                and_(
                                    Lote.fecha_vencimiento >= hoy, Lote.fecha_vencimiento <= hoy + timedelta(days=dias)
                                ),
                                Lote.cantidad_actual * Lote.costo_unitario,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ),
                contar(Lote.fecha_vencimiento < hoy),
            ).where(Lote.almacen_id == almacen.id, Lote.cantidad_actual > 0)
        )
    ).one()

    inicio_mes = _inicio_mes_utc()
    merma_ajustes = await session.scalar(
        select(func.coalesce(func.sum(-DetalleAjusteInventario.cantidad * DetalleAjusteInventario.costo_unitario), 0))
        .join(AjusteInventario, AjusteInventario.id == DetalleAjusteInventario.ajuste_id)
        .join(MotivoAjuste, MotivoAjuste.id == AjusteInventario.motivo_id)
        .where(
            AjusteInventario.almacen_id == almacen.id,
            AjusteInventario.estado == EstadoDocumento.APLICADO,
            AjusteInventario.fecha_aplicacion >= inicio_mes,
            MotivoAjuste.es_merma.is_(True),
            DetalleAjusteInventario.cantidad < 0,
        )
    )
    merma_transferencias = await session.scalar(
        select(
            func.coalesce(
                func.sum(
                    (DetalleTransferencia.cantidad - DetalleTransferencia.cantidad_recibida)
                    * DetalleTransferencia.costo_unitario
                ),
                0,
            )
        )
        .join(Transferencia, Transferencia.id == DetalleTransferencia.transferencia_id)
        .where(
            Transferencia.almacen_origen_id == almacen.id,
            Transferencia.estado == EstadoTransferencia.RECIBIDA,
            Transferencia.fecha_recepcion >= inicio_mes,
        )
    )
    ajustes_mes = await session.scalar(
        select(func.count(AjusteInventario.id)).where(
            AjusteInventario.almacen_id == almacen.id,
            AjusteInventario.estado == EstadoDocumento.APLICADO,
            AjusteInventario.fecha_aplicacion >= inicio_mes,
        )
    )
    por_aprobar = await session.scalar(
        select(func.count(AjusteInventario.id)).where(
            AjusteInventario.almacen_id == almacen.id,
            AjusteInventario.estado == EstadoDocumento.PENDIENTE_APROBACION,
        )
    ) + await session.scalar(
        select(func.count(InventarioFisico.id)).where(
            InventarioFisico.almacen_id == almacen.id, InventarioFisico.estado == "PENDIENTE_APROBACION"
        )
    )
    transito = (
        await session.execute(
            select(
                func.coalesce(func.sum(DetalleTransferencia.cantidad * DetalleTransferencia.costo_unitario), 0),
                func.count(func.distinct(Transferencia.id)),
            )
            .select_from(Transferencia)
            .join(DetalleTransferencia, DetalleTransferencia.transferencia_id == Transferencia.id)
            .where(
                Transferencia.estado == EstadoTransferencia.EN_TRANSITO,
                or_(Transferencia.almacen_origen_id == almacen.id, Transferencia.almacen_destino_id == almacen.id),
            )
        )
    ).one()

    ver = puede_ver_costos(ctx)
    return {
        "almacen_id": almacen.id,
        "valor_total": redondear(Decimal(fila[0])) if ver else None,
        "productos": int(fila[1]),
        "unidades": Decimal(fila[2]),
        "stock_bajo": int(fila[3]),
        "sin_stock": int(fila[4]),
        "por_regularizar": int(fila[5]),
        "lotes_por_vencer": int(lotes[0]),
        "valor_por_vencer": redondear(Decimal(lotes[1])) if ver else None,
        "lotes_vencidos": int(lotes[2]),
        "dias_alerta": dias,
        "mermas_mes": redondear(Decimal(merma_ajustes) + Decimal(merma_transferencias)) if ver else None,
        "ajustes_mes": int(ajustes_mes),
        "por_aprobar": int(por_aprobar),
        "transito_valor": redondear(Decimal(transito[0])) if ver else None,
        "transito_documentos": int(transito[1]),
    }


async def listar_lotes(
    session: AsyncSession,
    ctx: ContextoUsuario,
    *,
    almacen_id: int | None,
    producto_id: int | None = None,
    por_vencer_dias: int | None = None,
    solo_vencidos: bool = False,
    limite: int = 200,
) -> list[dict[str, Any]]:
    almacen = await almacen_visible(session, ctx, almacen_id)
    hoy = hoy_local()
    consulta = (
        select(Lote, Producto.nombre)
        .join(Producto, Producto.id == Lote.producto_id)
        .where(Lote.almacen_id == almacen.id, Lote.cantidad_actual > 0)
        .order_by(Lote.fecha_vencimiento.is_(None), Lote.fecha_vencimiento, Lote.id)
        .limit(limite)
    )
    if producto_id:
        consulta = consulta.where(Lote.producto_id == producto_id)
    if solo_vencidos:
        consulta = consulta.where(Lote.fecha_vencimiento < hoy)
    elif por_vencer_dias is not None:
        consulta = consulta.where(Lote.fecha_vencimiento <= hoy + timedelta(days=por_vencer_dias))
    ver = puede_ver_costos(ctx)
    return [
        {
            "id": lote.id,
            "producto_id": lote.producto_id,
            "producto": nombre,
            "almacen_id": lote.almacen_id,
            "numero_lote": lote.numero_lote,
            "fecha_vencimiento": lote.fecha_vencimiento,
            "dias_para_vencer": (lote.fecha_vencimiento - hoy).days if lote.fecha_vencimiento else None,
            "cantidad_actual": lote.cantidad_actual,
            "costo_unitario": lote.costo_unitario if ver else None,
            "valor": redondear(lote.cantidad_actual * lote.costo_unitario) if ver else None,
        }
        for lote, nombre in (await session.execute(consulta)).tuples()
    ]


_DOCUMENTOS = {
    "ajuste": AjusteInventario,
    "transferencia": Transferencia,
    "inventario_fisico": InventarioFisico,
}


async def kardex(
    session: AsyncSession,
    ctx: ContextoUsuario,
    params: ParametrosPaginacion,
    *,
    almacen_id: int | None,
    producto_id: int | None = None,
    tipo: TipoMovimientoInventario | None = None,
    desde=None,
    hasta=None,
) -> tuple[list[dict[str, Any]], int]:
    almacen = await almacen_visible(session, ctx, almacen_id)
    consulta = (
        select(MovimientoInventario, Lote.numero_lote, Usuario.nombre_completo, Producto.nombre)
        .join(Producto, Producto.id == MovimientoInventario.producto_id)
        .outerjoin(Lote, Lote.id == MovimientoInventario.lote_id)
        .outerjoin(Usuario, Usuario.id == MovimientoInventario.usuario_id)
        .where(MovimientoInventario.almacen_id == almacen.id)
        .order_by(MovimientoInventario.creado_en.desc(), MovimientoInventario.id.desc())
    )
    if producto_id:
        consulta = consulta.where(MovimientoInventario.producto_id == producto_id)
    if tipo:
        consulta = consulta.where(MovimientoInventario.tipo == tipo)
    if desde:
        consulta = consulta.where(MovimientoInventario.creado_en >= a_utc(datetime.combine(desde, time.min)))
    if hasta:
        consulta = consulta.where(
            MovimientoInventario.creado_en < a_utc(datetime.combine(hasta + timedelta(days=1), time.min))
        )
    filas, total = await paginar(session, consulta, params, escalares=False)

    # Número de documento (AJ-000001, TR-...) en una consulta por tipo
    por_tipo: dict[str, set[int]] = defaultdict(set)
    for m, *_ in filas:
        if m.referencia_tipo in _DOCUMENTOS and m.referencia_id:
            por_tipo[m.referencia_tipo].add(m.referencia_id)
    numeros: dict[tuple[str, int], str] = {}
    for tipo_doc, ids in por_tipo.items():
        modelo = _DOCUMENTOS[tipo_doc]
        for id_, numero in (await session.execute(select(modelo.id, modelo.numero).where(modelo.id.in_(ids)))).tuples():
            numeros[(tipo_doc, id_)] = numero

    ver = puede_ver_costos(ctx)
    return [
        {
            "id": m.id,
            "creado_en": m.creado_en,
            "producto_id": m.producto_id,
            "producto": producto,
            "almacen_id": m.almacen_id,
            "tipo": m.tipo,
            "cantidad": m.cantidad,
            "stock_anterior": m.stock_anterior,
            "stock_nuevo": m.stock_nuevo,
            "costo_unitario": m.costo_unitario if ver else None,
            "lote": lote,
            "referencia_tipo": m.referencia_tipo,
            "referencia_id": m.referencia_id,
            "documento": numeros.get((m.referencia_tipo or "", m.referencia_id or 0)),
            "motivo": m.motivo,
            "usuario": usuario,
        }
        for m, lote, usuario, producto in filas
    ], total


async def motivos_ajuste(session: AsyncSession) -> list[MotivoAjuste]:
    return list(
        await session.scalars(select(MotivoAjuste).where(MotivoAjuste.activo.is_(True)).order_by(MotivoAjuste.id))
    )


# --- Stock inicial -----------------------------------------------------------------------------------------


async def _con_movimientos(session: AsyncSession, producto_ids: list[int], almacen_id: int) -> set[int]:
    return set(
        await session.scalars(
            select(MovimientoInventario.producto_id)
            .where(MovimientoInventario.producto_id.in_(producto_ids), MovimientoInventario.almacen_id == almacen_id)
            .distinct()
        )
    )


async def cargables(
    session: AsyncSession, ctx: ContextoUsuario, producto_ids: list[int], almacen_id: int | None
) -> list[dict[str, Any]]:
    almacen = await almacen_de_trabajo(session, ctx, almacen_id)
    usados = await _con_movimientos(session, producto_ids, almacen.id)
    return [
        {
            "producto_id": pid,
            "puede": pid not in usados,
            "motivo": "Ya tiene movimientos en este almacén: use un ajuste" if pid in usados else None,
        }
        for pid in producto_ids
    ]


def _validar_items_stock_inicial(items, productos: dict[int, Producto]) -> None:
    vistos: set[tuple[int, str | None]] = set()
    for item in items:
        producto = productos[item.producto_id]
        if not producto.activo:
            raise ValidacionNegocio(f"«{producto.nombre}» está inactivo", codigo="producto_inactivo")
        stock.validar_cantidad(producto, item.cantidad)
        if producto.maneja_lotes and not item.numero_lote:
            raise ValidacionNegocio(f"Indique el lote de «{producto.nombre}»", codigo="lote_requerido")
        if not producto.maneja_lotes and (item.numero_lote or item.fecha_vencimiento):
            raise ValidacionNegocio(f"«{producto.nombre}» no maneja lotes", codigo="lote_invalido")
        clave = (item.producto_id, item.numero_lote.strip().upper() if item.numero_lote else None)
        if clave in vistos:
            raise ValidacionNegocio(f"«{producto.nombre}» está repetido en la carga", codigo="producto_repetido")
        vistos.add(clave)


async def aplicar_stock_inicial(
    session: AsyncSession, ctx: ContextoUsuario, almacen: Almacen, items, *, origen: str = "STOCK_INICIAL"
) -> dict[str, Any]:
    """Aplica la carga (sin commit). Lo usan la pantalla de stock inicial y la importación de Excel."""
    producto_ids = [i.producto_id for i in items]
    bloqueo = await stock.bloquear(session, producto_ids, [almacen.id])
    _validar_items_stock_inicial(items, bloqueo.productos)
    # Se revisa DESPUÉS de bloquear: nadie puede registrar un movimiento de estos productos mientras tanto
    usados = await _con_movimientos(session, producto_ids, almacen.id)
    if usados:
        nombres = ", ".join(sorted(bloqueo.productos[p].nombre for p in usados)[:5])
        raise ValidacionNegocio(
            f"Ya tienen movimientos en este almacén (use un ajuste): {nombres}",
            codigo="ya_tiene_movimientos",
            datos={"producto_ids": sorted(usados)},
        )

    por_producto: dict[int, list] = defaultdict(list)
    for item in items:
        por_producto[item.producto_id].append(item)
    unidades = valor = CERO
    for producto_id in sorted(por_producto):
        producto = bloqueo.productos[producto_id]
        lineas = por_producto[producto_id]
        cantidad = sum((i.cantidad for i in lineas), CERO)
        costo = sum((i.cantidad * i.costo_unitario for i in lineas), CERO) / cantidad
        await stock.actualizar_costo_promedio(
            session, producto, cantidad, costo, usuario_id=ctx.usuario_id, origen=origen
        )
        fila = bloqueo.stock(producto_id, almacen.id)
        for item in lineas:
            lote = None
            if producto.maneja_lotes:
                lote = await stock.lote_para_entrada(
                    session, producto_id, almacen.id, item.numero_lote, item.fecha_vencimiento, item.costo_unitario
                )
            stock.mover(
                session,
                producto=producto,
                stock=fila,
                cantidad=item.cantidad,
                tipo=TipoMovimientoInventario.STOCK_INICIAL,
                costo_unitario=item.costo_unitario,
                usuario_id=ctx.usuario_id,
                referencia_tipo="stock_inicial",
                motivo="Carga de stock inicial" if origen == "STOCK_INICIAL" else "Stock inicial (importado de Excel)",
                lote=lote,
            )
            unidades += item.cantidad
            valor += item.cantidad * item.costo_unitario
    return {"productos": len(por_producto), "unidades": unidades, "valor": redondear(valor)}


async def cargar_stock_inicial(
    session: AsyncSession, ctx: ContextoUsuario, datos: StockInicialEntrada, clave: str | None
) -> dict[str, Any]:
    resultado: dict[str, Any] = {}

    async def accion() -> int:
        almacen = await almacen_de_trabajo(session, ctx, datos.almacen_id)
        resultado.clear()
        resultado.update(await aplicar_stock_inicial(session, ctx, almacen, datos.items))
        auditoria.registrar(
            session,
            accion="STOCK_INICIAL",
            modulo=MODULO,
            usuario_id=ctx.usuario_id,
            sucursal_id=ctx.sucursal_id,
            entidad="almacen",
            entidad_id=almacen.id,
            descripcion=f"Cargó stock inicial de {resultado['productos']} producto(s) en {almacen.nombre}",
            datos={k: str(v) for k, v in resultado.items()},
            ip=ctx.ip,
        )
        return almacen.id

    await transacciones.ejecutar(session, accion, usuario_id=ctx.usuario_id, operacion="stock_inicial", clave=clave)
    if not resultado:  # repetición de una carga ya hecha (misma clave): no se vuelve a aplicar
        return {
            "productos": len({i.producto_id for i in datos.items}),
            "unidades": sum((i.cantidad for i in datos.items), CERO),
            "valor": redondear(sum((i.cantidad * i.costo_unitario for i in datos.items), CERO)),
        }
    return resultado


# --- Integridad --------------------------------------------------------------------------------------------


async def revisar_integridad(session: AsyncSession) -> dict[str, Any]:
    """Comprueba que el stock cuadra con el kardex y con los lotes. Debe dar siempre cero problemas."""
    problemas: list[dict[str, Any]] = []
    nombres = dict((await session.execute(select(Producto.id, Producto.nombre))).tuples().all())

    def agregar(tipo: str, producto_id: int | None, almacen_id: int | None, detalle: str) -> None:
        problemas.append(
            {
                "tipo": tipo,
                "producto_id": producto_id,
                "producto": nombres.get(producto_id) if producto_id else None,
                "almacen_id": almacen_id,
                "detalle": detalle,
            }
        )

    suma_kardex = (
        select(
            MovimientoInventario.producto_id,
            MovimientoInventario.almacen_id,
            func.sum(MovimientoInventario.cantidad).label("total"),
        )
        .group_by(MovimientoInventario.producto_id, MovimientoInventario.almacen_id)
        .subquery()
    )
    filas = await session.execute(
        select(StockAlmacen.producto_id, StockAlmacen.almacen_id, StockAlmacen.cantidad, suma_kardex.c.total)
        .outerjoin(
            suma_kardex,
            and_(
                suma_kardex.c.producto_id == StockAlmacen.producto_id,
                suma_kardex.c.almacen_id == StockAlmacen.almacen_id,
            ),
        )
        .where(StockAlmacen.cantidad != func.coalesce(suma_kardex.c.total, 0))
    )
    for pid, aid, cantidad, total in filas.tuples():
        agregar("stock_vs_kardex", pid, aid, f"Stock {cantidad} pero el kardex suma {total or 0}")

    huerfanos = await session.execute(
        select(suma_kardex.c.producto_id, suma_kardex.c.almacen_id, suma_kardex.c.total).where(
            ~exists().where(
                StockAlmacen.producto_id == suma_kardex.c.producto_id,
                StockAlmacen.almacen_id == suma_kardex.c.almacen_id,
            )
        )
    )
    for pid, aid, total in huerfanos.tuples():
        agregar("kardex_sin_stock", pid, aid, f"El kardex suma {total} pero no hay fila de stock")

    cadena = await session.execute(
        select(MovimientoInventario.id, MovimientoInventario.producto_id, MovimientoInventario.almacen_id).where(
            MovimientoInventario.stock_nuevo != MovimientoInventario.stock_anterior + MovimientoInventario.cantidad
        )
    )
    for mid, pid, aid in cadena.tuples():
        agregar("movimiento_inconsistente", pid, aid, f"El movimiento {mid} no cuadra (anterior + cantidad ≠ nuevo)")

    suma_lotes = (
        select(Lote.producto_id, Lote.almacen_id, func.sum(Lote.cantidad_actual).label("total"))
        .group_by(Lote.producto_id, Lote.almacen_id)
        .subquery()
    )
    lotes = await session.execute(
        select(
            StockAlmacen.producto_id,
            StockAlmacen.almacen_id,
            StockAlmacen.cantidad,
            StockAlmacen.pendiente_lote,
            func.coalesce(suma_lotes.c.total, 0),
        )
        .join(Producto, Producto.id == StockAlmacen.producto_id)
        .outerjoin(
            suma_lotes,
            and_(
                suma_lotes.c.producto_id == StockAlmacen.producto_id, suma_lotes.c.almacen_id == StockAlmacen.almacen_id
            ),
        )
        .where(
            Producto.maneja_lotes.is_(True),
            func.coalesce(suma_lotes.c.total, 0) - StockAlmacen.pendiente_lote != StockAlmacen.cantidad,
        )
    )
    for pid, aid, cantidad, pendiente, total in lotes.tuples():
        agregar("stock_vs_lotes", pid, aid, f"Stock {cantidad}, lotes {total}, pendiente de lote {pendiente}")

    sin_lotes = await session.execute(
        select(StockAlmacen.producto_id, StockAlmacen.almacen_id)
        .join(Producto, Producto.id == StockAlmacen.producto_id)
        .where(Producto.maneja_lotes.is_(False), StockAlmacen.pendiente_lote != 0)
    )
    for pid, aid in sin_lotes.tuples():
        agregar("pendiente_sin_lotes", pid, aid, "Tiene unidades pendientes de lote pero no maneja lotes")

    revisados = await session.scalar(select(func.count(StockAlmacen.id)))
    return {"correcto": not problemas, "revisados": int(revisados or 0), "problemas": problemas}


async def registrar_revision(session: AsyncSession, ctx: ContextoUsuario, reporte: dict[str, Any]) -> None:
    auditoria.registrar(
        session,
        accion="REVISAR_INTEGRIDAD",
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        descripcion="Revisión de integridad del stock: "
        + ("sin problemas" if reporte["correcto"] else f"{len(reporte['problemas'])} problema(s)"),
        ip=ctx.ip,
    )
    await session.commit()
