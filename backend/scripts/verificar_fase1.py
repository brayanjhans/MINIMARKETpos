import asyncio
from decimal import Decimal

from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from app.core.database import SessionLocal, engine
from app.core.excepciones import _clasificar_error_bd
from app.core.security import verify_password
from app.main import app
from app.models import (
    Almacen,
    Caja,
    Categoria,
    Correlativo,
    DetalleVenta,
    Empresa,
    MotivoAjuste,
    ParametroSistema,
    Permiso,
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
from app.models.enums import EstadoSesionCaja, TipoAfectacionIGV, TipoComprobante

resultados: list[tuple[str, bool]] = []


def check(nombre: str, ok: bool) -> None:
    resultados.append((nombre, ok))
    print(("  OK   " if ok else "  FALLA ") + nombre)


async def rechaza(s, accion) -> bool:
    try:
        async with s.begin_nested():
            await accion()
        return False
    except DBAPIError as e:
        c = _clasificar_error_bd(e)
        print(f"         -> API respondería {c[0]}: {c[1]}")
        return True


async def main() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/health")
        check("/health responde 200", r.status_code == 200)

    async with SessionLocal() as s:
        admin = await s.scalar(select(Usuario).where(Usuario.username == "admin"))
        principal = await s.scalar(select(Sucursal))
        almacen = await s.scalar(select(Almacen).where(Almacen.es_almacen_venta))
        caja = await s.scalar(select(Caja))
        check("admin: contraseña válida", verify_password("Admin123*", admin.password_hash))
        check("admin asignado a sucursal Principal", [x.nombre for x in admin.sucursales] == ["Principal"])
        check("61 permisos", await s.scalar(select(func.count(Permiso.id))) == 61)
        print("  datos: categorías", await s.scalar(select(func.count(Categoria.id))),
              "| motivos", await s.scalar(select(func.count(MotivoAjuste.id))),
              "| correlativos", await s.scalar(select(func.count(Correlativo.clave))),
              "| parámetros", await s.scalar(select(func.count(ParametroSistema.clave))),
              "| ICBPER", (await s.get(Empresa, 1)).icbper_monto)
        denom = await s.get(ParametroSistema, "caja.denominaciones")
        check("parámetro JSON se lee como lista", isinstance(denom.valor, list) and denom.valor[0] == "200")

        prod = Producto(nombre="Cerveza Pilsen lata 355ml", codigo_barras="7750182000017", precio_venta=Decimal("4.50"))
        s.add(prod)
        await s.flush()
        s.add(StockAlmacen(producto_id=prod.id, almacen_id=almacen.id, cantidad=Decimal("48")))
        await s.flush()

        async def stock_negativo():
            st = await s.scalar(select(StockAlmacen).where(StockAlmacen.producto_id == prod.id).with_for_update())
            st.cantidad = Decimal("-1")
            await s.flush()
        check("BD rechaza stock negativo en almacén", await rechaza(s, stock_negativo))

        async def stock_duplicado():
            s.add(StockAlmacen(producto_id=prod.id, almacen_id=almacen.id, cantidad=Decimal("1")))
            await s.flush()
        check("BD rechaza 2 filas de stock para mismo producto/almacén", await rechaza(s, stock_duplicado))

        s.add(ProductoPresentacion(producto_id=prod.id, nombre="Six pack", codigo_barras="7750182000024",
                                   factor=Decimal("6"), precio_venta=Decimal("25.00")))
        await s.flush()
        async def factor_cero():
            s.add(ProductoPresentacion(producto_id=prod.id, nombre="Malo", factor=Decimal("0"), precio_venta=1))
            await s.flush()
        check("BD rechaza presentación con factor 0", await rechaza(s, factor_cero))

        async def segundo_almacen_venta():
            s.add(Almacen(sucursal_id=principal.id, nombre="Otro", es_almacen_venta=True))
            await s.flush()
        check("BD rechaza 2 almacenes de venta en una sucursal", await rechaza(s, segundo_almacen_venta))

        # Segunda sucursal: puede tener su propio almacén de venta y su serie B002 predeterminada
        sur = Sucursal(codigo="0001", nombre="Sucursal Sur")
        s.add(sur)
        await s.flush()
        almacen_sur = Almacen(sucursal_id=sur.id, nombre="Almacén Sur", es_almacen_venta=True)
        s.add_all([almacen_sur, SerieComprobante(sucursal_id=sur.id, tipo_comprobante=TipoComprobante.BOLETA,
                                                 serie="B002", predeterminada=True)])
        await s.flush()
        check("2ª sucursal con su almacén de venta y serie B002 predeterminada", True)

        async def serie_predet_repetida():
            s.add(SerieComprobante(sucursal_id=sur.id, tipo_comprobante=TipoComprobante.BOLETA, serie="B003",
                                   predeterminada=True))
            await s.flush()
        check("BD rechaza 2 series predeterminadas del mismo tipo en una sucursal",
              await rechaza(s, serie_predet_repetida))

        async def transferencia_mismo_almacen():
            s.add(Transferencia(numero="TR-X", almacen_origen_id=almacen.id, almacen_destino_id=almacen.id,
                                usuario_id=admin.id))
            await s.flush()
        check("BD rechaza transferencia al mismo almacén", await rechaza(s, transferencia_mismo_almacen))

        sesion = SesionCaja(caja_id=caja.id, usuario_id=admin.id, monto_inicial=Decimal("100"))
        s.add(sesion)
        await s.flush()
        caja2 = Caja(sucursal_id=principal.id, nombre="Caja 2")
        s.add(caja2)
        await s.flush()
        async def segunda_caja():
            s.add(SesionCaja(caja_id=caja2.id, usuario_id=admin.id, monto_inicial=Decimal("50")))
            await s.flush()
        check("BD rechaza 2 cajas abiertas del mismo cajero", await rechaza(s, segunda_caja))

        venta = Venta(sucursal_id=principal.id, almacen_id=almacen.id, tipo_comprobante=TipoComprobante.TICKET,
                      serie="T001", numero=1, sesion_caja_id=sesion.id, usuario_id=admin.id,
                      op_gravadas=Decimal("7.63"), igv=Decimal("1.37"), total=Decimal("9.00"))
        det = DetalleVenta(descripcion=prod.nombre, producto_id=prod.id, cantidad=Decimal("2"),
                           precio_unitario=Decimal("4.50"), costo_unitario=Decimal("3.20"),
                           tipo_afectacion_igv=TipoAfectacionIGV.GRAVADO, igv=Decimal("1.37"), total=Decimal("9.00"))
        venta.detalles.append(det)
        s.add(venta)
        await s.flush()
        async def devolver_de_mas():
            det.cantidad_devuelta = Decimal("3")
            await s.flush()
        check("BD rechaza devolver más de lo vendido", await rechaza(s, devolver_de_mas))

        sesion.estado = EstadoSesionCaja.CERRADA
        await s.flush()
        await s.commit()

        sql = "SELECT nombre FROM productos WHERE MATCH(nombre) AGAINST('\"pilse\"' IN BOOLEAN MODE)"
        rs = (await s.scalars(text(sql))).all()
        check("Búsqueda FULLTEXT 'pilse' encuentra la cerveza", rs == ["Cerveza Pilsen lata 355ml"])

    # Limpieza de los datos de prueba (vuelve al estado del seed)
    async with SessionLocal() as s, s.begin():
        for sql in ["DELETE FROM detalles_venta", "DELETE FROM ventas", "DELETE FROM sesiones_caja",
                    "DELETE FROM cajas WHERE nombre='Caja 2'", "DELETE FROM series_comprobante WHERE serie='B002'",
                    "DELETE FROM almacenes WHERE nombre='Almacén Sur'", "DELETE FROM sucursales WHERE codigo='0001'",
                    "DELETE FROM stock_almacen", "DELETE FROM producto_presentaciones", "DELETE FROM productos"]:
            await s.execute(text(sql))
    await engine.dispose()
    fallas = [n for n, ok in resultados if not ok]
    print(f"\n{len(resultados) - len(fallas)}/{len(resultados)} pruebas OK", "" if not fallas else f"FALLAS: {fallas}")


asyncio.run(main())
