"""Datos iniciales del sistema. Es idempotente: se puede ejecutar varias veces sin duplicar.

Uso:  python -m app.seed
"""

import asyncio
import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constantes import (
    CATALOGO_PERMISOS,
    CORRELATIVOS,
    DESCRIPCION_ROLES,
    MOTIVOS_AJUSTE,
    PARAMETROS_SISTEMA,
    PERMISOS_POR_ROL,
    ROL_ADMINISTRADOR,
    SUCURSAL_PRINCIPAL,
)
from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.models import (
    Almacen,
    Caja,
    Categoria,
    Correlativo,
    Empresa,
    Impresora,
    MotivoAjuste,
    ParametroSistema,
    Permiso,
    Rol,
    SerieComprobante,
    Sucursal,
    Usuario,
)
from app.models.enums import ConexionImpresora, TipoComprobante, TipoImpresora, TipoMotivoAjuste, TipoParametro

logger = logging.getLogger("minimarket.seed")

CATEGORIAS_INICIALES: list[tuple[str, str, str]] = [
    ("Abarrotes", "Arroz, azúcar, aceite, fideos, menestras", "#f59e0b"),
    ("Bebidas", "Gaseosas, aguas, jugos, energizantes", "#3b82f6"),
    ("Lácteos y huevos", "Leche, yogurt, quesos, mantequilla, huevos", "#facc15"),
    ("Panadería", "Pan, galletas, queques", "#d97706"),
    ("Snacks y golosinas", "Papitas, chocolates, caramelos", "#ec4899"),
    ("Limpieza", "Detergentes, lejía, desinfectantes", "#06b6d4"),
    ("Cuidado personal", "Jabón, champú, papel higiénico, pasta dental", "#8b5cf6"),
    ("Licores", "Cervezas, vinos, licores", "#ef4444"),
    ("Embutidos y carnes", "Jamón, hot dog, pollo, carnes", "#f97316"),
    ("Frutas y verduras", "Productos frescos a granel", "#22c55e"),
]

SERIES_INICIALES: list[tuple[TipoComprobante, str]] = [
    (TipoComprobante.TICKET, "T001"),
    (TipoComprobante.BOLETA, "B001"),
    (TipoComprobante.FACTURA, "F001"),
]


async def sembrar_permisos_y_roles(session: AsyncSession) -> dict[str, Rol]:
    existentes = {p.codigo: p for p in (await session.scalars(select(Permiso))).all()}
    for modulo, acciones in CATALOGO_PERMISOS.items():
        for accion, descripcion in acciones.items():
            codigo = f"{modulo}.{accion}"
            if codigo in existentes:
                existentes[codigo].descripcion = descripcion
            else:
                permiso = Permiso(codigo=codigo, modulo=modulo, accion=accion, descripcion=descripcion)
                session.add(permiso)
                existentes[codigo] = permiso
    await session.flush()

    roles: dict[str, Rol] = {}
    for nombre, codigos in PERMISOS_POR_ROL.items():
        rol = await session.scalar(select(Rol).where(Rol.nombre == nombre))
        if rol is None:
            rol = Rol(nombre=nombre, descripcion=DESCRIPCION_ROLES[nombre], es_sistema=True)
            rol.permisos = [existentes[c] for c in codigos]
            session.add(rol)
            logger.info("Rol creado: %s (%d permisos)", nombre, len(codigos))
        elif nombre == ROL_ADMINISTRADOR:
            # El administrador siempre debe tener todos los permisos (incluidos los nuevos)
            rol.permisos = list(existentes.values())
        roles[nombre] = rol
    await session.flush()
    return roles


async def sembrar_sucursal_principal(session: AsyncSession) -> Sucursal:
    sucursal = await session.scalar(select(Sucursal).where(Sucursal.codigo == SUCURSAL_PRINCIPAL["codigo"]))
    if sucursal is None:
        sucursal = Sucursal(**SUCURSAL_PRINCIPAL)
        session.add(sucursal)
        await session.flush()
        logger.info("Sucursal creada: %s", sucursal.nombre)

    if await session.scalar(select(Almacen).where(Almacen.sucursal_id == sucursal.id).limit(1)) is None:
        session.add(Almacen(sucursal_id=sucursal.id, nombre="Almacén principal", es_almacen_venta=True))

    caja = await session.scalar(select(Caja).where(Caja.sucursal_id == sucursal.id).limit(1))
    if caja is None:
        caja = Caja(sucursal_id=sucursal.id, nombre="Caja 1", descripcion="Caja principal")
        session.add(caja)
        await session.flush()

    series = set((await session.scalars(select(SerieComprobante.serie))).all())
    for tipo, serie in SERIES_INICIALES:
        if serie not in series:
            session.add(
                SerieComprobante(sucursal_id=sucursal.id, tipo_comprobante=tipo, serie=serie, predeterminada=True)
            )

    if await session.scalar(select(Impresora).where(Impresora.sucursal_id == sucursal.id).limit(1)) is None:
        session.add(
            Impresora(
                sucursal_id=sucursal.id,
                caja_id=caja.id,
                nombre="Ticketera 80mm",
                tipo=TipoImpresora.TERMICA_80,
                conexion=ConexionImpresora.NAVEGADOR,
                predeterminada=True,
            )
        )
    await session.flush()
    return sucursal


async def sembrar_admin(session: AsyncSession, rol_admin: Rol, sucursal: Sucursal) -> None:
    admin = await session.scalar(select(Usuario).where(Usuario.username == settings.ADMIN_USERNAME))
    if admin is None:
        admin = Usuario(
            nombre_completo=settings.ADMIN_NOMBRE,
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            rol_id=rol_admin.id,
            sucursal_predeterminada_id=sucursal.id,
            sucursales=[sucursal],
        )
        session.add(admin)
        logger.info("Usuario administrador creado: %s", settings.ADMIN_USERNAME)
    elif sucursal not in admin.sucursales:
        admin.sucursales.append(sucursal)


async def sembrar_catalogos(session: AsyncSession) -> None:
    existentes = set((await session.scalars(select(Categoria.nombre))).all())
    for nombre, descripcion, color in CATEGORIAS_INICIALES:
        if nombre not in existentes:
            session.add(Categoria(nombre=nombre, descripcion=descripcion, color=color))

    motivos = set((await session.scalars(select(MotivoAjuste.nombre))).all())
    for nombre, tipo, es_merma in MOTIVOS_AJUSTE:
        if nombre not in motivos:
            session.add(MotivoAjuste(nombre=nombre, tipo=TipoMotivoAjuste(tipo), es_merma=es_merma))

    correlativos = set((await session.scalars(select(Correlativo.clave))).all())
    for clave, (prefijo, descripcion) in CORRELATIVOS.items():
        if clave not in correlativos:
            session.add(Correlativo(clave=clave, prefijo=prefijo, descripcion=descripcion))

    # Solo se agregan parámetros nuevos: nunca se sobrescribe un valor que el usuario ya cambió
    parametros = set((await session.scalars(select(ParametroSistema.clave))).all())
    for clave, (valor, tipo, modulo, descripcion) in PARAMETROS_SISTEMA.items():
        if clave not in parametros:
            session.add(
                ParametroSistema(
                    clave=clave, valor=valor, tipo=TipoParametro(tipo), modulo=modulo, descripcion=descripcion
                )
            )


async def sembrar_empresa(session: AsyncSession) -> None:
    if await session.get(Empresa, 1) is None:
        session.add(
            Empresa(
                id=1,
                ruc="20000000001",
                razon_social="MI MINIMARKET S.A.C.",
                nombre_comercial="Mi Minimarket",
                direccion_fiscal=SUCURSAL_PRINCIPAL["direccion"],
                igv_porcentaje=Decimal(str(settings.IGV_PORCENTAJE)),
                mensaje_ticket="¡Gracias por su compra!",
            )
        )


async def ejecutar_seed() -> None:
    async with SessionLocal() as session, session.begin():
        roles = await sembrar_permisos_y_roles(session)
        sucursal = await sembrar_sucursal_principal(session)
        await sembrar_admin(session, roles[ROL_ADMINISTRADOR], sucursal)
        await sembrar_catalogos(session)
        await sembrar_empresa(session)
    logger.info("Datos iniciales cargados correctamente")


async def _main() -> None:
    try:
        await ejecutar_seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    asyncio.run(_main())
