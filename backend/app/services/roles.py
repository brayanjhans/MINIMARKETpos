from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constantes import CATALOGO_PERMISOS, ETIQUETAS_MODULOS, ROL_ADMINISTRADOR
from app.core.excepciones import Conflicto, NoEncontrado, ValidacionNegocio
from app.dependencies.auth import ContextoUsuario
from app.models import Permiso, Rol, Usuario
from app.models.permiso import rol_permisos
from app.schemas.roles import ModuloPermisos, PermisoItem, RolActualizar, RolCrear, RolDetalle, RolListado
from app.services import auditoria

MODULO = "roles"


def catalogo() -> list[ModuloPermisos]:
    return [
        ModuloPermisos(
            modulo=modulo,
            etiqueta=ETIQUETAS_MODULOS.get(modulo, modulo.capitalize()),
            permisos=[
                PermisoItem(codigo=f"{modulo}.{accion}", accion=accion, descripcion=descripcion)
                for accion, descripcion in acciones.items()
            ],
        )
        for modulo, acciones in CATALOGO_PERMISOS.items()
    ]


async def listar(session: AsyncSession) -> list[RolListado]:
    total_usuarios = (
        select(func.count(Usuario.id)).where(Usuario.rol_id == Rol.id).correlate(Rol).scalar_subquery()
    )
    total_permisos = (
        select(func.count()).select_from(rol_permisos).where(rol_permisos.c.rol_id == Rol.id).correlate(Rol)
    ).scalar_subquery()
    consulta = select(Rol, total_usuarios, total_permisos).order_by(Rol.es_sistema.desc(), Rol.nombre)
    filas = await session.execute(consulta)
    return [
        RolListado.model_validate(rol).model_copy(update={"total_usuarios": usuarios, "total_permisos": permisos})
        for rol, usuarios, permisos in filas.all()
    ]


def _detalle(rol: Rol) -> RolDetalle:
    return RolDetalle(
        id=rol.id,
        nombre=rol.nombre,
        descripcion=rol.descripcion,
        es_sistema=rol.es_sistema,
        activo=rol.activo,
        permisos=sorted(p.codigo for p in rol.permisos),
        creado_en=rol.creado_en,
    )


async def _obtener_modelo(session: AsyncSession, rol_id: int) -> Rol:
    rol = await session.get(Rol, rol_id, with_for_update=True)
    if rol is None:
        raise NoEncontrado("El rol no existe")
    return rol


async def obtener(session: AsyncSession, rol_id: int) -> RolDetalle:
    rol = await session.get(Rol, rol_id)
    if rol is None:
        raise NoEncontrado("El rol no existe")
    return _detalle(rol)


async def _permisos_validos(session: AsyncSession, codigos: list[str]) -> list[Permiso]:
    unicos = set(codigos)
    permisos = list((await session.scalars(select(Permiso).where(Permiso.codigo.in_(unicos)))).all())
    desconocidos = unicos - {p.codigo for p in permisos}
    if desconocidos:
        raise ValidacionNegocio(
            "Hay permisos que no existen", codigo="permiso_invalido", datos={"permisos": sorted(desconocidos)}
        )
    return permisos


async def _validar_nombre(session: AsyncSession, nombre: str, excluir_id: int | None) -> None:
    existe = await session.scalar(select(Rol.id).where(Rol.nombre == nombre, Rol.id != (excluir_id or 0)))
    if existe:
        raise Conflicto(f"Ya existe un rol llamado «{nombre}»", codigo="rol_duplicado")


async def crear(session: AsyncSession, ctx: ContextoUsuario, datos: RolCrear) -> RolDetalle:
    await _validar_nombre(session, datos.nombre, None)
    rol = Rol(nombre=datos.nombre, descripcion=datos.descripcion, es_sistema=False)
    rol.permisos = await _permisos_validos(session, datos.permisos)
    session.add(rol)
    await session.flush()
    auditoria.registrar(
        session,
        accion="CREAR",
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad="rol",
        entidad_id=rol.id,
        descripcion=f"Creó el rol {rol.nombre}",
        datos={"permisos": sorted(datos.permisos)},
        ip=ctx.ip,
    )
    await session.commit()
    return await obtener(session, rol.id)


async def actualizar(session: AsyncSession, ctx: ContextoUsuario, rol_id: int, datos: RolActualizar) -> RolDetalle:
    rol = await _obtener_modelo(session, rol_id)
    cambios = datos.model_dump(exclude_unset=True)
    es_admin = rol.nombre == ROL_ADMINISTRADOR

    if rol.es_sistema and "nombre" in cambios and cambios["nombre"] != rol.nombre:
        raise ValidacionNegocio("Los roles del sistema no se pueden renombrar", codigo="rol_sistema")
    if es_admin and ("permisos" in cambios or cambios.get("activo") is False):
        raise ValidacionNegocio(
            "El rol Administrador siempre tiene todos los permisos y no se puede desactivar", codigo="rol_sistema"
        )
    if cambios.get("activo") is False and rol.id == ctx.usuario.rol_id:
        raise ValidacionNegocio("No puede desactivar su propio rol", codigo="auto_desactivacion")

    if "nombre" in cambios and cambios["nombre"]:
        await _validar_nombre(session, cambios["nombre"], rol.id)
        rol.nombre = cambios["nombre"]
    if "descripcion" in cambios:
        rol.descripcion = cambios["descripcion"]
    if cambios.get("activo") is not None:
        rol.activo = cambios["activo"]

    datos_auditoria: dict[str, object] = {"campos": sorted(cambios.keys())}
    if cambios.get("permisos") is not None:
        anteriores = {p.codigo for p in rol.permisos}
        nuevos = await _permisos_validos(session, cambios["permisos"])
        rol.permisos = nuevos
        codigos_nuevos = {p.codigo for p in nuevos}
        datos_auditoria["agregados"] = sorted(codigos_nuevos - anteriores)
        datos_auditoria["quitados"] = sorted(anteriores - codigos_nuevos)

    auditoria.registrar(
        session,
        accion="EDITAR",
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad="rol",
        entidad_id=rol.id,
        descripcion=f"Editó el rol {rol.nombre}",
        datos=datos_auditoria,
        ip=ctx.ip,
    )
    await session.commit()
    return await obtener(session, rol.id)


async def eliminar(session: AsyncSession, ctx: ContextoUsuario, rol_id: int) -> None:
    rol = await _obtener_modelo(session, rol_id)
    if rol.es_sistema:
        raise ValidacionNegocio("Los roles del sistema no se pueden eliminar", codigo="rol_sistema")
    usuarios = await session.scalar(select(func.count(Usuario.id)).where(Usuario.rol_id == rol.id))
    if usuarios:
        raise Conflicto(
            f"El rol tiene {usuarios} usuario(s) asignado(s). Reasígnelos antes de eliminarlo.", codigo="rol_en_uso"
        )
    nombre = rol.nombre
    await session.delete(rol)
    auditoria.registrar(
        session,
        accion="ELIMINAR",
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad="rol",
        entidad_id=rol_id,
        descripcion=f"Eliminó el rol {nombre}",
        ip=ctx.ip,
    )
    await session.commit()
