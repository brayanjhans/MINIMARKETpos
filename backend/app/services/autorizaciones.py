"""Autorización de un supervisor en la misma caja (anular una venta, descuento mayor al permitido, vender sin stock).

1. El supervisor escribe su usuario y contraseña en la caja: `autorizar` los verifica (con el mismo bloqueo por
   intentos fallidos que el login) y devuelve un token corto, válido solo para ESE permiso, ESE cajero y esa
   sucursal, durante pocos minutos.
2. La operación recibe el token y `consumir` lo valida y lo marca como usado en la misma transacción: no se puede
   reutilizar (si la operación falla, la transacción se revierte y el token sigue sirviendo para reintentar).
3. Queda en la auditoría quién autorizó.
"""

from dataclasses import dataclass
from datetime import timedelta

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constantes import CATALOGO_PERMISOS
from app.core.excepciones import NoAutenticado, PermisoDenegado, ValidacionNegocio
from app.core.security import crear_token_autorizacion, decodificar_token, verify_password
from app.dependencies.auth import ContextoUsuario, cargar_usuario
from app.models import OperacionIdempotente, Rol, Usuario
from app.services import auditoria, parametros
from app.services.auth import MENSAJE_CREDENCIALES, _hash_ficticio
from app.utils.zona_horaria import ahora_utc

MODULO = "auth"
MINUTOS_VALIDEZ = 3
# Acciones que un supervisor puede autorizar desde la caja de otro usuario
AUTORIZABLES = {"pos.anular_venta", "pos.aplicar_descuento", "pos.vender_sin_stock", "pos.venta_credito"}


def descripcion_permiso(permiso: str) -> str:
    modulo, accion = permiso.split(".", 1)
    return CATALOGO_PERMISOS.get(modulo, {}).get(accion, permiso)


@dataclass(slots=True, frozen=True)
class Autorizacion:
    supervisor_id: int
    supervisor: str
    permiso: str


def _usuario_con_permiso(usuario: Usuario, permiso: str, sucursal_id: int) -> bool:
    return (
        usuario.activo
        and usuario.rol.activo
        and permiso in {p.codigo for p in usuario.rol.permisos}
        and sucursal_id in {s.id for s in usuario.sucursales if s.activo}
    )


async def autorizar(
    session: AsyncSession, ctx: ContextoUsuario, username: str, password: str, permiso: str
) -> tuple[str, str]:
    """Verifica la clave del supervisor y devuelve (token, nombre del supervisor)."""
    if permiso not in AUTORIZABLES:
        raise ValidacionNegocio("Esa acción no se puede autorizar desde la caja", codigo="permiso_no_autorizable")
    username = username.strip().lower()
    supervisor = await session.scalar(
        select(Usuario)
        .where(Usuario.username == username)
        .options(selectinload(Usuario.rol).selectinload(Rol.permisos), selectinload(Usuario.sucursales))
        .with_for_update()
    )
    ahora = ahora_utc()
    if supervisor is None:
        verify_password(password, _hash_ficticio())  # mismo tiempo de respuesta que con un usuario real
        auditoria.registrar(
            session,
            accion="AUTORIZACION_FALLIDA",
            modulo=MODULO,
            usuario_id=ctx.usuario_id,
            sucursal_id=ctx.sucursal_id,
            descripcion=f"Supervisor inexistente: {username[:50]}",
            ip=ctx.ip,
        )
        await session.commit()
        raise NoAutenticado(MENSAJE_CREDENCIALES, codigo="credenciales_invalidas")

    if supervisor.bloqueado_hasta and supervisor.bloqueado_hasta > ahora:
        await session.rollback()
        raise NoAutenticado("Ese usuario está bloqueado por intentos fallidos", codigo="usuario_bloqueado")

    if not verify_password(password, supervisor.password_hash):
        max_intentos = await parametros.obtener(session, "seguridad.max_intentos_login")
        supervisor.intentos_fallidos += 1
        if supervisor.intentos_fallidos >= max_intentos:
            supervisor.bloqueado_hasta = ahora + timedelta(
                minutes=await parametros.obtener(session, "seguridad.minutos_bloqueo")
            )
            supervisor.intentos_fallidos = 0
        auditoria.registrar(
            session,
            accion="AUTORIZACION_FALLIDA",
            modulo=MODULO,
            usuario_id=ctx.usuario_id,
            sucursal_id=ctx.sucursal_id,
            entidad="usuario",
            entidad_id=supervisor.id,
            descripcion=f"Clave incorrecta de {supervisor.username} para «{descripcion_permiso(permiso)}»",
            ip=ctx.ip,
        )
        await session.commit()
        raise NoAutenticado(MENSAJE_CREDENCIALES, codigo="credenciales_invalidas")

    nombre = supervisor.nombre_completo  # antes del rollback, que expira el objeto
    if not _usuario_con_permiso(supervisor, permiso, ctx.sucursal_id):
        await session.rollback()
        raise PermisoDenegado(
            f"{nombre} no tiene permiso para «{descripcion_permiso(permiso)}» en esta sucursal",
            codigo="supervisor_sin_permiso",
        )
    supervisor.intentos_fallidos = 0
    token, _ = crear_token_autorizacion(
        supervisor.id,
        {"permiso": permiso, "para": ctx.usuario_id, "suc": ctx.sucursal_id},
        MINUTOS_VALIDEZ,
    )
    await session.commit()
    return token, nombre


def leer(ctx: ContextoUsuario, token: str) -> tuple[int, str, str]:
    """Valida firma, vigencia y destinatario del token (sin consumirlo). Devuelve (supervisor_id, permiso, jti)."""
    try:
        payload = decodificar_token(token, "autorizacion")
        supervisor_id = int(payload["sub"])
        permiso = str(payload["permiso"])
        para, sucursal = int(payload["para"]), int(payload["suc"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise ValidacionNegocio(
            "La autorización del supervisor venció o no es válida: pídala de nuevo", codigo="autorizacion_invalida"
        ) from exc
    if para != ctx.usuario_id or sucursal != ctx.sucursal_id:
        raise ValidacionNegocio("La autorización es para otra caja", codigo="autorizacion_invalida")
    return supervisor_id, permiso, payload["jti"]


class Autorizador:
    """Resuelve si el usuario puede hacer una acción: por su propio permiso o con la autorización de un
    supervisor. Cada token se consume (una sola vez) recién cuando de verdad se usa."""

    def __init__(self, session: AsyncSession, ctx: ContextoUsuario, tokens: list[str] | None):
        self.session = session
        self.ctx = ctx
        self._tokens: dict[str, tuple[int, str]] = {}
        for token in tokens or []:
            supervisor_id, permiso, jti = leer(ctx, token)
            self._tokens[permiso] = (supervisor_id, jti)
        self.usadas: list[Autorizacion] = []

    def disponible(self, permiso: str) -> bool:
        return self.ctx.tiene(permiso) or permiso in self._tokens

    async def exigir(self, permiso: str, mensaje: str, codigo: str, **datos) -> Autorizacion | None:
        """None si el usuario tiene el permiso; la autorización usada si la dio un supervisor."""
        if self.ctx.tiene(permiso):
            return None
        if permiso not in self._tokens:
            raise PermisoDenegado(mensaje, codigo=codigo, datos={"permiso": permiso, "autorizable": True, **datos})
        supervisor_id, jti = self._tokens.pop(permiso)
        usado = await self.session.scalar(
            select(OperacionIdempotente).where(
                OperacionIdempotente.usuario_id == supervisor_id, OperacionIdempotente.clave == f"aut-{jti}"
            )
        )
        if usado is not None:
            raise ValidacionNegocio("Esa autorización ya se usó: pídala de nuevo", codigo="autorizacion_usada")
        supervisor = await cargar_usuario(self.session, supervisor_id)
        # Se vuelve a revisar: pudieron quitarle el permiso o desactivarlo en estos minutos
        if supervisor is None or not _usuario_con_permiso(supervisor, permiso, self.ctx.sucursal_id):
            raise ValidacionNegocio("El supervisor ya no tiene ese permiso", codigo="autorizacion_invalida")
        # Si dos operaciones usan el mismo token a la vez, la clave primaria deja pasar solo a una
        self.session.add(
            OperacionIdempotente(usuario_id=supervisor_id, clave=f"aut-{jti}", operacion="autorizacion")
        )
        await self.session.flush()
        autorizacion = Autorizacion(supervisor_id, supervisor.nombre_completo, permiso)
        self.usadas.append(autorizacion)
        return autorizacion
