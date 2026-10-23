"""Datos de DEMOSTRACIÓN para ver el sistema funcionando (no usar en producción).

Crea ~30 productos típicos de un minimarket peruano con códigos de barras de prueba (prefijo 200, que no
pertenece a ningún fabricante), carga su stock inicial (algunos con lotes y vencimiento), un segundo almacén
"Depósito" y un ajuste por aprobar. Es idempotente: si un producto ya existe, no lo vuelve a crear.

Uso:  python -m app.demo
"""

import asyncio
import logging
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.dependencies.auth import ContextoUsuario, cargar_usuario
from app.models import Almacen, Categoria, Marca, MotivoAjuste, Producto, Usuario
from app.schemas.inventario import AjusteCrear, AjusteDetalleEntrada, StockInicialEntrada, StockInicialItem
from app.schemas.productos import PresentacionEntrada, ProductoCrear
from app.services import ajustes, inventario, productos
from app.utils.zona_horaria import hoy_local

logger = logging.getLogger("minimarket.demo")

# (nombre, categoría, marca, unidad, precio venta, costo, stock, mínimo, igv, lotes [(lote, días, cantidad)])
PRODUCTOS: list[tuple] = [
    ("Arroz Costeño extra 1 kg", "Abarrotes", "Costeño", "UNIDAD", "4.50", "3.95", "33", "20", "GRAVADO", None),
    ("Azúcar rubia Dulfina 1 kg", "Abarrotes", "Dulfina", "UNIDAD", "3.80", "3.20", "5", "20", "GRAVADO", None),
    ("Aceite Primor premium 1 L", "Abarrotes", "Primor", "UNIDAD", "11.50", "9.40", "3", "12", "GRAVADO", None),
    ("Fideo spaghetti Don Vittorio 500 g", "Abarrotes", "Don Vittorio", "UNIDAD", "3.60", "2.85", "40", "15",
     "GRAVADO", None),
    ("Atún Florida filete 170 g", "Abarrotes", "Florida", "UNIDAD", "6.90", "5.30", "36", "12", "GRAVADO", None),
    ("Leche Gloria evaporada 400 g", "Lácteos y huevos", "Gloria", "UNIDAD", "4.20", "3.30", None, "48", "GRAVADO",
     [("LG-1022", 120, "72"), ("LG-1030", 150, "24")]),
    ("Gaseosa Inca Kola 1.5 L", "Bebidas", "Inca Kola", "UNIDAD", "7.50", "5.40", "48", "24", "GRAVADO", None),
    ("Gaseosa Coca-Cola 500 ml", "Bebidas", "Coca-Cola", "UNIDAD", "3.00", "2.10", "36", "24", "GRAVADO", None),
    ("Agua San Luis sin gas 625 ml", "Bebidas", "San Luis", "UNIDAD", "1.80", "1.10", "60", "24", "GRAVADO", None),
    ("Gaseosa Guaraná 1 L", "Bebidas", "Backus", "UNIDAD", "4.00", "2.90", "24", "12", "GRAVADO", None),
    ("Frugos del Valle durazno 1 L", "Bebidas", "Frugos", "UNIDAD", "4.50", "3.40", "18", "12", "GRAVADO", None),
    ("Red Bull 250 ml", "Bebidas", "Red Bull", "UNIDAD", "7.50", "5.80", "12", "6", "GRAVADO", None),
    ("Cerveza Pilsen Callao 630 ml", "Licores", "Pilsen", "UNIDAD", "6.50", "4.90", "120", "48", "GRAVADO", None),
    ("Cerveza Cusqueña dorada lata 355 ml", "Licores", "Cusqueña", "UNIDAD", "4.50", "3.40", "0", "24", "GRAVADO",
     None),
    ("Yogurt Gloria fresa 1 L", "Lácteos y huevos", "Gloria", "UNIDAD", "6.90", "5.10", None, "6", "GRAVADO",
     [("L-0921", 2, "6"), ("L-0950", 18, "6")]),
    ("Queso fresco Laive 500 g", "Lácteos y huevos", "Laive", "UNIDAD", "17.90", "14.50", None, "3", "GRAVADO",
     [("Q-118", 12, "4")]),
    ("Mantequilla Laive con sal 200 g", "Lácteos y huevos", "Laive", "UNIDAD", "9.20", "7.30", "10", "5", "GRAVADO",
     None),
    ("Huevos rosados (unidad)", "Lácteos y huevos", None, "UNIDAD", "0.60", "0.45", "90", "60", "EXONERADO", None),
    ("Pan francés", "Panadería", None, "UNIDAD", "0.20", "0.12", "180", "50", "GRAVADO", None),
    ("Pan de molde Bimbo blanco", "Panadería", "Bimbo", "UNIDAD", "8.90", "6.90", None, "4", "GRAVADO",
     [("PM-77", 25, "8")]),
    ("Galletas Soda Field paquete x6", "Snacks y golosinas", "Field", "UNIDAD", "3.20", "2.40", "22", "10",
     "GRAVADO", None),
    ("Papas Lay's clásicas 42 g", "Snacks y golosinas", "Lay's", "UNIDAD", "2.50", "1.70", "30", "12", "GRAVADO",
     None),
    ("Chocolate Sublime clásico 30 g", "Snacks y golosinas", "Nestlé", "UNIDAD", "1.50", "1.05", "50", "24",
     "GRAVADO", None),
    ("Galletas Oreo 36 g", "Snacks y golosinas", "Oreo", "UNIDAD", "1.20", "0.80", "0", "24", "GRAVADO", None),
    ("Detergente Bolívar 750 g", "Limpieza", "Bolívar", "UNIDAD", "9.90", "7.80", "14", "6", "GRAVADO", None),
    ("Lejía Clorox 1 L", "Limpieza", "Clorox", "UNIDAD", "4.20", "3.10", "20", "8", "GRAVADO", None),
    ("Lavavajilla Ayudín limón 450 g", "Limpieza", "Ayudín", "UNIDAD", "5.50", "4.20", "9", "10", "GRAVADO", None),
    ("Papel higiénico Elite x4", "Cuidado personal", "Elite", "UNIDAD", "6.90", "5.20", "25", "10", "GRAVADO", None),
    ("Jabón Protex avena 110 g", "Cuidado personal", "Protex", "UNIDAD", "3.90", "2.90", "18", "8", "GRAVADO", None),
    ("Pasta dental Colgate triple acción 75 ml", "Cuidado personal", "Colgate", "UNIDAD", "5.90", "4.40", "15", "6",
     "GRAVADO", None),
    ("Plátano de seda", "Frutas y verduras", None, "KILOGRAMO", "3.50", "2.40", "25.5", "10", "EXONERADO", None),
    ("Papa amarilla", "Frutas y verduras", None, "KILOGRAMO", "4.20", "3.00", "40.25", "15", "EXONERADO", None),
    ("Limón", "Frutas y verduras", None, "KILOGRAMO", "6.00", "4.50", "8.75", "5", "EXONERADO", None),
    ("Hot dog San Fernando x10", "Embutidos y carnes", "San Fernando", "UNIDAD", "8.50", "6.60", None, "4",
     "GRAVADO", [("HD-3310", 4, "5")]),
]

# Presentaciones de algunos productos: nombre del producto -> [(presentación, factor, precio)]
PRESENTACIONES = {
    "Cerveza Pilsen Callao 630 ml": [("Caja x12", "12", "72.00")],
    "Chocolate Sublime clásico 30 g": [("Caja x24", "24", "33.00")],
    "Gaseosa Coca-Cola 500 ml": [("Six pack", "6", "16.50")],
}


def ean13(numero: int) -> str:
    """Código EAN-13 de prueba con prefijo 200 (uso interno) y dígito verificador correcto."""
    base = f"200{numero:09d}"
    suma = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(base))
    return base + str((10 - suma % 10) % 10)


async def _contexto(session) -> ContextoUsuario:
    admin = await session.scalar(select(Usuario).where(Usuario.username == settings.ADMIN_USERNAME))
    usuario = await cargar_usuario(session, admin.id)
    return ContextoUsuario(
        usuario=usuario,
        sucursal_id=usuario.sucursal_predeterminada_id,
        permisos=frozenset(p.codigo for p in usuario.rol.permisos),
        ip="127.0.0.1",
    )


async def _id_por_nombre(session, modelo, nombre: str | None) -> int | None:
    if not nombre:
        return None
    objeto = await session.scalar(select(modelo).where(modelo.nombre == nombre))
    if objeto is None:
        objeto = modelo(nombre=nombre)
        session.add(objeto)
        await session.commit()
    return objeto.id


async def cargar_demo() -> None:
    async with SessionLocal() as session:
        ctx = await _contexto(session)
        hoy = hoy_local()

        # Segundo almacén para probar transferencias
        if await session.scalar(select(Almacen).where(Almacen.sucursal_id == ctx.sucursal_id,
                                                      Almacen.nombre == "Depósito")) is None:
            session.add(Almacen(sucursal_id=ctx.sucursal_id, nombre="Depósito", es_almacen_venta=False))
            await session.commit()
            logger.info("Almacén Depósito creado")

        items: list[StockInicialItem] = []
        creados = 0
        for i, (nombre, categoria, marca, unidad, precio, costo, cantidad, minimo, igv, lotes) in enumerate(
            PRODUCTOS, start=1
        ):
            producto_id = await session.scalar(select(Producto.id).where(Producto.nombre == nombre))
            if producto_id is None:
                decimales = unidad == "KILOGRAMO"
                presentaciones = [
                    PresentacionEntrada(nombre=p, factor=Decimal(f), precio_venta=Decimal(v),
                                        codigos=[ean13(9000 + i)])
                    for p, f, v in PRESENTACIONES.get(nombre, [])
                ]
                detalle = await productos.crear(
                    session,
                    ctx,
                    ProductoCrear(
                        nombre=nombre,
                        codigos=[] if decimales or nombre == "Pan francés" else [ean13(1000 + i)],
                        categoria_id=await _id_por_nombre(session, Categoria, categoria),
                        marca_id=await _id_por_nombre(session, Marca, marca),
                        unidad_medida=unidad,
                        precio_venta=Decimal(precio),
                        precio_costo=Decimal(costo),
                        stock_minimo=Decimal(minimo),
                        tipo_afectacion_igv=igv,
                        maneja_lotes=lotes is not None,
                        permite_decimales=decimales,
                        presentaciones=presentaciones,
                    ),
                )
                producto_id = detalle.id
                creados += 1
            if lotes:
                items += [
                    StockInicialItem(producto_id=producto_id, cantidad=Decimal(c), costo_unitario=Decimal(costo),
                                     numero_lote=lote, fecha_vencimiento=hoy + timedelta(days=dias))
                    for lote, dias, c in lotes
                ]
            elif cantidad and Decimal(cantidad) > 0:
                items.append(StockInicialItem(producto_id=producto_id, cantidad=Decimal(cantidad),
                                              costo_unitario=Decimal(costo)))
        logger.info("Productos creados: %d", creados)

        cargables = {
            c["producto_id"]
            for c in await inventario.cargables(session, ctx, list({i.producto_id for i in items}), None)
            if c["puede"]
        }
        pendientes = [i for i in items if i.producto_id in cargables]
        if pendientes:
            resultado = await inventario.cargar_stock_inicial(
                session, ctx, StockInicialEntrada(items=pendientes), None
            )
            logger.info("Stock inicial: %s productos, valor S/ %s", resultado["productos"], resultado["valor"])

        # Un ajuste por aprobar (yogurt que vence en 2 días)
        yogurt = await session.scalar(select(Producto).where(Producto.nombre == "Yogurt Gloria fresa 1 L"))
        motivo = await session.scalar(select(MotivoAjuste).where(MotivoAjuste.nombre == "Producto vencido"))
        lotes_yogurt = await inventario.listar_lotes(session, ctx, almacen_id=None, producto_id=yogurt.id)
        hay_ajuste = (await ajustes.listar(session, ctx, _pag(), almacen_id=None))[1] > 0
        if lotes_yogurt and not hay_ajuste:
            await ajustes.crear(
                session,
                ctx,
                AjusteCrear(
                    motivo_id=motivo.id,
                    observaciones="Revisión de la mañana: yogurt por vencer en mal estado",
                    detalles=[AjusteDetalleEntrada(producto_id=yogurt.id, cantidad=Decimal("-2"),
                                                   lote_id=lotes_yogurt[0]["id"])],
                ),
                None,
            )
            logger.info("Ajuste de ejemplo creado (por aprobar)")
    logger.info("Datos de demostración listos")


def _pag():
    from app.utils.paginacion import ParametrosPaginacion

    return ParametrosPaginacion(pagina=1, tamanio=1)


async def _main() -> None:
    try:
        await cargar_demo()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    asyncio.run(_main())
