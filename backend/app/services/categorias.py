"""Categorías y marcas de productos."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import Conflicto, NoEncontrado
from app.dependencies.auth import ContextoUsuario
from app.models import Categoria, Marca, Producto, StockAlmacen
from app.schemas.productos import (
    CategoriaActualizar,
    CategoriaCrear,
    CategoriaSalida,
    MarcaActualizar,
    MarcaCrear,
    MarcaSalida,
)
from app.services import auditoria

type Modelo = type[Categoria] | type[Marca]


def _etiqueta(modelo: Modelo) -> tuple[str, str]:
    return ("categoria", "categorías") if modelo is Categoria else ("marca", "marcas")


async def listar_categorias(session: AsyncSession, *, activo: bool | None = None) -> list[CategoriaSalida]:
    productos = (
        select(Producto.categoria_id, func.count(Producto.id).label("n"))
        .where(Producto.activo.is_(True))
        .group_by(Producto.categoria_id)
        .subquery()
    )
    # Valor del inventario al costo (stock positivo de todos los almacenes)
    valor = (
        select(
            Producto.categoria_id,
            func.sum(func.greatest(StockAlmacen.cantidad, 0) * Producto.precio_costo).label("valor"),
        )
        .join(StockAlmacen, StockAlmacen.producto_id == Producto.id)
        .where(Producto.activo.is_(True))
        .group_by(Producto.categoria_id)
        .subquery()
    )
    consulta = (
        select(Categoria, func.coalesce(productos.c.n, 0), func.coalesce(valor.c.valor, 0))
        .outerjoin(productos, productos.c.categoria_id == Categoria.id)
        .outerjoin(valor, valor.c.categoria_id == Categoria.id)
        .order_by(Categoria.nombre)
    )
    if activo is not None:
        consulta = consulta.where(Categoria.activo.is_(activo))
    return [
        CategoriaSalida(
            id=c.id,
            nombre=c.nombre,
            color=c.color,
            descripcion=c.descripcion,
            activo=c.activo,
            productos=int(n),
            valor_inventario=Decimal(v).quantize(Decimal("0.01")),
        )
        for c, n, v in (await session.execute(consulta)).tuples()
    ]


async def listar_marcas(session: AsyncSession, *, activo: bool | None = None) -> list[MarcaSalida]:
    productos = (
        select(Producto.marca_id, func.count(Producto.id).label("n"))
        .where(Producto.activo.is_(True))
        .group_by(Producto.marca_id)
        .subquery()
    )
    consulta = (
        select(Marca, func.coalesce(productos.c.n, 0))
        .outerjoin(productos, productos.c.marca_id == Marca.id)
        .order_by(Marca.nombre)
    )
    if activo is not None:
        consulta = consulta.where(Marca.activo.is_(activo))
    return [
        MarcaSalida(id=m.id, nombre=m.nombre, activo=m.activo, productos=int(n))
        for m, n in (await session.execute(consulta)).tuples()
    ]


async def _validar_nombre(session: AsyncSession, modelo: Modelo, nombre: str, excluir_id: int | None) -> None:
    otro = await session.scalar(select(modelo.id).where(modelo.nombre == nombre, modelo.id != (excluir_id or 0)))
    if otro:
        entidad, _ = _etiqueta(modelo)
        raise Conflicto(f"Ya existe una {entidad} llamada «{nombre}»", codigo="nombre_duplicado")


async def _obtener(session: AsyncSession, modelo: Modelo, id_: int, *, bloquear: bool = False):
    consulta = select(modelo).where(modelo.id == id_)
    if bloquear:
        consulta = consulta.with_for_update()
    objeto = await session.scalar(consulta)
    if objeto is None:
        entidad, _ = _etiqueta(modelo)
        raise NoEncontrado(f"La {entidad} no existe")
    return objeto


async def crear(session: AsyncSession, ctx: ContextoUsuario, modelo: Modelo, datos: CategoriaCrear | MarcaCrear):
    await _validar_nombre(session, modelo, datos.nombre, None)
    objeto = modelo(**datos.model_dump())
    session.add(objeto)
    await session.flush()
    entidad, modulo = _etiqueta(modelo)
    auditoria.registrar(
        session,
        accion="CREAR",
        modulo=modulo,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad=entidad,
        entidad_id=objeto.id,
        descripcion=f"Creó la {entidad} {objeto.nombre}",
        ip=ctx.ip,
    )
    await session.commit()
    return objeto.id


async def actualizar(
    session: AsyncSession, ctx: ContextoUsuario, modelo: Modelo, id_: int, datos: CategoriaActualizar | MarcaActualizar
):
    objeto = await _obtener(session, modelo, id_, bloquear=True)
    cambios = {k: v for k, v in datos.model_dump(exclude_unset=True).items() if getattr(objeto, k) != v}
    if not cambios:
        return objeto.id
    if "nombre" in cambios:
        if not cambios["nombre"]:
            raise Conflicto("El nombre no puede quedar vacío", codigo="dato_obligatorio")
        await _validar_nombre(session, modelo, cambios["nombre"], objeto.id)
    if cambios.get("activo") is None and "activo" in cambios:
        cambios.pop("activo")
    for campo, valor in cambios.items():
        setattr(objeto, campo, valor)
    entidad, modulo = _etiqueta(modelo)
    auditoria.registrar(
        session,
        accion="EDITAR",
        modulo=modulo,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad=entidad,
        entidad_id=objeto.id,
        descripcion=f"Editó la {entidad} {objeto.nombre}",
        datos={"campos": sorted(cambios)},
        ip=ctx.ip,
    )
    await session.commit()
    return objeto.id


async def eliminar(session: AsyncSession, ctx: ContextoUsuario, modelo: Modelo, id_: int) -> None:
    objeto = await _obtener(session, modelo, id_, bloquear=True)
    columna = Producto.categoria_id if modelo is Categoria else Producto.marca_id
    usados = await session.scalar(select(func.count(Producto.id)).where(columna == id_))
    entidad, modulo = _etiqueta(modelo)
    if usados:
        raise Conflicto(
            f"La {entidad} tiene {usados} producto(s). Muévalos a otra {entidad} o desactívela.",
            codigo="en_uso",
            datos={"productos": usados},
        )
    nombre = objeto.nombre
    await session.delete(objeto)
    auditoria.registrar(
        session,
        accion="ELIMINAR",
        modulo=modulo,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad=entidad,
        entidad_id=id_,
        descripcion=f"Eliminó la {entidad} {nombre}",
        ip=ctx.ip,
    )
    await session.commit()
