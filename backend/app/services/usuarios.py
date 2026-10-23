from datetime import datetime

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constantes import ROL_ADMINISTRADOR
from app.core.excepciones import Conflicto, NoEncontrado, ValidacionNegocio
from app.core.security import hash_password
from app.dependencies.auth import ContextoUsuario
from app.models import Rol, Sucursal, Usuario
from app.schemas.usuarios import RestablecerPassword, UsuarioActualizar, UsuarioCrear
from app.services import auditoria
from app.services.auth import revocar_sesiones
from app.utils.paginacion import ParametrosPaginacion, aplicar_orden, paginar
from app.utils.zona_horaria import ahora_utc

MODULO = "usuarios"

_ORDEN = {
    "nombre": Usuario.nombre_completo,
    "username": Usuario.username,
    "ultimo_acceso": Usuario.ultimo_acceso,
    "creado": Usuario.creado_en,
}


def _consulta_base():
    return select(Usuario).options(selectinload(Usuario.sucursales))


async def listar(
    session: AsyncSession,
    params: ParametrosPaginacion,
    *,
    busqueda: str | None = None,
    rol_id: int | None = None,
    activo: bool | None = None,
    sucursal_id: int | None = None,
    orden: str | None = None,
) -> tuple[list[Usuario], int]:
    consulta = _consulta_base()
    if busqueda:
        patron = f"%{busqueda.strip()}%"
        consulta = consulta.where(
            or_(Usuario.nombre_completo.ilike(patron), Usuario.username.ilike(patron), Usuario.email.ilike(patron))
        )
    if rol_id:
        consulta = consulta.where(Usuario.rol_id == rol_id)
    if activo is not None:
        consulta = consulta.where(Usuario.activo.is_(activo))
    if sucursal_id:
        consulta = consulta.where(Usuario.sucursales.any(Sucursal.id == sucursal_id))
    consulta = aplicar_orden(consulta, orden, _ORDEN, "nombre")
    return await paginar(session, consulta, params)


async def resumen(session: AsyncSession, inicio_hoy_utc: datetime) -> dict[str, int]:
    """Conteos para la cabecera de la pantalla de usuarios (una sola consulta)."""
    ahora = ahora_utc()

    # SUM(CASE ...) en vez de COUNT(...) FILTER: MySQL no soporta FILTER
    def contar(*condiciones):
        return func.coalesce(func.sum(case((and_(*condiciones), 1), else_=0)), 0)

    fila = (
        await session.execute(
            select(
                contar(Usuario.activo.is_(True)),
                contar(Usuario.activo.is_(False)),
                contar(Usuario.activo.is_(True), Usuario.bloqueado_hasta > ahora),
                contar(Usuario.ultimo_acceso >= inicio_hoy_utc),
            )
        )
    ).one()
    return {
        "con_acceso": int(fila[0]),
        "sin_acceso": int(fila[1]),
        "bloqueados": int(fila[2]),
        "ingresaron_hoy": int(fila[3]),
    }


async def obtener(session: AsyncSession, usuario_id: int, *, bloquear: bool = False) -> Usuario:
    consulta = _consulta_base().where(Usuario.id == usuario_id)
    if bloquear:
        consulta = consulta.with_for_update()
    usuario = await session.scalar(consulta)
    if usuario is None:
        raise NoEncontrado("El usuario no existe")
    return usuario


async def _validar_rol(session: AsyncSession, rol_id: int) -> Rol:
    rol = await session.get(Rol, rol_id)
    if rol is None or not rol.activo:
        raise ValidacionNegocio("El rol seleccionado no existe o está inactivo", codigo="rol_invalido")
    return rol


async def _validar_sucursales(session: AsyncSession, ids: list[int], predeterminada: int | None) -> list[Sucursal]:
    ids_unicos = set(ids)
    sucursales = list((await session.scalars(select(Sucursal).where(Sucursal.id.in_(ids_unicos)))).all())
    if len(sucursales) != len(ids_unicos) or any(not s.activo for s in sucursales):
        raise ValidacionNegocio("Alguna de las sucursales no existe o está inactiva", codigo="sucursal_invalida")
    if predeterminada is not None and predeterminada not in ids_unicos:
        raise ValidacionNegocio(
            "La sucursal predeterminada debe estar entre las sucursales asignadas", codigo="sucursal_invalida"
        )
    return sucursales


async def _validar_unicos(session: AsyncSession, username: str | None, email: str | None, excluir_id: int | None):
    if username:
        existe = await session.scalar(
            select(Usuario.id).where(Usuario.username == username, Usuario.id != (excluir_id or 0))
        )
        if existe:
            raise Conflicto(f"El usuario «{username}» ya existe", codigo="username_duplicado")
    if email:
        existe = await session.scalar(select(Usuario.id).where(Usuario.email == email, Usuario.id != (excluir_id or 0)))
        if existe:
            raise Conflicto(f"El correo «{email}» ya está registrado", codigo="email_duplicado")


async def _es_ultimo_admin_activo(session: AsyncSession, usuario: Usuario) -> bool:
    """True si el usuario es el único administrador activo (el sistema no puede quedarse sin uno)."""
    if usuario.rol.nombre != ROL_ADMINISTRADOR or not usuario.activo:
        return False
    otros = await session.scalar(
        select(func.count(Usuario.id))
        .join(Rol, Rol.id == Usuario.rol_id)
        .where(Rol.nombre == ROL_ADMINISTRADOR, Usuario.activo.is_(True), Usuario.id != usuario.id)
    )
    return otros == 0


async def crear(session: AsyncSession, ctx: ContextoUsuario, datos: UsuarioCrear) -> Usuario:
    email = str(datos.email).lower() if datos.email else None
    await _validar_unicos(session, datos.username, email, None)
    await _validar_rol(session, datos.rol_id)
    sucursales = await _validar_sucursales(session, datos.sucursal_ids, datos.sucursal_predeterminada_id)

    usuario = Usuario(
        nombre_completo=datos.nombre_completo,
        username=datos.username,
        email=email,
        password_hash=hash_password(datos.password),
        rol_id=datos.rol_id,
        debe_cambiar_password=datos.debe_cambiar_password,
        password_actualizado_en=ahora_utc(),
        sucursal_predeterminada_id=datos.sucursal_predeterminada_id or sucursales[0].id,
        sucursales=sucursales,
    )
    session.add(usuario)
    await session.flush()
    auditoria.registrar(
        session,
        accion="CREAR",
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad="usuario",
        entidad_id=usuario.id,
        descripcion=f"Creó el usuario {usuario.username}",
        datos={"rol_id": datos.rol_id, "sucursales": datos.sucursal_ids},
        ip=ctx.ip,
    )
    await session.commit()
    return await obtener(session, usuario.id)


async def actualizar(session: AsyncSession, ctx: ContextoUsuario, usuario_id: int, datos: UsuarioActualizar) -> Usuario:
    usuario = await obtener(session, usuario_id, bloquear=True)
    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        return usuario
    antes: dict[str, object] = {}

    if "email" in cambios:
        cambios["email"] = str(cambios["email"]).lower() if cambios["email"] else None
        await _validar_unicos(session, None, cambios["email"], usuario.id)

    if cambios.get("activo") is False:
        if usuario.id == ctx.usuario_id:
            raise ValidacionNegocio("No puede desactivar su propio usuario", codigo="auto_desactivacion")
        if await _es_ultimo_admin_activo(session, usuario):
            raise ValidacionNegocio("No se puede desactivar al único administrador activo", codigo="ultimo_admin")

    if "rol_id" in cambios and cambios["rol_id"] != usuario.rol_id:
        if cambios["rol_id"] is None:
            raise ValidacionNegocio("Debe indicar un rol", codigo="rol_invalido")
        nuevo_rol = await _validar_rol(session, cambios["rol_id"])
        if nuevo_rol.nombre != ROL_ADMINISTRADOR and await _es_ultimo_admin_activo(session, usuario):
            raise ValidacionNegocio(
                "No se puede quitar el rol de administrador al único administrador activo", codigo="ultimo_admin"
            )
        if usuario.id == ctx.usuario_id:
            raise ValidacionNegocio("No puede cambiar su propio rol", codigo="auto_cambio_rol")

    ids_sucursales = cambios.pop("sucursal_ids", None)
    predeterminada = cambios.get("sucursal_predeterminada_id", usuario.sucursal_predeterminada_id)
    if ids_sucursales is not None:
        usuario.sucursales = await _validar_sucursales(session, ids_sucursales, None)
        antes["sucursales"] = ids_sucursales
        if predeterminada not in set(ids_sucursales):
            predeterminada = ids_sucursales[0]
    elif predeterminada is not None and predeterminada not in {s.id for s in usuario.sucursales}:
        raise ValidacionNegocio(
            "La sucursal predeterminada debe estar entre las sucursales asignadas", codigo="sucursal_invalida"
        )
    usuario.sucursal_predeterminada_id = predeterminada
    cambios.pop("sucursal_predeterminada_id", None)

    for campo, valor in cambios.items():
        antes[campo] = getattr(usuario, campo)
        setattr(usuario, campo, valor)

    if cambios.get("activo") is False:
        await revocar_sesiones(session, usuario.id, "DESACTIVADO")

    auditoria.registrar(
        session,
        accion="EDITAR",
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad="usuario",
        entidad_id=usuario.id,
        descripcion=f"Editó el usuario {usuario.username}",
        datos={"campos": sorted([*cambios.keys(), *(["sucursales"] if ids_sucursales is not None else [])])},
        ip=ctx.ip,
    )
    await session.commit()
    return await obtener(session, usuario.id)


async def restablecer_password(
    session: AsyncSession, ctx: ContextoUsuario, usuario_id: int, datos: RestablecerPassword
) -> None:
    usuario = await obtener(session, usuario_id, bloquear=True)
    usuario.password_hash = hash_password(datos.password)
    usuario.debe_cambiar_password = datos.debe_cambiar_password
    usuario.password_actualizado_en = ahora_utc()
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    await revocar_sesiones(session, usuario.id, "ADMIN")
    auditoria.registrar(
        session,
        accion="RESTABLECER_PASSWORD",
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad="usuario",
        entidad_id=usuario.id,
        descripcion=f"Restableció la contraseña de {usuario.username}",
        ip=ctx.ip,
    )
    await session.commit()


async def desbloquear(session: AsyncSession, ctx: ContextoUsuario, usuario_id: int) -> Usuario:
    usuario = await obtener(session, usuario_id, bloquear=True)
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    auditoria.registrar(
        session,
        accion="DESBLOQUEAR",
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad="usuario",
        entidad_id=usuario.id,
        descripcion=f"Desbloqueó al usuario {usuario.username}",
        ip=ctx.ip,
    )
    await session.commit()
    return await obtener(session, usuario.id)


async def cerrar_sesiones(session: AsyncSession, ctx: ContextoUsuario, usuario_id: int) -> None:
    usuario = await obtener(session, usuario_id)
    await revocar_sesiones(session, usuario.id, "ADMIN")
    auditoria.registrar(
        session,
        accion="CERRAR_SESIONES",
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad="usuario",
        entidad_id=usuario.id,
        descripcion=f"Cerró todas las sesiones de {usuario.username}",
        ip=ctx.ip,
    )
    await session.commit()
