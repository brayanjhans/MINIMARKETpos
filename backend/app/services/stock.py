"""Único punto del sistema que cambia el stock.

Reglas (todas las operaciones de inventario, compras y ventas pasan por aquí):
1. Orden fijo de bloqueo para evitar interbloqueos: primero las filas de `productos` (por id), luego
   `stock_almacen` (por producto, almacén) y al final los `lotes`. Como TODO cambio de stock bloquea antes la
   fila del producto, dos operaciones sobre el mismo producto nunca se cruzan.
2. Cada cambio deja un movimiento en el kardex (inmutable) con el stock anterior y el nuevo del almacén.
3. El stock de un almacén solo puede quedar negativo por una venta autorizada (`permitir_negativo`).
4. Los lotes nunca quedan negativos. Si el producto maneja lotes:
   suma(lotes.cantidad_actual) - stock.pendiente_lote = stock.cantidad
5. El costo promedio solo cambia con entradas de mercadería (compras, stock inicial).
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.core.excepciones import NoEncontrado, ValidacionNegocio
from app.models import (
    DetalleTransferencia,
    HistorialPrecio,
    Lote,
    MovimientoInventario,
    Producto,
    StockAlmacen,
    Transferencia,
)
from app.models.base import CERO
from app.models.enums import EstadoTransferencia, TipoMovimientoInventario, TipoPrecio
from app.utils.zona_horaria import hoy_local

CUATRO_DECIMALES = Decimal("0.0001")


def fmt(cantidad: Decimal) -> str:
    """Cantidad legible: 12 en vez de 12.000, 1.25 en vez de 1.250."""
    texto = f"{cantidad.normalize():f}"
    return texto


@dataclass(slots=True)
class Bloqueo:
    productos: dict[int, Producto]
    stocks: dict[tuple[int, int], StockAlmacen]

    def stock(self, producto_id: int, almacen_id: int) -> StockAlmacen:
        return self.stocks[(producto_id, almacen_id)]


async def bloquear(session: AsyncSession, producto_ids: Iterable[int], almacen_ids: Iterable[int]) -> Bloqueo:
    """Bloquea (FOR UPDATE) los productos y sus filas de stock en los almacenes indicados, creando las que falten."""
    pids = sorted(set(producto_ids))
    aids = sorted(set(almacen_ids))
    productos = {
        p.id: p
        for p in await session.scalars(
            select(Producto).where(Producto.id.in_(pids)).order_by(Producto.id).options(noload("*")).with_for_update()
        )
    }
    faltan = set(pids) - productos.keys()
    if faltan:
        raise NoEncontrado("Alguno de los productos no existe", datos={"producto_ids": sorted(faltan)})

    filas = [{"producto_id": p, "almacen_id": a} for p in pids for a in aids]
    if filas:
        consulta = insert(StockAlmacen).values(filas)
        await session.execute(consulta.on_duplicate_key_update(producto_id=consulta.inserted.producto_id))
    stocks = {
        (s.producto_id, s.almacen_id): s
        for s in await session.scalars(
            select(StockAlmacen)
            .where(StockAlmacen.producto_id.in_(pids), StockAlmacen.almacen_id.in_(aids))
            .order_by(StockAlmacen.producto_id, StockAlmacen.almacen_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    }
    return Bloqueo(productos=productos, stocks=stocks)


async def lotes_disponibles(session: AsyncSession, producto_id: int, almacen_id: int) -> list[Lote]:
    """Lotes con saldo, bloqueados, en orden FEFO (primero el que vence antes; sin fecha al final)."""
    return list(
        await session.scalars(
            select(Lote)
            .where(Lote.producto_id == producto_id, Lote.almacen_id == almacen_id, Lote.cantidad_actual > 0)
            .order_by(Lote.fecha_vencimiento.is_(None), Lote.fecha_vencimiento, Lote.id)
            .options(noload("*"))
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    )


async def bloquear_lote(session: AsyncSession, lote_id: int, producto_id: int, almacen_id: int) -> Lote:
    lote = await session.scalar(
        select(Lote)
        .where(Lote.id == lote_id)
        .options(noload("*"))
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if lote is None or lote.producto_id != producto_id or lote.almacen_id != almacen_id:
        raise ValidacionNegocio("El lote no corresponde a ese producto y almacén", codigo="lote_invalido")
    return lote


async def lote_para_entrada(
    session: AsyncSession,
    producto_id: int,
    almacen_id: int,
    numero_lote: str,
    fecha_vencimiento: date | None,
    costo_unitario: Decimal,
) -> Lote:
    """Lote donde entra mercadería: el existente con ese número en el almacén, o uno nuevo."""
    numero = numero_lote.strip().upper()
    lote = await session.scalar(
        select(Lote)
        .where(Lote.producto_id == producto_id, Lote.almacen_id == almacen_id, Lote.numero_lote == numero)
        .options(noload("*"))
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if lote is None:
        lote = Lote(
            producto_id=producto_id,
            almacen_id=almacen_id,
            numero_lote=numero,
            fecha_vencimiento=fecha_vencimiento,
            cantidad_inicial=CERO,
            cantidad_actual=CERO,
            costo_unitario=costo_unitario,
        )
        session.add(lote)
        await session.flush()
    elif fecha_vencimiento and lote.fecha_vencimiento and fecha_vencimiento != lote.fecha_vencimiento:
        raise ValidacionNegocio(
            f"El lote {numero} ya existe con otra fecha de vencimiento ({lote.fecha_vencimiento:%d/%m/%Y})",
            codigo="lote_vencimiento_distinto",
        )
    elif fecha_vencimiento and lote.fecha_vencimiento is None:
        lote.fecha_vencimiento = fecha_vencimiento
    lote.activo = True
    return lote


def validar_cantidad(producto: Producto, cantidad: Decimal) -> None:
    if not producto.permite_decimales and cantidad != cantidad.to_integral_value():
        raise ValidacionNegocio(
            f"«{producto.nombre}» se maneja en unidades enteras (no admite {fmt(cantidad)})",
            codigo="cantidad_no_entera",
        )


def mover(
    session: AsyncSession,
    *,
    producto: Producto,
    stock: StockAlmacen,
    cantidad: Decimal,
    tipo: TipoMovimientoInventario,
    costo_unitario: Decimal,
    usuario_id: int | None,
    referencia_tipo: str | None = None,
    referencia_id: int | None = None,
    motivo: str | None = None,
    lote: Lote | None = None,
    permitir_negativo: bool = False,
) -> MovimientoInventario | None:
    """Aplica un cambio de stock (positivo = entrada, negativo = salida) y lo registra en el kardex.

    Las filas de producto, stock y lote deben venir bloqueadas (`bloquear`, `lotes_disponibles`...).
    """
    if cantidad == 0:
        return None
    validar_cantidad(producto, abs(cantidad))

    if producto.maneja_lotes and lote is None and not (cantidad < 0 and permitir_negativo):
        # Solo una venta puede sacar unidades sin lote: quedan "pendientes de lote"
        raise ValidacionNegocio(f"Indique el lote de «{producto.nombre}»", codigo="lote_requerido")
    if not producto.maneja_lotes and lote is not None:
        raise ValidacionNegocio(f"«{producto.nombre}» no maneja lotes", codigo="lote_invalido")

    anterior = stock.cantidad
    nuevo = anterior + cantidad
    if cantidad < 0 and nuevo < 0 and not permitir_negativo:
        raise ValidacionNegocio(
            f"Stock insuficiente de «{producto.nombre}»: "
            f"hay {fmt(max(anterior, CERO))} y se necesitan {fmt(-cantidad)}",
            codigo="stock_insuficiente",
            datos={"producto_id": producto.id, "disponible": str(anterior), "requerido": str(-cantidad)},
        )

    if lote is not None:
        if cantidad > 0:
            # Lo vendido sin lote se descuenta primero de la mercadería que llega
            cubre = min(stock.pendiente_lote, cantidad)
            stock.pendiente_lote -= cubre
            lote.cantidad_actual += cantidad - cubre
            lote.cantidad_inicial += cantidad
        else:
            if lote.cantidad_actual + cantidad < 0:
                raise ValidacionNegocio(
                    f"El lote {lote.numero_lote} de «{producto.nombre}» solo tiene {fmt(lote.cantidad_actual)}",
                    codigo="lote_insuficiente",
                    datos={"lote_id": lote.id, "disponible": str(lote.cantidad_actual)},
                )
            lote.cantidad_actual += cantidad
    elif producto.maneja_lotes:
        stock.pendiente_lote += -cantidad

    stock.cantidad = nuevo
    movimiento = MovimientoInventario(
        producto_id=producto.id,
        almacen_id=stock.almacen_id,
        lote_id=lote.id if lote else None,
        tipo=tipo,
        cantidad=cantidad,
        stock_anterior=anterior,
        stock_nuevo=nuevo,
        costo_unitario=costo_unitario,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        motivo=motivo[:300] if motivo else None,
        usuario_id=usuario_id,
    )
    session.add(movimiento)
    return movimiento


async def salida_fefo(
    session: AsyncSession,
    *,
    producto: Producto,
    stock: StockAlmacen,
    cantidad: Decimal,
    **kwargs,
) -> list[tuple[Lote | None, Decimal]]:
    """Saca `cantidad` (positiva) repartiéndola entre lotes en orden FEFO. Devuelve [(lote, cantidad)]."""
    if not producto.maneja_lotes:
        mover(session, producto=producto, stock=stock, cantidad=-cantidad, **kwargs)
        return [(None, cantidad)]
    hoy = hoy_local()
    restante = cantidad
    usados: list[tuple[Lote | None, Decimal]] = []
    for lote in await lotes_disponibles(session, producto.id, stock.almacen_id):
        if restante <= 0:
            break
        if lote.fecha_vencimiento and lote.fecha_vencimiento < hoy:
            continue  # los vencidos no salen por FEFO: se dan de baja como merma
        toma = min(lote.cantidad_actual, restante)
        mover(session, producto=producto, stock=stock, cantidad=-toma, lote=lote, **kwargs)
        usados.append((lote, toma))
        restante -= toma
    if restante > 0:
        raise ValidacionNegocio(
            f"No hay suficiente stock en lotes vigentes de «{producto.nombre}» (faltan {fmt(restante)})",
            codigo="stock_insuficiente",
            datos={"producto_id": producto.id, "faltante": str(restante)},
        )
    return usados


async def existencia_total(session: AsyncSession, producto_id: int) -> Decimal:
    """Unidades valorizables del producto: stock positivo de todos los almacenes + lo que está en tránsito."""
    en_almacenes = await session.scalar(
        select(func.coalesce(func.sum(func.greatest(StockAlmacen.cantidad, 0)), 0)).where(
            StockAlmacen.producto_id == producto_id
        )
    )
    en_transito = await session.scalar(
        select(func.coalesce(func.sum(DetalleTransferencia.cantidad), 0))
        .join(Transferencia, Transferencia.id == DetalleTransferencia.transferencia_id)
        .where(
            DetalleTransferencia.producto_id == producto_id,
            Transferencia.estado == EstadoTransferencia.EN_TRANSITO,
        )
    )
    return Decimal(en_almacenes) + Decimal(en_transito)


async def actualizar_costo_promedio(
    session: AsyncSession,
    producto: Producto,
    cantidad: Decimal,
    costo_unitario: Decimal,
    *,
    usuario_id: int | None,
    origen: str,
    referencia_id: int | None = None,
) -> None:
    """Costo promedio ponderado tras una ENTRADA. Debe llamarse ANTES de aplicar la entrada al stock
    y con el producto bloqueado."""
    if cantidad <= 0:
        return
    existente = await existencia_total(session, producto.id)
    anterior = producto.precio_costo
    if existente <= 0:
        nuevo = costo_unitario
    else:
        nuevo = (existente * anterior + cantidad * costo_unitario) / (existente + cantidad)
    nuevo = nuevo.quantize(CUATRO_DECIMALES, rounding=ROUND_HALF_UP)
    if nuevo != anterior:
        producto.precio_costo = nuevo
        session.add(
            HistorialPrecio(
                producto_id=producto.id,
                tipo=TipoPrecio.COSTO,
                precio_anterior=anterior,
                precio_nuevo=nuevo,
                origen=origen,
                referencia_id=referencia_id,
                usuario_id=usuario_id,
            )
        )
