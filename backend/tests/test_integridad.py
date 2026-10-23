"""Reglas que la base de datos hace cumplir aunque el código fallara (última barrera)."""

from decimal import Decimal

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.models import (
    Almacen,
    Caja,
    DetalleVenta,
    Producto,
    ProductoPresentacion,
    SerieComprobante,
    SesionCaja,
    StockAlmacen,
    Sucursal,
    Transferencia,
    Usuario,
    Venta,
)
from app.models.enums import TipoAfectacionIGV, TipoComprobante


@pytest.fixture
async def base(db):
    """Datos base dentro de una transacción que se deshace al final de cada prueba."""
    admin = await db.scalar(select(Usuario).where(Usuario.username == "admin"))
    sucursal = await db.scalar(select(Sucursal).where(Sucursal.codigo == "0000"))
    almacen = await db.scalar(select(Almacen).where(Almacen.es_almacen_venta.is_(True)))
    caja = await db.scalar(select(Caja))
    producto = Producto(nombre="Cerveza Pilsen 355 ml", precio_venta=Decimal("4.50"))
    db.add(producto)
    await db.flush()
    yield {"db": db, "admin": admin, "sucursal": sucursal, "almacen": almacen, "caja": caja, "producto": producto}
    await db.rollback()


async def rechaza(db, *objetos, cambio=None) -> bool:
    try:
        async with db.begin_nested():
            db.add_all(objetos)
            if cambio:
                cambio()
            await db.flush()
        return False
    except DBAPIError:
        return True


async def test_stock_no_puede_ser_negativo_ni_duplicarse(base):
    db, p, a = base["db"], base["producto"], base["almacen"]
    assert await rechaza(db, StockAlmacen(producto_id=p.id, almacen_id=a.id, cantidad=Decimal("-1")))
    db.add(StockAlmacen(producto_id=p.id, almacen_id=a.id, cantidad=Decimal("10")))
    await db.flush()
    assert await rechaza(db, StockAlmacen(producto_id=p.id, almacen_id=a.id, cantidad=Decimal("1")))


async def test_presentacion_con_factor_cero(base):
    p = base["producto"]
    assert await rechaza(base["db"], ProductoPresentacion(producto_id=p.id, nombre="Mala", factor=0, precio_venta=1))


async def test_un_solo_almacen_de_venta_por_sucursal(base):
    s = base["sucursal"]
    assert await rechaza(base["db"], Almacen(sucursal_id=s.id, nombre="Otro", es_almacen_venta=True))


async def test_una_serie_predeterminada_por_tipo_y_sucursal(base):
    s = base["sucursal"]
    serie = SerieComprobante(
        sucursal_id=s.id, tipo_comprobante=TipoComprobante.BOLETA, serie="B099", predeterminada=True
    )
    assert await rechaza(base["db"], serie)


async def test_transferencia_al_mismo_almacen(base):
    a, u = base["almacen"], base["admin"]
    t = Transferencia(numero="TR-TEST", almacen_origen_id=a.id, almacen_destino_id=a.id, usuario_id=u.id)
    assert await rechaza(base["db"], t)


async def test_un_cajero_no_tiene_dos_cajas_abiertas(base):
    db, u, s = base["db"], base["admin"], base["sucursal"]
    db.add(SesionCaja(caja_id=base["caja"].id, usuario_id=u.id, monto_inicial=Decimal("100")))
    caja2 = Caja(sucursal_id=s.id, nombre="Caja test")
    db.add(caja2)
    await db.flush()
    assert await rechaza(db, SesionCaja(caja_id=caja2.id, usuario_id=u.id, monto_inicial=Decimal("50")))


async def test_no_se_devuelve_mas_de_lo_vendido(base):
    db, u, s, a, p = base["db"], base["admin"], base["sucursal"], base["almacen"], base["producto"]
    sesion = SesionCaja(caja_id=base["caja"].id, usuario_id=u.id, monto_inicial=Decimal("0"))
    db.add(sesion)
    await db.flush()
    detalle = DetalleVenta(
        producto_id=p.id,
        descripcion=p.nombre,
        cantidad=Decimal("2"),
        precio_unitario=Decimal("4.50"),
        costo_unitario=Decimal("3.20"),
        tipo_afectacion_igv=TipoAfectacionIGV.GRAVADO,
        total=Decimal("9.00"),
    )
    venta = Venta(
        sucursal_id=s.id,
        almacen_id=a.id,
        tipo_comprobante=TipoComprobante.TICKET,
        serie="T001",
        numero=999,
        sesion_caja_id=sesion.id,
        usuario_id=u.id,
        total=Decimal("9.00"),
        detalles=[detalle],
    )
    db.add(venta)
    await db.flush()

    def devolver_de_mas():
        detalle.cantidad_devuelta = Decimal("3")

    assert await rechaza(db, cambio=devolver_de_mas)


async def test_busqueda_fulltext_por_fragmento(db):
    db.add(Producto(nombre="Leche Gloria Evaporada 400 g", precio_venta=Decimal("4.20")))
    await db.commit()  # InnoDB solo indexa en FULLTEXT lo confirmado
    try:
        sql = "SELECT nombre FROM productos WHERE MATCH(nombre) AGAINST('\"glori\"' IN BOOLEAN MODE)"
        assert (await db.scalars(text(sql))).all() == ["Leche Gloria Evaporada 400 g"]
    finally:
        await db.execute(text("DELETE FROM productos WHERE nombre = 'Leche Gloria Evaporada 400 g'"))
        await db.commit()
