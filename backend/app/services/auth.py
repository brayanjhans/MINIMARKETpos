"""Autenticación: login con bloqueo por intentos, refresh tokens rotativos y cambio de sucursal."""

from dataclasses import dataclass
from datetime import timedelta
from functools import cache

import jwt
from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.excepciones import NoAutenticado, PermisoDenegado, ValidacionNegocio
from app.core.security import (
    crear_access_token,
    crear_refresh_token,
    decodificar_token,
    hash_identificador,
    hash_password,
    segundos_access_token,
    verify_password,
)
from app.dependencies.auth import ContextoUsuario, cargar_usuario
from app.models import RefreshToken, Rol, Sucursal, Usuario
from app.schemas.auth import CambiarPasswordEntrada, LoginEntrada, TokenRespuesta, UsuarioSesion
from app.schemas.roles import RolResumen
from app.schemas.sucursales import SucursalResumen
from app.services import auditoria, parametros
from app.utils.zona_horaria import ahora_utc

MODULO = "auth"
MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos"


@dataclass(slots=True)
class ResultadoSesion:
    respuesta: TokenRespuesta
    refresh_token: str | None  # None cuando no cambia la cookie


@cache
def _hash_ficticio() -> str:
    # Se usa para que un usuario inexistente tarde lo mismo que uno real (evita enumerar usuarios)
    return hash_password("contraseña-ficticia-123")


def construir_sesion(usuario: Usuario, sucursal_id: int) -> UsuarioSesion:
    sucursales = [s for s in usuario.sucursales if s.activo]
    actual = next(s for s in sucursales if s.id == sucursal_id)
    return UsuarioSesion(
        id=usuario.id,
        nombre_completo=usuario.nombre_completo,
        username=usuario.username,
        email=usuario.email,
        rol=RolResumen.model_validate(usuario.rol),
        permisos=sorted(p.codigo for p in usuario.rol.permisos),
        sucursales=[SucursalResumen.model_validate(s) for s in sorted(sucursales, key=lambda s: s.nombre)],
        sucursal_actual=SucursalResumen.model_validate(actual),
        debe_cambiar_password=usuario.debe_cambiar_password,
    )


def _respuesta(usuario: Usuario, sucursal_id: int) -> TokenRespuesta:
    return TokenRespuesta(
        access_token=crear_access_token(usuario.id, {"suc": sucursal_id}),
        expira_en=segundos_access_token(),
        usuario=construir_sesion(usuario, sucursal_id),
    )


def _elegir_sucursal(usuario: Usuario, solicitada: int | None) -> int:
    permitidas = {s.id for s in usuario.sucursales if s.activo}
    if not permitidas:
        raise PermisoDenegado("Su usuario no tiene sucursales asignadas. Contacte al administrador.")
    if solicitada is not None:
        if solicitada not in permitidas:
            raise PermisoDenegado("No tiene acceso a la sucursal seleccionada")
        return solicitada
    if usuario.sucursal_predeterminada_id in permitidas:
        return usuario.sucursal_predeterminada_id  # type: ignore[return-value]
    return min(permitidas)


def _nuevo_refresh(
    session: AsyncSession, usuario_id: int, sucursal_id: int, ip: str | None, user_agent: str | None
) -> str:
    token, jti, expira = crear_refresh_token(usuario_id)
    session.add(
        RefreshToken(
            usuario_id=usuario_id,
            sucursal_id=sucursal_id,
            jti_hash=hash_identificador(jti),
            expira_en=expira,
            ip=ip,
            user_agent=(user_agent or "")[:300] or None,
        )
    )
    return token


async def revocar_sesiones(
    session: AsyncSession, usuario_id: int, motivo: str, *, excepto_id: int | None = None
) -> None:
    consulta = (
        update(RefreshToken)
        .where(RefreshToken.usuario_id == usuario_id, RefreshToken.revocado.is_(False))
        .values(revocado=True, revocado_en=ahora_utc(), motivo_revocacion=motivo)
    )
    if excepto_id is not None:
        consulta = consulta.where(RefreshToken.id != excepto_id)
    await session.execute(consulta)


async def login(session: AsyncSession, datos: LoginEntrada, ip: str | None, user_agent: str | None) -> ResultadoSesion:
    username = datos.username.strip().lower()
    usuario = await session.scalar(
        select(Usuario)
        .where(Usuario.username == username)
        .options(selectinload(Usuario.rol).selectinload(Rol.permisos), selectinload(Usuario.sucursales))
        .with_for_update()
    )
    ahora = ahora_utc()

    if usuario is None:
        verify_password(datos.password, _hash_ficticio())
        auditoria.registrar(
            session, accion="LOGIN_FALLIDO", modulo=MODULO, descripcion=f"Usuario inexistente: {username[:50]}", ip=ip
        )
        await session.commit()
        raise NoAutenticado(MENSAJE_CREDENCIALES, codigo="credenciales_invalidas")

    if usuario.bloqueado_hasta and usuario.bloqueado_hasta > ahora:
        minutos = max(1, int((usuario.bloqueado_hasta - ahora).total_seconds() // 60) + 1)
        await session.rollback()
        raise NoAutenticado(
            f"Usuario bloqueado por intentos fallidos. Intente nuevamente en {minutos} minuto(s).",
            codigo="usuario_bloqueado",
        )

    if not verify_password(datos.password, usuario.password_hash):
        max_intentos = await parametros.obtener(session, "seguridad.max_intentos_login")
        usuario.intentos_fallidos += 1
        descripcion = f"Contraseña incorrecta (intento {usuario.intentos_fallidos})"
        if usuario.intentos_fallidos >= max_intentos:
            minutos_bloqueo = await parametros.obtener(session, "seguridad.minutos_bloqueo")
            usuario.bloqueado_hasta = ahora + timedelta(minutes=minutos_bloqueo)
            usuario.intentos_fallidos = 0
            descripcion = f"Usuario bloqueado {minutos_bloqueo} min por {max_intentos} intentos fallidos"
        auditoria.registrar(
            session,
            accion="LOGIN_FALLIDO",
            modulo=MODULO,
            usuario_id=usuario.id,
            entidad="usuario",
            entidad_id=usuario.id,
            descripcion=descripcion,
            ip=ip,
        )
        await session.commit()
        raise NoAutenticado(MENSAJE_CREDENCIALES, codigo="credenciales_invalidas")

    if not usuario.activo or not usuario.rol.activo:
        await session.rollback()
        raise NoAutenticado("Su usuario está inactivo. Contacte al administrador.", codigo="usuario_inactivo")

    sucursal_id = _elegir_sucursal(usuario, datos.sucursal_id)
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    usuario.ultimo_acceso = ahora
    # Limpieza de sesiones vencidas o revocadas hace más de un día
    await session.execute(
        delete(RefreshToken).where(
            RefreshToken.usuario_id == usuario.id,
            or_(RefreshToken.expira_en < ahora, RefreshToken.revocado_en < ahora - timedelta(days=1)),
        )
    )
    refresh = _nuevo_refresh(session, usuario.id, sucursal_id, ip, user_agent)
    auditoria.registrar(
        session,
        accion="LOGIN",
        modulo=MODULO,
        usuario_id=usuario.id,
        sucursal_id=sucursal_id,
        descripcion="Inicio de sesión",
        ip=ip,
    )
    respuesta = _respuesta(usuario, sucursal_id)
    await session.commit()
    return ResultadoSesion(respuesta, refresh)


async def _token_refresh_valido(session: AsyncSession, refresh_token: str | None) -> RefreshToken:
    """Busca la sesión del refresh token (bloqueando la fila)."""
    if not refresh_token:
        raise NoAutenticado("Debe iniciar sesión", codigo="sin_sesion")
    try:
        payload = decodificar_token(refresh_token, "refresh")
    except jwt.PyJWTError as exc:
        raise NoAutenticado("Su sesión expiró. Inicie sesión nuevamente.", codigo="sesion_expirada") from exc
    registro = await session.scalar(
        select(RefreshToken).where(RefreshToken.jti_hash == hash_identificador(payload["jti"])).with_for_update()
    )
    if registro is None:
        raise NoAutenticado("Su sesión expiró. Inicie sesión nuevamente.", codigo="sesion_expirada")
    return registro


async def refrescar(
    session: AsyncSession, refresh_token: str | None, ip: str | None, user_agent: str | None
) -> ResultadoSesion:
    registro = await _token_refresh_valido(session, refresh_token)
    ahora = ahora_utc()

    if registro.revocado:
        dentro_de_gracia = (
            registro.motivo_revocacion == "ROTACION"
            and registro.revocado_en is not None
            and ahora - registro.revocado_en < timedelta(seconds=settings.REFRESH_GRACIA_SEGUNDOS)
        )
        if not dentro_de_gracia:
            # Reutilización de un token ya usado: posible robo -> se cierran todas las sesiones
            if registro.motivo_revocacion == "ROTACION":
                await revocar_sesiones(session, registro.usuario_id, "ROBO")
                auditoria.registrar(
                    session,
                    accion="SESION_REVOCADA",
                    modulo=MODULO,
                    usuario_id=registro.usuario_id,
                    descripcion="Reutilización de refresh token: se cerraron todas las sesiones",
                    ip=ip,
                )
                await session.commit()
            raise NoAutenticado("Su sesión fue cerrada. Inicie sesión nuevamente.", codigo="sesion_revocada")

    usuario = await cargar_usuario(session, registro.usuario_id)
    if usuario is None or not usuario.activo or not usuario.rol.activo:
        raise NoAutenticado("Su usuario está inactivo. Contacte al administrador.", codigo="usuario_inactivo")
    sucursales = {s.id for s in usuario.sucursales if s.activo}
    if not sucursales:
        raise NoAutenticado("Su usuario no tiene sucursales asignadas.", codigo="sin_sucursal")
    sucursal_id = registro.sucursal_id if registro.sucursal_id in sucursales else _elegir_sucursal(usuario, None)

    if not registro.revocado:
        registro.revocado = True
        registro.revocado_en = ahora
        registro.motivo_revocacion = "ROTACION"
    nuevo = _nuevo_refresh(session, usuario.id, sucursal_id, ip, user_agent)
    respuesta = _respuesta(usuario, sucursal_id)
    await session.commit()
    return ResultadoSesion(respuesta, nuevo)


async def logout(session: AsyncSession, refresh_token: str | None, ip: str | None) -> None:
    try:
        registro = await _token_refresh_valido(session, refresh_token)
    except NoAutenticado:
        return  # sin sesión válida no hay nada que cerrar
    if not registro.revocado:
        registro.revocado = True
        registro.revocado_en = ahora_utc()
        registro.motivo_revocacion = "LOGOUT"
    auditoria.registrar(
        session,
        accion="LOGOUT",
        modulo=MODULO,
        usuario_id=registro.usuario_id,
        sucursal_id=registro.sucursal_id,
        descripcion="Cierre de sesión",
        ip=ip,
    )
    await session.commit()


async def cambiar_sucursal(
    session: AsyncSession, ctx: ContextoUsuario, refresh_token: str | None, sucursal_id: int
) -> TokenRespuesta:
    registro = await _token_refresh_valido(session, refresh_token)
    if registro.usuario_id != ctx.usuario_id or registro.revocado:
        raise NoAutenticado("Su sesión expiró. Inicie sesión nuevamente.", codigo="sesion_expirada")
    nueva = _elegir_sucursal(ctx.usuario, sucursal_id)
    anterior = registro.sucursal_id
    registro.sucursal_id = nueva
    sucursal = await session.get(Sucursal, nueva)
    auditoria.registrar(
        session,
        accion="CAMBIAR_SUCURSAL",
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=nueva,
        descripcion=f"Cambió a la sucursal {sucursal.nombre if sucursal else nueva}",
        datos={"anterior": anterior, "nueva": nueva},
        ip=ctx.ip,
    )
    respuesta = _respuesta(ctx.usuario, nueva)
    await session.commit()
    return respuesta


async def cambiar_password(
    session: AsyncSession, ctx: ContextoUsuario, datos: CambiarPasswordEntrada, refresh_token: str | None
) -> TokenRespuesta:
    usuario = ctx.usuario
    if not verify_password(datos.password_actual, usuario.password_hash):
        raise ValidacionNegocio("La contraseña actual es incorrecta", codigo="password_incorrecto")
    if verify_password(datos.password_nueva, usuario.password_hash):
        raise ValidacionNegocio("La nueva contraseña debe ser distinta de la actual", codigo="password_repetido")

    registro_actual: RefreshToken | None = None
    try:
        registro_actual = await _token_refresh_valido(session, refresh_token)
    except NoAutenticado:
        pass

    usuario.password_hash = hash_password(datos.password_nueva)
    usuario.debe_cambiar_password = False
    usuario.password_actualizado_en = ahora_utc()
    # Cierra las demás sesiones abiertas del usuario (otros equipos)
    await revocar_sesiones(
        session, usuario.id, "CAMBIO_PASSWORD", excepto_id=registro_actual.id if registro_actual else None
    )
    auditoria.registrar(
        session,
        accion="CAMBIAR_PASSWORD",
        modulo=MODULO,
        usuario_id=usuario.id,
        sucursal_id=ctx.sucursal_id,
        entidad="usuario",
        entidad_id=usuario.id,
        descripcion="Cambió su contraseña",
        ip=ctx.ip,
    )
    respuesta = _respuesta(usuario, ctx.sucursal_id)
    await session.commit()
    return respuesta
