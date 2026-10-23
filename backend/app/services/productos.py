from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload

from app.core.excepciones import Conflicto, NoEncontrado, ValidacionNegocio
from app.dependencies.auth import ContextoUsuario
from app.models import (
    Almacen,
    Categoria,
    CodigoBarras,
    DetalleCompra,
    DetalleVenta,
    HistorialPrecio,
    Lote,
    Marca,
    MovimientoInventario,
    Producto,
    ProductoPresentacion,
    StockAlmacen,
    Sucursal,
    Usuario,
)
from app.models.base import CERO
from app.models.enums import TipoPrecio
from app.schemas.productos import (
    CategoriaResumen,
    MarcaResumen,
    PresentacionEntrada,
    PresentacionSalida,
    ProductoActualizar,
    ProductoCrear,
    ProductoDetalle,
    ProductoListado,
    StockEnAlmacen,
)
from app.services import auditoria, imagenes
from app.utils.paginacion import ParametrosPaginacion, aplicar_orden, paginar

MODULO = "productos"
CIEN = Decimal(100)
# Campos que ya no se pueden cambiar cuando el producto tiene movimientos (romperían el kardex o el costo)
CAMPOS_BLOQUEADOS = {
    "unidad_medida": "la unidad de medida",
    "maneja_lotes": "si maneja lotes",
    "permite_decimales": "si admite decimales",
    "precio_costo": "el costo (ahora solo cambia con compras)",
}


def puede_ver_costos(ctx: ContextoUsuario) -> bool:
    return ctx.tiene("productos.editar") or ctx.tiene("reportes.ganancias")


async def almacen_venta_id(session: AsyncSession, sucursal_id: int) -> int | None:
    return await session.scalar(
        select(Almacen.id).where(
            Almacen.sucursal_id == sucursal_id, Almacen.es_almacen_venta.is_(True), Almacen.activo.is_(True)
        )
    )


def estado_stock(stock: Decimal, minimo: Decimal) -> str:
    if stock < 0:
        return "negativo"
    if stock == 0:
        return "sin_stock"
    if minimo > 0 and stock <= minimo:
        return "bajo"
    return "normal"


def margen(precio_venta: Decimal, costo: Decimal) -> Decimal | None:
    if precio_venta <= 0 or costo <= 0:
        return None
    return ((precio_venta - costo) / precio_venta * CIEN).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def _codigo_principal(producto: Producto) -> str | None:
    return next((c.codigo for c in producto.codigos if c.presentacion_id is None), None)


def a_listado(producto: Producto, stock: Decimal, minimo: Decimal, ver_costos: bool) -> ProductoListado:
    imagen, miniatura = imagenes.urls(producto.imagen)
    return ProductoListado(
        id=producto.id,
        nombre=producto.nombre,
        codigo_interno=producto.codigo_interno,
        codigo_barras=_codigo_principal(producto),
        categoria=CategoriaResumen.model_validate(producto.categoria) if producto.categoria else None,
        marca=MarcaResumen.model_validate(producto.marca) if producto.marca else None,
        unidad_medida=producto.unidad_medida,
        precio_venta=producto.precio_venta,
        precio_costo=producto.precio_costo if ver_costos else None,
        margen=margen(producto.precio_venta, producto.precio_costo) if ver_costos else None,
        stock=stock,
        stock_minimo=minimo,
        estado_stock=estado_stock(stock, minimo),
        maneja_lotes=producto.maneja_lotes,
        permite_decimales=producto.permite_decimales,
        imagen_url=imagen,
        miniatura_url=miniatura,
        activo=producto.activo,
    )


def _escapar_like(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def filtro_busqueda(busqueda: str):
    """Coincide por código de barras / código interno exacto, o por TODAS las palabras del nombre (en cualquier orden,
    sin importar mayúsculas ni tildes por la intercalación de MySQL)."""
    texto = busqueda.strip()
    palabras = texto.split()[:6]
    por_nombre = and_(*[Producto.nombre.like(f"%{_escapar_like(p)}%", escape="\\") for p in palabras])
    por_codigo = or_(
        Producto.codigos.any(CodigoBarras.codigo == texto.upper()),
        Producto.codigo_interno == texto,
    )
    return or_(por_nombre, por_codigo)


def _columnas_stock(almacen_id: int | None):
    stock = func.coalesce(StockAlmacen.cantidad, 0)
    minimo = func.coalesce(StockAlmacen.stock_minimo, Producto.stock_minimo)
    union = and_(StockAlmacen.producto_id == Producto.id, StockAlmacen.almacen_id == (almacen_id or 0))
    return stock, minimo, union


async def listar(
    session: AsyncSession,
    ctx: ContextoUsuario,
    params: ParametrosPaginacion,
    *,
    busqueda: str | None = None,
    categoria_id: int | None = None,
    marca_id: int | None = None,
    activo: bool | None = True,
    estado: str | None = None,
    orden: str | None = None,
) -> tuple[list[ProductoListado], int]:
    almacen_id = await almacen_venta_id(session, ctx.sucursal_id)
    stock, minimo, union = _columnas_stock(almacen_id)
    consulta = (
        select(Producto, stock.label("stock"), minimo.label("minimo"))
        .outerjoin(StockAlmacen, union)
        .options(selectinload(Producto.codigos))
    )
    if busqueda and busqueda.strip():
        consulta = consulta.where(filtro_busqueda(busqueda))
    if categoria_id:
        consulta = consulta.where(Producto.categoria_id == categoria_id)
    if marca_id:
        consulta = consulta.where(Producto.marca_id == marca_id)
    if activo is not None:
        consulta = consulta.where(Producto.activo.is_(activo))
    match estado:
        case "bajo":
            consulta = consulta.where(stock > 0, minimo > 0, stock <= minimo)
        case "sin_stock":
            consulta = consulta.where(stock == 0)
        case "negativo":
            consulta = consulta.where(stock < 0)
        case "sin_codigo":
            consulta = consulta.where(~Producto.codigos.any())
    columnas = {
        "nombre": Producto.nombre, "precio": Producto.precio_venta, "stock": stock, "creado": Producto.creado_en,
    }
    consulta = aplicar_orden(consulta, orden, columnas, "nombre").order_by(Producto.id)
    filas, total = await paginar(session, consulta, params, escalares=False)
    ver_costos = puede_ver_costos(ctx)
    return [a_listado(f[0], Decimal(f[1]), Decimal(f[2]), ver_costos) for f in filas], total


async def resumen(session: AsyncSession, ctx: ContextoUsuario) -> dict[str, int]:
    almacen_id = await almacen_venta_id(session, ctx.sucursal_id)
    stock, minimo, union = _columnas_stock(almacen_id)
    activo = Producto.activo.is_(True)

    def contar(*condiciones):
        return func.coalesce(func.sum(case((and_(*condiciones), 1), else_=0)), 0)

    fila = (
        await session.execute(
            select(
                func.count(Producto.id),
                contar(activo),
                contar(activo, stock > 0, minimo > 0, stock <= minimo),
                contar(activo, stock == 0),
                contar(activo, stock < 0),
                contar(activo, ~Producto.codigos.any()),
            )
            .select_from(Producto)
            .outerjoin(StockAlmacen, union)
        )
    ).one()
    total = int(fila[0])
    return {
        "total": total,
        "activos": int(fila[1]),
        "inactivos": total - int(fila[1]),
        "stock_bajo": int(fila[2]),
        "sin_stock": int(fila[3]),
        "negativos": int(fila[4]),
        "sin_codigo": int(fila[5]),
    }


async def _cargar(session: AsyncSession, producto_id: int, *, bloquear: bool = False) -> Producto:
    consulta = select(Producto).where(Producto.id == producto_id)
    if bloquear:
        # Sin los JOIN de categoría/marca: FOR UPDATE bloquearía también esas filas
        consulta = consulta.options(noload(Producto.categoria), noload(Producto.marca)).with_for_update()
    consulta = consulta.options(
        selectinload(Producto.codigos), selectinload(Producto.presentaciones)
    ).execution_options(populate_existing=True)
    producto = await session.scalar(consulta)
    if producto is None:
        raise NoEncontrado("El producto no existe")
    return producto


async def tiene_movimientos(session: AsyncSession, producto_id: int) -> bool:
    return bool(
        await session.scalar(
            select(
                or_(
                    exists().where(MovimientoInventario.producto_id == producto_id),
                    exists().where(Lote.producto_id == producto_id),
                )
            )
        )
    )


async def obtener(session: AsyncSession, ctx: ContextoUsuario, producto_id: int) -> ProductoDetalle:
    producto = await _cargar(session, producto_id)
    consulta = (
        select(StockAlmacen, Almacen, Sucursal)
        .join(Almacen, Almacen.id == StockAlmacen.almacen_id)
        .join(Sucursal, Sucursal.id == Almacen.sucursal_id)
        .where(StockAlmacen.producto_id == producto_id)
        .order_by(Sucursal.nombre, Almacen.nombre)
    )
    if not ctx.tiene("sucursales.todas"):
        consulta = consulta.where(Almacen.sucursal_id == ctx.sucursal_id)
    por_almacen = [
        StockEnAlmacen(
            almacen_id=a.id,
            almacen=a.nombre,
            sucursal_id=s.id,
            sucursal=s.nombre,
            cantidad=st.cantidad,
            pendiente_lote=st.pendiente_lote,
            stock_minimo=st.stock_minimo if st.stock_minimo is not None else producto.stock_minimo,
        )
        for st, a, s in (await session.execute(consulta)).tuples()
    ]
    almacen_id = await almacen_venta_id(session, ctx.sucursal_id)
    actual = next((s for s in por_almacen if s.almacen_id == almacen_id), None)
    listado = a_listado(
        producto,
        actual.cantidad if actual else CERO,
        actual.stock_minimo if actual else producto.stock_minimo,
        puede_ver_costos(ctx),
    )
    return ProductoDetalle(
        **listado.model_dump(),
        descripcion=producto.descripcion,
        codigos=[c.codigo for c in producto.codigos if c.presentacion_id is None],
        presentaciones=[_presentacion_salida(p, producto) for p in producto.presentaciones],
        tipo_afectacion_igv=producto.tipo_afectacion_igv,
        afecto_icbper=producto.afecto_icbper,
        version=producto.version,
        tiene_movimientos=await tiene_movimientos(session, producto_id),
        stock_por_almacen=por_almacen,
        creado_en=producto.creado_en,
        actualizado_en=producto.actualizado_en,
    )


def _presentacion_salida(p: ProductoPresentacion, producto: Producto) -> PresentacionSalida:
    return PresentacionSalida(
        id=p.id,
        nombre=p.nombre,
        factor=p.factor,
        precio_venta=p.precio_venta,
        activo=p.activo,
        codigos=[c.codigo for c in producto.codigos if c.presentacion_id == p.id],
    )


async def buscar_por_codigo(session: AsyncSession, ctx: ContextoUsuario, codigo: str) -> dict[str, Any]:
    texto = codigo.strip().upper()
    fila = await session.scalar(select(CodigoBarras).where(CodigoBarras.codigo == texto))
    if fila is None:
        producto_id = await session.scalar(select(Producto.id).where(Producto.codigo_interno == codigo.strip()))
        if producto_id is None:
            raise NoEncontrado(f"No hay ningún producto con el código {texto}", codigo="codigo_no_encontrado")
        presentacion_id = None
    else:
        producto_id, presentacion_id = fila.producto_id, fila.presentacion_id
    detalle = await obtener(session, ctx, producto_id)
    presentacion = next((p for p in detalle.presentaciones if p.id == presentacion_id), None)
    return {"producto": ProductoListado(**detalle.model_dump(include=set(ProductoListado.model_fields))),
            "presentacion": presentacion}


async def historial_precios(session: AsyncSession, producto_id: int, limite: int = 50) -> list[dict[str, Any]]:
    filas = await session.execute(
        select(HistorialPrecio, Usuario.nombre_completo)
        .outerjoin(Usuario, Usuario.id == HistorialPrecio.usuario_id)
        .where(HistorialPrecio.producto_id == producto_id)
        .order_by(HistorialPrecio.creado_en.desc(), HistorialPrecio.id.desc())
        .limit(limite)
    )
    return [
        {
            "id": h.id,
            "tipo": h.tipo,
            "presentacion_id": h.presentacion_id,
            "precio_anterior": h.precio_anterior,
            "precio_nuevo": h.precio_nuevo,
            "origen": h.origen,
            "usuario": nombre,
            "creado_en": h.creado_en,
        }
        for h, nombre in filas.tuples()
    ]


# --- Validaciones ---------------------------------------------------------------------------------------


async def _validar_referencias(session: AsyncSession, categoria_id: int | None, marca_id: int | None) -> None:
    if categoria_id is not None:
        categoria = await session.get(Categoria, categoria_id)
        if categoria is None or not categoria.activo:
            raise ValidacionNegocio("La categoría no existe o está inactiva", codigo="categoria_invalida")
    if marca_id is not None:
        marca = await session.get(Marca, marca_id)
        if marca is None or not marca.activo:
            raise ValidacionNegocio("La marca no existe o está inactiva", codigo="marca_invalida")


async def validar_codigos_libres(session: AsyncSession, codigos: list[str], producto_id: int | None) -> None:
    if not codigos:
        return
    ocupados = await session.execute(
        select(CodigoBarras.codigo, Producto.nombre)
        .join(Producto, Producto.id == CodigoBarras.producto_id)
        .where(CodigoBarras.codigo.in_(codigos), CodigoBarras.producto_id != (producto_id or 0))
    )
    fila = ocupados.first()
    if fila:
        raise Conflicto(f"El código {fila[0]} ya pertenece a «{fila[1]}»", codigo="codigo_duplicado",
                        datos={"codigo": fila[0]})


async def _validar_unicos(
    session: AsyncSession, nombre: str | None, codigo_interno: str | None, producto_id: int | None
) -> None:
    if nombre:
        otro = await session.scalar(
            select(Producto.id).where(Producto.nombre == nombre, Producto.id != (producto_id or 0))
        )
        if otro:
            raise Conflicto(f"Ya existe un producto llamado «{nombre}»", codigo="nombre_duplicado")
    if codigo_interno:
        otro = await session.scalar(
            select(Producto.id).where(Producto.codigo_interno == codigo_interno, Producto.id != (producto_id or 0))
        )
        if otro:
            raise Conflicto(f"El código interno {codigo_interno} ya está en uso", codigo="codigo_interno_duplicado")


def _validar_unidad_decimales(unidad, permite_decimales: bool, stock_minimo: Decimal, presentaciones) -> None:
    if not permite_decimales:
        if stock_minimo != stock_minimo.to_integral_value():
            raise ValidacionNegocio("El stock mínimo debe ser entero si el producto no admite decimales",
                                    codigo="cantidad_no_entera")
        for p in presentaciones:
            if p.factor != p.factor.to_integral_value():
                raise ValidacionNegocio(f"La presentación «{p.nombre}» debe contener unidades enteras",
                                        codigo="cantidad_no_entera")


def _historial(producto: Producto, tipo: TipoPrecio, anterior: Decimal, nuevo: Decimal, usuario_id: int,
               origen: str = "MANUAL", presentacion_id: int | None = None) -> HistorialPrecio:
    return HistorialPrecio(
        producto_id=producto.id,
        presentacion_id=presentacion_id,
        tipo=tipo,
        precio_anterior=anterior,
        precio_nuevo=nuevo,
        origen=origen,
        usuario_id=usuario_id,
    )


# --- Escritura ------------------------------------------------------------------------------------------


def nuevo_producto(datos: ProductoCrear) -> Producto:
    producto = Producto(
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        codigo_interno=datos.codigo_interno,
        categoria_id=datos.categoria_id,
        marca_id=datos.marca_id,
        unidad_medida=datos.unidad_medida,
        precio_venta=datos.precio_venta,
        precio_costo=datos.precio_costo,
        stock_minimo=datos.stock_minimo,
        tipo_afectacion_igv=datos.tipo_afectacion_igv,
        afecto_icbper=datos.afecto_icbper,
        maneja_lotes=datos.maneja_lotes,
        permite_decimales=datos.permite_decimales,
        codigos=[CodigoBarras(codigo=c) for c in datos.codigos],
        presentaciones=[],
    )
    for entrada in datos.presentaciones:
        presentacion = ProductoPresentacion(
            nombre=entrada.nombre, factor=entrada.factor, precio_venta=entrada.precio_venta, activo=entrada.activo
        )
        producto.presentaciones.append(presentacion)
        producto.codigos.extend(CodigoBarras(codigo=c, presentacion=presentacion) for c in entrada.codigos)
    return producto


async def validar_nuevo(session: AsyncSession, datos: ProductoCrear) -> None:
    await _validar_referencias(session, datos.categoria_id, datos.marca_id)
    await _validar_unicos(session, datos.nombre, datos.codigo_interno, None)
    await validar_codigos_libres(session, [*datos.codigos, *(c for p in datos.presentaciones for c in p.codigos)], None)
    _validar_unidad_decimales(datos.unidad_medida, datos.permite_decimales, datos.stock_minimo, datos.presentaciones)


async def crear(session: AsyncSession, ctx: ContextoUsuario, datos: ProductoCrear) -> ProductoDetalle:
    await validar_nuevo(session, datos)
    producto = nuevo_producto(datos)
    session.add(producto)
    await session.flush()
    auditoria.registrar(
        session,
        accion="CREAR",
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad="producto",
        entidad_id=producto.id,
        descripcion=f"Creó el producto {producto.nombre}",
        datos={"precio_venta": str(datos.precio_venta), "codigos": datos.codigos},
        ip=ctx.ip,
    )
    await session.commit()
    return await obtener(session, ctx, producto.id)


async def _sincronizar_presentaciones(
    session: AsyncSession, ctx: ContextoUsuario, producto: Producto, entradas: list[PresentacionEntrada]
) -> dict[int | None, list[str]] | None:
    """Actualiza/crea/quita presentaciones. Devuelve {id_temporal: códigos} para sincronizar códigos después."""
    actuales = {p.id: p for p in producto.presentaciones}
    deseadas: list[tuple[ProductoPresentacion, list[str]]] = []
    for entrada in entradas:
        if entrada.id is not None:
            presentacion = actuales.get(entrada.id)
            if presentacion is None:
                raise ValidacionNegocio("Una de las presentaciones no pertenece a este producto",
                                        codigo="presentacion_invalida")
            if presentacion.precio_venta != entrada.precio_venta:
                session.add(_historial(producto, TipoPrecio.VENTA, presentacion.precio_venta, entrada.precio_venta,
                                       ctx.usuario_id, presentacion_id=presentacion.id))
            presentacion.nombre = entrada.nombre
            presentacion.factor = entrada.factor
            presentacion.precio_venta = entrada.precio_venta
            presentacion.activo = entrada.activo
        else:
            presentacion = ProductoPresentacion(
                nombre=entrada.nombre, factor=entrada.factor, precio_venta=entrada.precio_venta, activo=entrada.activo
            )
            producto.presentaciones.append(presentacion)
        deseadas.append((presentacion, entrada.codigos))

    ids_deseados = {e.id for e in entradas if e.id is not None}
    for pid, presentacion in actuales.items():
        if pid in ids_deseados:
            continue
        usada = await session.scalar(select(exists().where(DetalleVenta.presentacion_id == pid)))
        for codigo in [c for c in producto.codigos if c.presentacion_id == pid]:
            producto.codigos.remove(codigo)
        if usada:
            presentacion.activo = False  # se conserva para el historial de ventas
        else:
            producto.presentaciones.remove(presentacion)
    await session.flush()
    return {p.id: codigos for p, codigos in deseadas}


async def _sincronizar_codigos(
    session: AsyncSession, producto: Producto, base: list[str], por_presentacion: dict[int, list[str]]
) -> None:
    deseados: dict[str, int | None] = {c: None for c in base}
    for pid, codigos in por_presentacion.items():
        deseados.update({c: pid for c in codigos})
    await validar_codigos_libres(session, list(deseados), producto.id)
    for codigo in list(producto.codigos):
        if deseados.get(codigo.codigo, -1) != codigo.presentacion_id:
            producto.codigos.remove(codigo)
    await session.flush()
    existentes = {c.codigo for c in producto.codigos}
    for codigo, pid in deseados.items():
        if codigo not in existentes:
            producto.codigos.append(CodigoBarras(codigo=codigo, presentacion_id=pid))


async def actualizar(
    session: AsyncSession, ctx: ContextoUsuario, producto_id: int, datos: ProductoActualizar
) -> ProductoDetalle:
    producto = await _cargar(session, producto_id, bloquear=True)
    if producto.version != datos.version:
        raise Conflicto(
            "Otra persona modificó este producto mientras usted lo editaba. Recargue para ver los cambios.",
            codigo="version_desactualizada",
            datos={"version_actual": producto.version},
        )
    cambios = datos.model_dump(exclude_unset=True, exclude={"version", "codigos", "presentaciones"})
    cambios = {k: v for k, v in cambios.items() if getattr(producto, k) != v}

    bloqueados = [CAMPOS_BLOQUEADOS[k] for k in cambios if k in CAMPOS_BLOQUEADOS]
    if bloqueados and await tiene_movimientos(session, producto.id):
        raise ValidacionNegocio(
            "El producto ya tiene movimientos de stock: no se puede cambiar " + ", ".join(bloqueados),
            codigo="producto_con_movimientos",
        )
    for campo in ("nombre", "precio_venta", "unidad_medida", "maneja_lotes", "permite_decimales", "activo"):
        if campo in cambios and cambios[campo] is None:
            raise ValidacionNegocio(f"El campo {campo} no puede quedar vacío", codigo="dato_obligatorio")
    await _validar_referencias(session, cambios.get("categoria_id"), cambios.get("marca_id"))
    await _validar_unicos(session, cambios.get("nombre"), cambios.get("codigo_interno"), producto.id)

    if "precio_venta" in cambios:
        session.add(_historial(producto, TipoPrecio.VENTA, producto.precio_venta, cambios["precio_venta"],
                               ctx.usuario_id))
    if "precio_costo" in cambios:
        session.add(_historial(producto, TipoPrecio.COSTO, producto.precio_costo, cambios["precio_costo"],
                               ctx.usuario_id))
    for campo, valor in cambios.items():
        setattr(producto, campo, valor)

    campos = sorted(cambios)
    por_presentacion: dict[int, list[str]] | None = None
    if datos.presentaciones is not None:
        por_presentacion = await _sincronizar_presentaciones(session, ctx, producto, datos.presentaciones)
        campos.append("presentaciones")
    if datos.codigos is not None or por_presentacion is not None:
        base = datos.codigos if datos.codigos is not None else [
            c.codigo for c in producto.codigos if c.presentacion_id is None
        ]
        if por_presentacion is None:
            por_presentacion = {}
            for c in producto.codigos:
                if c.presentacion_id is not None:
                    por_presentacion.setdefault(c.presentacion_id, []).append(c.codigo)
        await _sincronizar_codigos(session, producto, base, por_presentacion)
        if datos.codigos is not None:
            campos.append("codigos")

    _validar_unidad_decimales(
        producto.unidad_medida, producto.permite_decimales, producto.stock_minimo,
        [p for p in producto.presentaciones if p.activo],
    )
    if not campos:
        await session.rollback()
        return await obtener(session, ctx, producto_id)

    producto.version += 1
    auditoria.registrar(
        session,
        accion="EDITAR",
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad="producto",
        entidad_id=producto.id,
        descripcion=f"Editó el producto {producto.nombre}",
        datos={"campos": campos},
        ip=ctx.ip,
    )
    await session.commit()
    return await obtener(session, ctx, producto_id)


async def eliminar(session: AsyncSession, ctx: ContextoUsuario, producto_id: int) -> None:
    producto = await _cargar(session, producto_id, bloquear=True)
    en_uso = await tiene_movimientos(session, producto_id) or await session.scalar(
        select(
            or_(
                exists().where(DetalleVenta.producto_id == producto_id),
                exists().where(DetalleCompra.producto_id == producto_id),
            )
        )
    )
    if en_uso:
        raise Conflicto(
            "El producto ya tiene movimientos, ventas o compras y no se puede eliminar. Desactívelo para ocultarlo.",
            codigo="producto_con_movimientos",
        )
    imagen = producto.imagen
    nombre = producto.nombre
    await session.execute(StockAlmacen.__table__.delete().where(StockAlmacen.producto_id == producto_id))
    await session.delete(producto)
    auditoria.registrar(
        session,
        accion="ELIMINAR",
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad="producto",
        entidad_id=producto_id,
        descripcion=f"Eliminó el producto {nombre}",
        ip=ctx.ip,
    )
    await session.commit()
    imagenes.borrar(imagen)


async def cambiar_imagen(
    session: AsyncSession, ctx: ContextoUsuario, producto_id: int, datos: bytes | None
) -> ProductoDetalle:
    """Sube (o quita, si datos es None) la foto. La anterior se borra solo después de confirmar el cambio."""
    nueva = await imagenes.guardar(datos) if datos is not None else None
    try:
        producto = await _cargar(session, producto_id, bloquear=True)
        anterior = producto.imagen
        producto.imagen = nueva
        producto.version += 1
        auditoria.registrar(
            session,
            accion="EDITAR",
            modulo=MODULO,
            usuario_id=ctx.usuario_id,
            sucursal_id=ctx.sucursal_id,
            entidad="producto",
            entidad_id=producto.id,
            descripcion=f"{'Cambió' if nueva else 'Quitó'} la foto de {producto.nombre}",
            ip=ctx.ip,
        )
        await session.commit()
    except BaseException:
        await session.rollback()
        imagenes.borrar(nueva)
        raise
    imagenes.borrar(anterior)
    return await obtener(session, ctx, producto_id)
