"""Ventas del punto de venta (ticket interno T001) y su anulación.

Una venta es UNA transacción: turno de caja (FOR SHARE) -> productos y stock (FOR UPDATE, en orden) -> lotes ->
cliente -> serie del comprobante. Si algo falla (stock, precio cambiado, pagos que no cuadran) no queda nada.

- El servidor recalcula todo (precios, descuentos, IGV, ICBPER, redondeo) y lo compara con lo que vio el cajero:
  si el precio de un producto cambió o el total no coincide, la venta se rechaza para no cobrar otro monto.
- Descuento mayor al permitido, venta sin stock, fiado y anulación sin permiso: con la clave de un supervisor
  (servicio `autorizaciones`), que queda en la auditoría.
- La anulación solo se hace mientras el turno de caja de la venta sigue abierto (el arqueo de un turno cerrado no
  cambia); después corresponde una devolución.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.excepciones import Conflicto, NoEncontrado, ValidacionNegocio
from app.dependencies.auth import ContextoUsuario
from app.models import (
    Caja,
    Categoria,
    Cliente,
    CuentaPorCobrar,
    DetalleVenta,
    Empresa,
    MovimientoInventario,
    PagoVenta,
    Producto,
    ProductoPresentacion,
    SerieComprobante,
    SesionCaja,
    StockAlmacen,
    Sucursal,
    Venta,
)
from app.models.base import CERO
from app.models.enums import (
    EstadoCuenta,
    EstadoSesionCaja,
    EstadoVenta,
    MetodoPago,
    TipoAfectacionIGV,
    TipoComprobante,
    TipoMovimientoInventario,
)
from app.schemas.ventas import AnulacionEntrada, VentaCrear
from app.services import auditoria, caja, imagenes, parametros, stock, transacciones
from app.services.autorizaciones import Autorizador
from app.services.inventario import nombres_usuarios
from app.services.productos import almacen_venta_id
from app.utils.paginacion import ParametrosPaginacion, paginar
from app.utils.zona_horaria import a_local, a_utc, ahora_utc, hoy_local, inicio_de_hoy_utc

MODULO = "ventas"
DOS = Decimal("0.01")
CIEN = Decimal("100")


def r2(valor: Decimal) -> Decimal:
    return valor.quantize(DOS, rounding=ROUND_HALF_UP)


def comprobante(venta: Venta) -> str:
    return f"{venta.serie}-{venta.numero:08d}"


# --- Cálculo (función pura: el POS hace exactamente lo mismo en el navegador) -------------------------------


@dataclass(slots=True)
class LineaCalculo:
    cantidad: Decimal
    precio: Decimal
    descuento: Decimal  # de la línea, en soles
    afectacion: TipoAfectacionIGV
    bolsas: Decimal = CERO  # unidades afectas al ICBPER (bolsas plásticas)
    # Resultado
    descuento_total: Decimal = CERO  # de la línea + su parte del descuento global
    base: Decimal = CERO
    igv: Decimal = CERO
    icbper: Decimal = CERO
    total: Decimal = CERO


@dataclass(slots=True)
class Calculo:
    lineas: list[LineaCalculo]
    bruto: Decimal = CERO
    descuento: Decimal = CERO
    op_gravadas: Decimal = CERO
    op_exoneradas: Decimal = CERO
    op_inafectas: Decimal = CERO
    igv: Decimal = CERO
    icbper: Decimal = CERO
    total: Decimal = CERO


def calcular(
    lineas: list[LineaCalculo],
    descuento_global: Decimal,
    igv_porcentaje: Decimal,
    icbper_monto: Decimal,
    precios_incluyen_igv: bool = True,
) -> Calculo:
    """Totales de la venta. El descuento global se reparte entre las líneas en proporción a su importe
    (así cada línea conserva su afectación al IGV); los céntimos que sobran van a la línea más grande."""
    tasa = igv_porcentaje / CIEN
    netos = []
    bruto_total = CERO
    for linea in lineas:
        bruto = r2(linea.cantidad * linea.precio)
        if linea.descuento > bruto:
            raise ValidacionNegocio("El descuento de una línea no puede ser mayor que su importe", codigo="descuento")
        bruto_total += bruto
        netos.append(bruto - linea.descuento)
    suma_netos = sum(netos, CERO)
    if descuento_global > suma_netos:
        raise ValidacionNegocio("El descuento no puede ser mayor que el total", codigo="descuento")

    partes = [CERO] * len(lineas)
    if descuento_global > 0 and suma_netos > 0:
        for i, neto in enumerate(netos):
            partes[i] = r2(descuento_global * neto / suma_netos)
        mayor = max(range(len(netos)), key=lambda i: netos[i])
        partes[mayor] += descuento_global - sum(partes, CERO)

    calculo = Calculo(lineas=lineas, bruto=bruto_total)
    for linea, neto, parte in zip(lineas, netos, partes, strict=True):
        importe = neto - parte
        linea.descuento_total = linea.descuento + parte
        if linea.afectacion == TipoAfectacionIGV.GRAVADO:
            if precios_incluyen_igv:
                linea.base = r2(importe / (1 + tasa))
                linea.igv = importe - linea.base
            else:
                linea.base = importe
                linea.igv = r2(importe * tasa)
            calculo.op_gravadas += linea.base
        else:
            linea.base = importe
            linea.igv = CERO
            if linea.afectacion == TipoAfectacionIGV.EXONERADO:
                calculo.op_exoneradas += importe
            else:
                calculo.op_inafectas += importe
        linea.icbper = r2(linea.bolsas * icbper_monto)
        linea.total = linea.base + linea.igv + linea.icbper
        calculo.igv += linea.igv
        calculo.icbper += linea.icbper
        calculo.descuento += linea.descuento_total
        calculo.total += linea.total
    return calculo


def a_cobrar(total: Decimal, paso: Decimal, solo_efectivo: bool) -> Decimal:
    """Monto a cobrar: con pago solo en efectivo y redondeo configurado, se redondea a favor del cliente."""
    if paso <= 0 or not solo_efectivo:
        return total
    return (total / paso).to_integral_value(rounding=ROUND_DOWN) * paso


# --- Catálogo del POS -------------------------------------------------------------------------------------


async def configuracion(session: AsyncSession, ctx: ContextoUsuario) -> dict[str, Any]:
    empresa = await session.get(Empresa, 1)
    serie = await session.scalar(
        select(SerieComprobante.serie).where(
            SerieComprobante.sucursal_id == ctx.sucursal_id,
            SerieComprobante.tipo_comprobante == TipoComprobante.TICKET,
            SerieComprobante.predeterminada.is_(True),
            SerieComprobante.activo.is_(True),
        )
    )
    return {
        "igv_porcentaje": empresa.igv_porcentaje,
        "icbper_monto": empresa.icbper_monto,
        "precios_incluyen_igv": empresa.precios_incluyen_igv,
        "redondeo_efectivo": Decimal(str(await parametros.obtener(session, "ventas.redondeo_efectivo"))),
        "descuento_maximo": Decimal(str(await parametros.obtener(session, "ventas.descuento_maximo_cajero"))),
        "simbolo_moneda": empresa.simbolo_moneda,
        "serie": serie,
        "almacen_id": await almacen_venta_id(session, ctx.sucursal_id),
    }


async def catalogo(session: AsyncSession, ctx: ContextoUsuario) -> dict[str, Any]:
    """Todos los productos activos con sus códigos, presentaciones y stock del almacén de venta: el POS los
    guarda en memoria y busca/escanea sin ir al servidor."""
    config = await configuracion(session, ctx)
    almacen_id = config["almacen_id"]
    stock_col = (
        select(StockAlmacen.cantidad)
        .where(StockAlmacen.producto_id == Producto.id, StockAlmacen.almacen_id == almacen_id)
        .scalar_subquery()
    )
    filas = await session.execute(
        select(Producto, func.coalesce(stock_col, 0), Categoria.nombre, Categoria.color)
        .outerjoin(Categoria, Categoria.id == Producto.categoria_id)
        .where(Producto.activo.is_(True))
        .order_by(Producto.nombre)
        .options(selectinload(Producto.codigos), selectinload(Producto.presentaciones))
    )
    productos = []
    for p, cantidad, categoria, color in filas.unique().tuples():
        _, miniatura = imagenes.urls(p.imagen)
        productos.append(
            {
                "id": p.id,
                "nombre": p.nombre,
                "codigos": [c.codigo for c in p.codigos if c.presentacion_id is None],
                "codigo_interno": p.codigo_interno,
                "precio": p.precio_venta,
                "unidad_medida": p.unidad_medida,
                "permite_decimales": p.permite_decimales,
                "maneja_lotes": p.maneja_lotes,
                "afecto_icbper": p.afecto_icbper,
                "tipo_afectacion_igv": p.tipo_afectacion_igv,
                "stock": Decimal(cantidad),
                "categoria_id": p.categoria_id,
                "categoria": categoria,
                "categoria_color": color,
                "miniatura_url": miniatura,
                "presentaciones": [
                    {
                        "id": pr.id,
                        "nombre": pr.nombre,
                        "factor": pr.factor,
                        "precio": pr.precio_venta,
                        "codigos": [c.codigo for c in p.codigos if c.presentacion_id == pr.id],
                    }
                    for pr in p.presentaciones
                    if pr.activo
                ],
            }
        )
    return {"configuracion": config, "productos": productos}


# --- Registrar venta --------------------------------------------------------------------------------------


@dataclass(slots=True)
class _Linea:
    producto: Producto
    presentacion: ProductoPresentacion | None
    cantidad: Decimal
    precio: Decimal
    calculo: LineaCalculo

    @property
    def factor(self) -> Decimal:
        return self.presentacion.factor if self.presentacion else Decimal("1")

    @property
    def unidades(self) -> Decimal:
        return self.cantidad * self.factor

    @property
    def descripcion(self) -> str:
        return f"{self.producto.nombre} · {self.presentacion.nombre}" if self.presentacion else self.producto.nombre


async def _disponible_vigente(session: AsyncSession, producto: Producto, fila: StockAlmacen) -> Decimal:
    """Lo que se puede vender sin quedar en negativo (en productos con lotes, solo lotes no vencidos)."""
    if not producto.maneja_lotes:
        return max(fila.cantidad, CERO)
    hoy = hoy_local()
    lotes = await stock.lotes_disponibles(session, producto.id, fila.almacen_id)
    return sum((lt.cantidad_actual for lt in lotes if not lt.fecha_vencimiento or lt.fecha_vencimiento >= hoy), CERO)


async def _sacar(
    session: AsyncSession, ctx: ContextoUsuario, linea: _Linea, fila: StockAlmacen, venta: Venta, permitir: bool
) -> None:
    """Saca del stock las unidades de una línea: por lotes en orden FEFO (sin vencidos) y, si se autorizó vender
    sin stock, el resto queda en negativo / pendiente de lote."""
    comun = {
        "tipo": TipoMovimientoInventario.SALIDA_VENTA,
        "costo_unitario": linea.producto.precio_costo,
        "usuario_id": ctx.usuario_id,
        "referencia_tipo": "venta",
        "referencia_id": venta.id,
        "motivo": f"Venta {comprobante(venta)}",
    }
    producto = linea.producto
    restante = linea.unidades
    if producto.maneja_lotes:
        hoy = hoy_local()
        for lote in await stock.lotes_disponibles(session, producto.id, fila.almacen_id):
            if restante <= 0:
                break
            if lote.fecha_vencimiento and lote.fecha_vencimiento < hoy:
                continue  # un lote vencido no se vende
            toma = min(lote.cantidad_actual, restante)
            stock.mover(session, producto=producto, stock=fila, cantidad=-toma, lote=lote, **comun)
            restante -= toma
    if restante > 0:
        stock.mover(session, producto=producto, stock=fila, cantidad=-restante, permitir_negativo=permitir, **comun)


async def _serie(session: AsyncSession, sucursal_id: int) -> SerieComprobante:
    serie = await session.scalar(
        select(SerieComprobante)
        .where(
            SerieComprobante.sucursal_id == sucursal_id,
            SerieComprobante.tipo_comprobante == TipoComprobante.TICKET,
            SerieComprobante.predeterminada.is_(True),
            SerieComprobante.activo.is_(True),
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if serie is None:
        raise ValidacionNegocio("La sucursal no tiene una serie de tickets configurada", codigo="sin_serie")
    return serie


async def _credito(session: AsyncSession, cliente_id: int | None, monto: Decimal) -> Cliente:
    if cliente_id is None:
        raise ValidacionNegocio("Elija el cliente al que se le fía", codigo="cliente_requerido")
    cliente = await session.scalar(
        select(Cliente).where(Cliente.id == cliente_id).with_for_update().execution_options(populate_existing=True)
    )
    if cliente is None or not cliente.activo:
        raise ValidacionNegocio("El cliente no existe o está inactivo", codigo="cliente_invalido")
    if not cliente.permite_credito:
        raise ValidacionNegocio(f"A {cliente.nombre} no se le puede fiar", codigo="cliente_sin_credito")
    if cliente.limite_credito > 0:
        deuda = await session.scalar(
            select(func.coalesce(func.sum(CuentaPorCobrar.saldo), 0)).where(
                CuentaPorCobrar.cliente_id == cliente.id,
                CuentaPorCobrar.estado.in_([EstadoCuenta.PENDIENTE, EstadoCuenta.PARCIAL]),
            )
        )
        if Decimal(deuda) + monto > cliente.limite_credito:
            disponible = max(cliente.limite_credito - Decimal(deuda), CERO)
            raise ValidacionNegocio(
                f"{cliente.nombre} supera su límite de fiado: le quedan S/ {disponible:.2f}",
                codigo="limite_credito",
                datos={"disponible": str(disponible)},
            )
    return cliente


async def registrar(session: AsyncSession, ctx: ContextoUsuario, datos: VentaCrear, clave: str) -> int:
    async def accion() -> int:
        autorizador = Autorizador(session, ctx, datos.autorizaciones)
        turno = await caja.exigir_turno(session, ctx)
        almacen_id = await almacen_venta_id(session, ctx.sucursal_id)
        if almacen_id is None:
            raise ValidacionNegocio("La sucursal no tiene almacén de venta", codigo="sin_almacen")

        bloqueo = await stock.bloquear(session, [i.producto_id for i in datos.items], [almacen_id])
        ids_presentacion = {i.presentacion_id for i in datos.items if i.presentacion_id}
        presentaciones = {
            p.id: p
            for p in await session.scalars(
                select(ProductoPresentacion).where(ProductoPresentacion.id.in_(ids_presentacion))
            )
        } if ids_presentacion else {}

        empresa = await session.get(Empresa, 1)
        lineas: list[_Linea] = []
        for item in datos.items:
            producto = bloqueo.productos[item.producto_id]
            if not producto.activo:
                raise ValidacionNegocio(f"«{producto.nombre}» está inactivo", codigo="producto_inactivo")
            presentacion = None
            if item.presentacion_id is not None:
                presentacion = presentaciones.get(item.presentacion_id)
                if presentacion is None or presentacion.producto_id != producto.id or not presentacion.activo:
                    raise ValidacionNegocio(
                        f"La presentación no corresponde a «{producto.nombre}»", codigo="presentacion_invalida"
                    )
                if item.cantidad != item.cantidad.to_integral_value():
                    raise ValidacionNegocio(
                        f"«{presentacion.nombre}» se vende por unidades enteras", codigo="cantidad_no_entera"
                    )
            else:
                stock.validar_cantidad(producto, item.cantidad)
            precio = presentacion.precio_venta if presentacion else producto.precio_venta
            if precio <= 0:
                raise ValidacionNegocio(f"«{producto.nombre}» no tiene precio de venta", codigo="sin_precio")
            if precio != item.precio_unitario:
                raise Conflicto(
                    f"El precio de «{producto.nombre}» cambió a S/ {precio:.2f}: revise la venta",
                    codigo="precio_cambiado",
                    datos={"producto_id": producto.id, "presentacion_id": item.presentacion_id, "precio": str(precio)},
                )
            factor = presentacion.factor if presentacion else Decimal("1")
            lineas.append(
                _Linea(
                    producto,
                    presentacion,
                    item.cantidad,
                    precio,
                    LineaCalculo(
                        cantidad=item.cantidad,
                        precio=precio,
                        descuento=item.descuento,
                        afectacion=producto.tipo_afectacion_igv,
                        bolsas=item.cantidad * factor if producto.afecto_icbper else CERO,
                    ),
                )
            )

        calculo = calcular(
            [linea.calculo for linea in lineas],
            datos.descuento,
            empresa.igv_porcentaje,
            empresa.icbper_monto,
            empresa.precios_incluyen_igv,
        )
        if calculo.descuento > 0:
            maximo = Decimal(str(await parametros.obtener(session, "ventas.descuento_maximo_cajero")))
            porcentaje = calculo.descuento / calculo.bruto * CIEN if calculo.bruto else CIEN
            if porcentaje > maximo:
                await autorizador.exigir(
                    "pos.aplicar_descuento",
                    f"El descuento ({porcentaje.quantize(Decimal('0.1'))}%) supera el {maximo.normalize():f}% "
                    "permitido: necesita la autorización de un supervisor",
                    "descuento_no_autorizado",
                )

        # Cobro: montos, vuelto y redondeo
        paso = Decimal(str(await parametros.obtener(session, "ventas.redondeo_efectivo")))
        solo_efectivo = all(p.metodo == MetodoPago.EFECTIVO for p in datos.pagos)
        cobrar = a_cobrar(calculo.total, paso, solo_efectivo)
        if datos.total != cobrar:
            raise Conflicto(
                f"El total cambió a S/ {cobrar:.2f}: revise la venta",
                codigo="total_distinto",
                datos={"total": str(cobrar)},
            )
        if sum((p.monto for p in datos.pagos), CERO) != cobrar:
            raise ValidacionNegocio("Los pagos no suman el total de la venta", codigo="pagos_no_cuadran")
        vuelto = sum(
            ((p.monto_recibido - p.monto) for p in datos.pagos if p.monto_recibido is not None), CERO
        )
        if vuelto > 0 and vuelto >= cobrar + 1000:
            raise ValidacionNegocio("Revise el monto recibido", codigo="recibido_excesivo")

        fiado = next((p for p in datos.pagos if p.metodo == MetodoPago.CREDITO), None)
        cliente = None
        if fiado is not None:
            await autorizador.exigir(
                "pos.venta_credito", "Vender al fiado necesita la autorización de un supervisor", "fiado_no_autorizado"
            )
            cliente = await _credito(session, datos.cliente_id, fiado.monto)
        elif datos.cliente_id is not None:
            cliente = await session.get(Cliente, datos.cliente_id)
            if cliente is None or not cliente.activo:
                raise ValidacionNegocio("El cliente no existe o está inactivo", codigo="cliente_invalido")

        # Stock: lo que se pide por producto contra lo que hay (lotes vencidos no cuentan)
        pedido: dict[int, Decimal] = defaultdict(lambda: CERO)
        for linea in lineas:
            pedido[linea.producto.id] += linea.unidades
        sin_stock: list[str] = []
        for producto_id in sorted(pedido):
            producto = bloqueo.productos[producto_id]
            disponible = await _disponible_vigente(session, producto, bloqueo.stock(producto_id, almacen_id))
            if pedido[producto_id] > disponible:
                sin_stock.append(f"«{producto.nombre}» (hay {stock.fmt(disponible)})")
        if sin_stock:
            await autorizador.exigir(
                "pos.vender_sin_stock",
                "Stock insuficiente de " + ", ".join(sin_stock[:3]) + ("…" if len(sin_stock) > 3 else ""),
                "stock_insuficiente",
                productos=sin_stock,
            )

        serie = await _serie(session, ctx.sucursal_id)
        serie.correlativo_actual += 1
        venta = Venta(
            sucursal_id=ctx.sucursal_id,
            almacen_id=almacen_id,
            tipo_comprobante=TipoComprobante.TICKET,
            serie=serie.serie,
            numero=serie.correlativo_actual,
            fecha=ahora_utc(),
            sesion_caja_id=turno.id,
            usuario_id=ctx.usuario_id,
            cliente_id=cliente.id if cliente else None,
            op_gravadas=calculo.op_gravadas,
            op_exoneradas=calculo.op_exoneradas,
            op_inafectas=calculo.op_inafectas,
            igv=calculo.igv,
            icbper=calculo.icbper,
            descuento=calculo.descuento,
            total=calculo.total,
            redondeo=cobrar - calculo.total,
            vuelto=vuelto,
            es_credito=fiado is not None,
            observaciones=datos.observaciones,
        )
        venta.detalles = [
            DetalleVenta(
                producto_id=linea.producto.id,
                presentacion_id=linea.presentacion.id if linea.presentacion else None,
                descripcion=linea.descripcion[:200],
                cantidad=linea.cantidad,
                factor=linea.factor,
                precio_unitario=linea.precio,
                costo_unitario=linea.producto.precio_costo,
                descuento=linea.calculo.descuento_total,
                tipo_afectacion_igv=linea.producto.tipo_afectacion_igv,
                igv=linea.calculo.igv,
                icbper=linea.calculo.icbper,
                total=linea.calculo.total,
            )
            for linea in lineas
        ]
        venta.pagos = [
            PagoVenta(metodo=p.metodo, monto=p.monto, monto_recibido=p.monto_recibido, referencia=p.referencia)
            for p in datos.pagos
        ]
        session.add(venta)
        await session.flush()

        permitir = bool(sin_stock)
        for linea in sorted(lineas, key=lambda x: x.producto.id):
            await _sacar(session, ctx, linea, bloqueo.stock(linea.producto.id, almacen_id), venta, permitir)

        if fiado is not None:
            dias = await parametros.obtener(session, "clientes.dias_credito_defecto")
            session.add(
                CuentaPorCobrar(
                    venta_id=venta.id,
                    cliente_id=cliente.id,
                    monto_total=fiado.monto,
                    saldo=fiado.monto,
                    fecha_vencimiento=hoy_local() + timedelta(days=int(dias)),
                )
            )

        for a in autorizador.usadas:
            auditoria.registrar(
                session,
                accion="AUTORIZAR",
                modulo=MODULO,
                usuario_id=a.supervisor_id,
                sucursal_id=ctx.sucursal_id,
                entidad="venta",
                entidad_id=venta.id,
                descripcion=f"{a.supervisor} autorizó «{a.permiso}» en la venta {comprobante(venta)} de "
                f"{ctx.nombre}",
                datos={"permiso": a.permiso, "cajero_id": ctx.usuario_id},
                ip=ctx.ip,
            )
        if fiado is not None:
            auditoria.registrar(
                session,
                accion="FIAR",
                modulo=MODULO,
                usuario_id=ctx.usuario_id,
                sucursal_id=ctx.sucursal_id,
                entidad="venta",
                entidad_id=venta.id,
                descripcion=f"Fió S/ {fiado.monto:.2f} a {cliente.nombre} ({comprobante(venta)})",
                ip=ctx.ip,
            )
        return venta.id

    return await transacciones.ejecutar(session, accion, usuario_id=ctx.usuario_id, operacion="venta", clave=clave)


# --- Anular -----------------------------------------------------------------------------------------------


async def anular(
    session: AsyncSession, ctx: ContextoUsuario, venta_id: int, datos: AnulacionEntrada, clave: str | None
) -> int:
    async def accion() -> int:
        autorizador = Autorizador(session, ctx, [datos.autorizacion] if datos.autorizacion else [])
        venta = await session.scalar(
            select(Venta)
            .where(Venta.id == venta_id)
            .with_for_update(of=Venta)
            .options(selectinload(Venta.detalles))
            .execution_options(populate_existing=True)
        )
        if venta is None or venta.sucursal_id != ctx.sucursal_id:
            raise NoEncontrado("La venta no existe")
        if venta.estado == EstadoVenta.ANULADA:
            raise Conflicto(f"La venta {comprobante(venta)} ya está anulada", codigo="ya_anulada")
        if venta.estado != EstadoVenta.COMPLETADA:
            raise Conflicto("Una venta con devoluciones no se puede anular", codigo="estado_invalido")
        turno = await session.scalar(
            select(SesionCaja)
            .where(SesionCaja.id == venta.sesion_caja_id)
            .with_for_update(read=True, of=SesionCaja)
            .execution_options(populate_existing=True)
        )
        if turno.estado != EstadoSesionCaja.ABIERTA:
            raise ValidacionNegocio(
                "El turno de caja de esta venta ya se cerró: registre una devolución", codigo="turno_cerrado"
            )
        autorizacion = await autorizador.exigir(
            "pos.anular_venta", "Anular una venta necesita la autorización de un supervisor", "anulacion_no_autorizada"
        )

        movimientos = list(
            await session.scalars(
                select(MovimientoInventario)
                .where(
                    MovimientoInventario.referencia_tipo == "venta",
                    MovimientoInventario.referencia_id == venta.id,
                    MovimientoInventario.tipo == TipoMovimientoInventario.SALIDA_VENTA,
                )
                .order_by(MovimientoInventario.producto_id, MovimientoInventario.id)
            )
        )
        bloqueo = await stock.bloquear(session, [m.producto_id for m in movimientos], [venta.almacen_id])
        motivo = f"Anulación {comprobante(venta)}"
        for m in movimientos:
            producto = bloqueo.productos[m.producto_id]
            fila = bloqueo.stock(m.producto_id, venta.almacen_id)
            comun = {
                "tipo": TipoMovimientoInventario.ANULACION_VENTA,
                "costo_unitario": m.costo_unitario,
                "usuario_id": ctx.usuario_id,
                "referencia_tipo": "venta",
                "referencia_id": venta.id,
                "motivo": motivo,
            }
            if m.lote_id is not None:
                lote = await stock.bloquear_lote(session, m.lote_id, m.producto_id, venta.almacen_id)
                stock.mover(session, producto=producto, stock=fila, cantidad=-m.cantidad, lote=lote, **comun)
            elif producto.maneja_lotes:
                await stock.reingresar_sin_lote(session, producto=producto, stock=fila, cantidad=-m.cantidad, **comun)
            else:
                stock.mover(session, producto=producto, stock=fila, cantidad=-m.cantidad, **comun)

        if venta.es_credito:
            cuenta = await session.scalar(
                select(CuentaPorCobrar).where(CuentaPorCobrar.venta_id == venta.id).with_for_update()
            )
            if cuenta is not None:
                if cuenta.saldo != cuenta.monto_total:
                    raise ValidacionNegocio(
                        "El cliente ya abonó a esta deuda: no se puede anular la venta", codigo="fiado_con_abonos"
                    )
                cuenta.saldo = CERO
                cuenta.estado = EstadoCuenta.ANULADA

        venta.estado = EstadoVenta.ANULADA
        venta.anulada_por_id = ctx.usuario_id
        venta.fecha_anulacion = ahora_utc()
        venta.motivo_anulacion = datos.motivo + (f" (autorizó {autorizacion.supervisor})" if autorizacion else "")
        venta.motivo_anulacion = venta.motivo_anulacion[:300]
        auditoria.registrar(
            session,
            accion="ANULAR",
            modulo=MODULO,
            usuario_id=ctx.usuario_id,
            sucursal_id=ctx.sucursal_id,
            entidad="venta",
            entidad_id=venta.id,
            descripcion=f"Anuló la venta {comprobante(venta)} (S/ {venta.total + venta.redondeo:.2f}): {datos.motivo}"
            + (f" — autorizó {autorizacion.supervisor}" if autorizacion else ""),
            datos={"autorizo_id": autorizacion.supervisor_id} if autorizacion else None,
            ip=ctx.ip,
        )
        return venta.id

    return await transacciones.ejecutar(
        session, accion, usuario_id=ctx.usuario_id, operacion="anular_venta", clave=clave
    )


# --- Consultas --------------------------------------------------------------------------------------------


def _visibles(ctx: ContextoUsuario):
    consulta = select(Venta).where(Venta.sucursal_id == ctx.sucursal_id)
    if not ctx.tiene(caja.VER_TODAS):
        consulta = consulta.where(Venta.usuario_id == ctx.usuario_id)
    return consulta


async def _caja_por_sesion(session: AsyncSession, sesion_ids: set[int]) -> dict[int, tuple[str, bool]]:
    if not sesion_ids:
        return {}
    filas = await session.execute(
        select(SesionCaja.id, Caja.nombre, SesionCaja.estado)
        .join(Caja, Caja.id == SesionCaja.caja_id)
        .where(SesionCaja.id.in_(sesion_ids))
    )
    return {i: (n, e == EstadoSesionCaja.ABIERTA) for i, n, e in filas.tuples()}


def _listado(venta: Venta, nombres: dict[int, str], cajas: dict[int, tuple[str, bool]]) -> dict[str, Any]:
    return {
        "id": venta.id,
        "comprobante": comprobante(venta),
        "tipo_comprobante": venta.tipo_comprobante,
        "fecha": venta.fecha,
        "usuario": nombres.get(venta.usuario_id, "—"),
        "cliente": venta.cliente.nombre if venta.cliente else None,
        "caja": cajas.get(venta.sesion_caja_id, ("—", False))[0],
        "items": len(venta.detalles),
        "total": venta.total,
        "a_cobrar": venta.total + venta.redondeo,
        "metodos": list(dict.fromkeys(p.metodo for p in venta.pagos)),
        "estado": venta.estado,
    }


async def listar(
    session: AsyncSession,
    ctx: ContextoUsuario,
    params: ParametrosPaginacion,
    *,
    sesion_caja_id: int | None,
    usuario_id: int | None,
    estado: EstadoVenta | None,
    metodo: MetodoPago | None,
    busqueda: str | None,
    desde,
    hasta,
) -> tuple[list[dict[str, Any]], int]:
    consulta = _visibles(ctx).options(
        selectinload(Venta.detalles), selectinload(Venta.pagos), selectinload(Venta.cliente)
    )
    if sesion_caja_id:
        consulta = consulta.where(Venta.sesion_caja_id == sesion_caja_id)
    if usuario_id:
        consulta = consulta.where(Venta.usuario_id == usuario_id)
    if estado:
        consulta = consulta.where(Venta.estado == estado)
    if metodo:
        consulta = consulta.where(Venta.pagos.any(PagoVenta.metodo == metodo))
    if busqueda:
        texto = busqueda.strip().upper()
        numero = texto.rsplit("-", 1)[-1].lstrip("0")
        condiciones = [Venta.cliente.has(Cliente.nombre.contains(busqueda.strip()))]
        if numero.isdigit():
            condiciones.append(Venta.numero == int(numero))
        consulta = consulta.where(or_(*condiciones))
    if desde:
        consulta = consulta.where(Venta.fecha >= a_utc(datetime.combine(desde, time.min)))
    if hasta:
        consulta = consulta.where(Venta.fecha < a_utc(datetime.combine(hasta + timedelta(days=1), time.min)))
    consulta = consulta.order_by(Venta.fecha.desc(), Venta.id.desc())
    ventas, total = await paginar(session, consulta, params)
    nombres = await nombres_usuarios(session, [v.usuario_id for v in ventas])
    cajas = await _caja_por_sesion(session, {v.sesion_caja_id for v in ventas})
    return [_listado(v, nombres, cajas) for v in ventas], total


async def detalle(session: AsyncSession, ctx: ContextoUsuario, venta_id: int) -> dict[str, Any]:
    venta = await session.scalar(
        _visibles(ctx)
        .where(Venta.id == venta_id)
        .options(selectinload(Venta.detalles), selectinload(Venta.pagos), selectinload(Venta.cliente))
    )
    if venta is None:
        raise NoEncontrado("La venta no existe")
    nombres = await nombres_usuarios(session, [venta.usuario_id, venta.anulada_por_id])
    cajas = await _caja_por_sesion(session, {venta.sesion_caja_id})
    empresa = await session.get(Empresa, 1)
    sucursal = await session.get(Sucursal, venta.sucursal_id)
    turno_abierto = cajas.get(venta.sesion_caja_id, ("", False))[1]
    return {
        **_listado(venta, nombres, cajas),
        "sesion_caja_id": venta.sesion_caja_id,
        "cliente_documento": venta.cliente.numero_documento if venta.cliente else None,
        "op_gravadas": venta.op_gravadas,
        "op_exoneradas": venta.op_exoneradas,
        "op_inafectas": venta.op_inafectas,
        "igv": venta.igv,
        "igv_porcentaje": empresa.igv_porcentaje,
        "icbper": venta.icbper,
        "descuento": venta.descuento,
        "redondeo": venta.redondeo,
        "vuelto": venta.vuelto,
        "es_credito": venta.es_credito,
        "observaciones": venta.observaciones,
        "detalles": [
            {
                "id": d.id,
                "producto_id": d.producto_id,
                "presentacion_id": d.presentacion_id,
                "descripcion": d.descripcion,
                "cantidad": d.cantidad,
                "factor": d.factor,
                "precio_unitario": d.precio_unitario,
                "descuento": d.descuento,
                "tipo_afectacion_igv": d.tipo_afectacion_igv,
                "igv": d.igv,
                "icbper": d.icbper,
                "total": d.total,
            }
            for d in sorted(venta.detalles, key=lambda d: d.id)
        ],
        "pagos": [
            {"metodo": p.metodo, "monto": p.monto, "monto_recibido": p.monto_recibido, "referencia": p.referencia}
            for p in venta.pagos
        ],
        "anulada_por": nombres.get(venta.anulada_por_id) if venta.anulada_por_id else None,
        "fecha_anulacion": venta.fecha_anulacion,
        "motivo_anulacion": venta.motivo_anulacion,
        "puede_anular": venta.estado == EstadoVenta.COMPLETADA and turno_abierto,
        "empresa": {
            "ruc": empresa.ruc,
            "razon_social": empresa.razon_social,
            "nombre_comercial": empresa.nombre_comercial,
            "direccion": empresa.direccion_fiscal,
            "telefono": empresa.telefono,
            "mensaje_ticket": empresa.mensaje_ticket,
            "sucursal": sucursal.nombre,
            "direccion_sucursal": sucursal.direccion,
        },
    }



async def resumen_hoy(session: AsyncSession, ctx: ContextoUsuario) -> dict[str, Any]:
    """Ventas de hoy (hora de Lima) para el Inicio: total, tickets, promedio, por método y por hora.
    Las anuladas no cuentan. El cajero ve las suyas; con `caja.ver_todas`, las de toda la sucursal."""
    desde = inicio_de_hoy_utc()
    ventas = list(
        await session.scalars(
            _visibles(ctx)
            .where(Venta.fecha >= desde, Venta.estado != EstadoVenta.ANULADA)
            .options(selectinload(Venta.pagos))
        )
    )
    por_hora: dict[int, Decimal] = defaultdict(lambda: CERO)
    por_metodo: dict[MetodoPago, Decimal] = defaultdict(lambda: CERO)
    total = CERO
    for v in ventas:
        cobrado = v.total + v.redondeo
        total += cobrado
        por_hora[a_local(v.fecha).hour] += cobrado
        for p in v.pagos:
            por_metodo[p.metodo] += p.monto
    return {
        "total": total,
        "tickets": len(ventas),
        "promedio": r2(total / len(ventas)) if ventas else None,
        "por_metodo": {m.value: str(por_metodo.get(m, CERO)) for m in MetodoPago},
        "por_hora": [{"hora": h, "total": str(por_hora[h])} for h in sorted(por_hora)],
    }
