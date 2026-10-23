"""Caja: apertura con monto inicial, ingresos y egresos, cierre ciego con arqueo e historial por cajero.

Concurrencia: una venta bloquea su turno de caja en modo compartido (FOR SHARE) y el cierre lo bloquea en modo
exclusivo (FOR UPDATE). Así el cierre espera a que terminen las ventas en curso, ninguna venta entra en un turno
ya cerrado y el arqueo cuadra con lo vendido. La BD garantiza un solo turno abierto por cajero y por caja.

Cierre ciego: mientras el turno está abierto, quien no puede ver todas las cajas no ve el efectivo esperado ni los
montos por método de pago; cuenta billetes y monedas y recién al cerrar ve la diferencia.
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.excepciones import Conflicto, NoEncontrado, PermisoDenegado, ValidacionNegocio
from app.dependencies.auth import ContextoUsuario
from app.models import (
    Abono,
    ArqueoDenominacion,
    Caja,
    Devolucion,
    MovimientoCaja,
    PagoVenta,
    ResumenCierreCaja,
    SesionCaja,
    Usuario,
    Venta,
)
from app.models.base import CERO
from app.models.enums import EstadoSesionCaja, EstadoVenta, MetodoPago, TipoDenominacion, TipoMovimientoCaja
from app.schemas.caja import AperturaEntrada, CierreEntrada, MovimientoCajaEntrada
from app.services import auditoria, parametros, transacciones
from app.services.inventario import nombres_usuarios
from app.utils.paginacion import ParametrosPaginacion, paginar
from app.utils.zona_horaria import a_utc, ahora_utc

MODULO = "caja"
VER_TODAS = "caja.ver_todas"
BILLETE_DESDE = Decimal("10")  # en soles: de 10 para arriba son billetes


# --- Turno abierto ----------------------------------------------------------------------------------------


async def sesion_abierta(session: AsyncSession, usuario_id: int, *, bloqueo: str | None = None) -> SesionCaja | None:
    """Turno abierto del usuario. bloqueo: None, "compartido" (ventas) o "exclusivo" (movimientos, cierre)."""
    consulta = select(SesionCaja).where(SesionCaja.usuario_abierta_id == usuario_id)
    if bloqueo == "compartido":
        consulta = consulta.with_for_update(read=True, of=SesionCaja)
    elif bloqueo == "exclusivo":
        consulta = consulta.with_for_update(of=SesionCaja)
    return await session.scalar(consulta.execution_options(populate_existing=True))


async def exigir_turno(session: AsyncSession, ctx: ContextoUsuario, *, bloqueo: str = "compartido") -> SesionCaja:
    """Turno abierto del usuario en la sucursal en la que trabaja (no se vende sin caja abierta)."""
    sesion = await sesion_abierta(session, ctx.usuario_id, bloqueo=bloqueo)
    if sesion is None:
        raise ValidacionNegocio("Abra su caja antes de vender", codigo="caja_cerrada")
    caja = await session.get(Caja, sesion.caja_id)
    if caja.sucursal_id != ctx.sucursal_id:
        raise ValidacionNegocio(
            f"Su caja abierta ({caja.nombre}) es de otra sucursal: ciérrela o cambie de sucursal",
            codigo="caja_otra_sucursal",
        )
    return sesion


async def _cargar(session: AsyncSession, sesion_id: int, *, bloquear: bool = False) -> SesionCaja:
    consulta = select(SesionCaja).where(SesionCaja.id == sesion_id)
    if bloquear:
        consulta = consulta.with_for_update(of=SesionCaja)
    sesion = await session.scalar(consulta.execution_options(populate_existing=True))
    if sesion is None:
        raise NoEncontrado("El turno de caja no existe")
    return sesion


def _puede_ver(ctx: ContextoUsuario, sesion: SesionCaja) -> bool:
    return sesion.usuario_id == ctx.usuario_id or (
        ctx.tiene(VER_TODAS) and sesion.caja.sucursal_id == ctx.sucursal_id
    )


def _ve_esperado(ctx: ContextoUsuario, sesion: SesionCaja) -> bool:
    return sesion.estado == EstadoSesionCaja.CERRADA or ctx.tiene(VER_TODAS)


# --- Totales del turno ------------------------------------------------------------------------------------


async def totales(session: AsyncSession, sesion: SesionCaja, *, bloquear: bool = False) -> dict[str, Any]:
    """Ventas, pagos por método, ingresos/egresos y efectivo esperado de un turno.

    Con `bloquear` las sumas se leen con FOR SHARE: así ven lo último confirmado aunque la transacción ya haya
    leído antes (REPEATABLE READ) — lo usa el cierre.
    """

    def leer(consulta):
        return consulta.with_for_update(read=True) if bloquear else consulta

    valida = Venta.estado != EstadoVenta.ANULADA
    fila_ventas = (
        await session.execute(
            leer(
                select(
                    func.coalesce(func.sum(case((valida, 1), else_=0)), 0),
                    func.coalesce(func.sum(case((Venta.estado == EstadoVenta.ANULADA, 1), else_=0)), 0),
                    func.coalesce(func.sum(case((valida, Venta.total + Venta.redondeo), else_=0)), 0),
                ).where(Venta.sesion_caja_id == sesion.id)
            )
        )
    ).one()
    por_metodo = {
        metodo: (int(ops), Decimal(monto))
        for metodo, ops, monto in (
            await session.execute(
                leer(
                    select(PagoVenta.metodo, func.count(), func.coalesce(func.sum(PagoVenta.monto), 0))
                    .join(Venta, Venta.id == PagoVenta.venta_id)
                    .where(Venta.sesion_caja_id == sesion.id, valida)
                    .group_by(PagoVenta.metodo)
                )
            )
        ).tuples()
    }
    movimientos = dict(
        (
            await session.execute(
                leer(
                    select(MovimientoCaja.tipo, func.coalesce(func.sum(MovimientoCaja.monto), 0))
                    .where(MovimientoCaja.sesion_caja_id == sesion.id)
                    .group_by(MovimientoCaja.tipo)
                )
            )
        )
        .tuples()
        .all()
    )
    abonos = await session.scalar(
        leer(
            select(func.coalesce(func.sum(Abono.monto), 0)).where(
                Abono.sesion_caja_id == sesion.id, Abono.metodo == MetodoPago.EFECTIVO
            )
        )
    )
    reembolsos = await session.scalar(
        leer(
            select(func.coalesce(func.sum(Devolucion.total), 0)).where(
                Devolucion.sesion_caja_id == sesion.id, Devolucion.metodo_reembolso == MetodoPago.EFECTIVO
            )
        )
    )
    ingresos = Decimal(movimientos.get(TipoMovimientoCaja.INGRESO, 0))
    egresos = Decimal(movimientos.get(TipoMovimientoCaja.EGRESO, 0))
    efectivo = por_metodo.get(MetodoPago.EFECTIVO, (0, CERO))[1]
    return {
        "ventas": int(fila_ventas[0]),
        "anuladas": int(fila_ventas[1]),
        "total_vendido": Decimal(fila_ventas[2]),
        "por_metodo": por_metodo,
        "ingresos": ingresos,
        "egresos": egresos,
        "abonos_efectivo": Decimal(abonos),
        "reembolsos_efectivo": Decimal(reembolsos),
        "efectivo_esperado": sesion.monto_inicial + efectivo + Decimal(abonos) + ingresos - egresos
        - Decimal(reembolsos),
    }


# --- Consultas --------------------------------------------------------------------------------------------


async def cajas(session: AsyncSession, ctx: ContextoUsuario) -> list[dict[str, Any]]:
    filas = await session.execute(
        select(Caja, SesionCaja)
        .outerjoin(SesionCaja, SesionCaja.caja_abierta_id == Caja.id)
        .where(Caja.sucursal_id == ctx.sucursal_id, Caja.activo.is_(True))
        .order_by(Caja.nombre)
    )
    resultado = []
    for caja, sesion in filas.tuples():
        resultado.append(
            {
                "id": caja.id,
                "nombre": caja.nombre,
                "descripcion": caja.descripcion,
                "sesion_id": sesion.id if sesion else None,
                "abierta_por": sesion.usuario.nombre_completo if sesion else None,
                "abierta_desde": sesion.fecha_apertura if sesion else None,
                "es_mia": bool(sesion and sesion.usuario_id == ctx.usuario_id),
            }
        )
    return resultado


def _salida(ctx: ContextoUsuario, sesion: SesionCaja, t: dict[str, Any]) -> dict[str, Any]:
    ve = _ve_esperado(ctx, sesion)
    return {
        "id": sesion.id,
        "caja_id": sesion.caja_id,
        "caja": sesion.caja.nombre,
        "sucursal": sesion.caja.sucursal.nombre,
        "usuario_id": sesion.usuario_id,
        "usuario": sesion.usuario.nombre_completo,
        "estado": sesion.estado,
        "fecha_apertura": sesion.fecha_apertura,
        "fecha_cierre": sesion.fecha_cierre,
        "monto_inicial": sesion.monto_inicial,
        "ventas": t["ventas"],
        "anuladas": t["anuladas"],
        "total_vendido": t["total_vendido"] if ve else None,
        "ingresos": t["ingresos"],
        "egresos": t["egresos"],
        "efectivo_esperado": (
            (sesion.monto_esperado if sesion.monto_esperado is not None else t["efectivo_esperado"]) if ve else None
        ),
        "monto_contado": sesion.monto_contado,
        "diferencia": sesion.diferencia,
        "observaciones_apertura": sesion.observaciones_apertura,
        "observaciones_cierre": sesion.observaciones_cierre,
        "puede_ver_esperado": ve,
    }


async def actual(session: AsyncSession, ctx: ContextoUsuario) -> dict[str, Any]:
    sesion = await sesion_abierta(session, ctx.usuario_id)
    if sesion is None:
        return {"sesion": None, "sucursal_distinta": False}
    return {
        "sesion": _salida(ctx, sesion, await totales(session, sesion)),
        "sucursal_distinta": sesion.caja.sucursal_id != ctx.sucursal_id,
    }


async def detalle(session: AsyncSession, ctx: ContextoUsuario, sesion_id: int) -> dict[str, Any]:
    sesion = await session.scalar(
        select(SesionCaja)
        .where(SesionCaja.id == sesion_id)
        .options(selectinload(SesionCaja.arqueo), selectinload(SesionCaja.resumen_cierre))
    )
    if sesion is None or not _puede_ver(ctx, sesion):
        raise NoEncontrado("El turno de caja no existe")
    t = await totales(session, sesion)
    ve = _ve_esperado(ctx, sesion)
    movimientos = list(
        await session.scalars(
            select(MovimientoCaja).where(MovimientoCaja.sesion_caja_id == sesion.id).order_by(MovimientoCaja.id)
        )
    )
    nombres = await nombres_usuarios(session, [m.usuario_id for m in movimientos])
    declarados = {r.metodo: r for r in sesion.resumen_cierre}
    metodos = []
    for metodo in MetodoPago:
        ops, monto = t["por_metodo"].get(metodo, (0, CERO))
        r = declarados.get(metodo)
        if not ops and r is None:
            continue
        metodos.append(
            {
                "metodo": metodo,
                "operaciones": ops,
                "monto_sistema": monto if ve else None,
                "monto_declarado": r.monto_declarado if r else None,
                "diferencia": r.diferencia if r else None,
            }
        )
    return {
        **_salida(ctx, sesion, t),
        "metodos": metodos,
        "movimientos": [
            {
                "id": m.id,
                "tipo": m.tipo,
                "monto": m.monto,
                "concepto": m.concepto,
                "usuario": nombres.get(m.usuario_id, "—"),
                "creado_en": m.creado_en,
            }
            for m in movimientos
        ],
        "arqueo": [
            {"denominacion": a.denominacion, "tipo": a.tipo.value, "cantidad": a.cantidad, "subtotal": a.subtotal}
            for a in sorted(sesion.arqueo, key=lambda a: -a.denominacion)
        ],
        "denominaciones": await denominaciones(session),
    }


async def listar(
    session: AsyncSession,
    ctx: ContextoUsuario,
    params: ParametrosPaginacion,
    *,
    usuario_id: int | None,
    estado: EstadoSesionCaja | None,
    desde: date | None,
    hasta: date | None,
) -> tuple[list[dict[str, Any]], int]:
    """Historial de turnos: el propio, o el de todos los cajeros de la sucursal con `caja.ver_todas`."""
    consulta = (
        select(SesionCaja)
        .join(Caja, Caja.id == SesionCaja.caja_id)
        .where(Caja.sucursal_id == ctx.sucursal_id)
        .order_by(SesionCaja.fecha_apertura.desc(), SesionCaja.id.desc())
    )
    if not ctx.tiene(VER_TODAS):
        consulta = consulta.where(SesionCaja.usuario_id == ctx.usuario_id)
    elif usuario_id:
        consulta = consulta.where(SesionCaja.usuario_id == usuario_id)
    if estado:
        consulta = consulta.where(SesionCaja.estado == estado)
    if desde:
        consulta = consulta.where(SesionCaja.fecha_apertura >= a_utc(datetime.combine(desde, time.min)))
    if hasta:
        consulta = consulta.where(
            SesionCaja.fecha_apertura < a_utc(datetime.combine(hasta + timedelta(days=1), time.min))
        )
    sesiones, total = await paginar(session, consulta, params)
    return [_salida(ctx, s, await totales(session, s)) for s in sesiones], total


async def denominaciones(session: AsyncSession) -> list[Decimal]:
    valores = await parametros.obtener(session, "caja.denominaciones")
    return sorted({Decimal(str(v)) for v in valores}, reverse=True)


# --- Operaciones ------------------------------------------------------------------------------------------


def _auditar(session, ctx: ContextoUsuario, sesion: SesionCaja, accion: str, descripcion: str, **datos) -> None:
    auditoria.registrar(
        session,
        accion=accion,
        modulo=MODULO,
        usuario_id=ctx.usuario_id,
        sucursal_id=ctx.sucursal_id,
        entidad="sesion_caja",
        entidad_id=sesion.id,
        descripcion=descripcion,
        datos=datos or None,
        ip=ctx.ip,
    )


async def abrir(session: AsyncSession, ctx: ContextoUsuario, datos: AperturaEntrada, clave: str | None) -> int:
    async def accion() -> int:
        # La fila de la caja se bloquea: dos personas no pueden abrir la misma caja a la vez
        caja = await session.scalar(
            select(Caja).where(Caja.id == datos.caja_id).with_for_update(of=Caja).execution_options(
                populate_existing=True
            )
        )
        if caja is None or not caja.activo or caja.sucursal_id != ctx.sucursal_id:
            raise ValidacionNegocio("La caja no existe en esta sucursal", codigo="caja_invalida")
        propia = await sesion_abierta(session, ctx.usuario_id)
        if propia is not None:
            if propia.caja_id == caja.id:
                return propia.id  # ya la tenía abierta (doble clic)
            raise Conflicto(f"Ya tiene abierta la {propia.caja.nombre}: ciérrela primero", codigo="ya_tiene_caja")
        ocupada = await session.scalar(select(SesionCaja).where(SesionCaja.caja_abierta_id == caja.id))
        if ocupada is not None:
            raise Conflicto(
                f"La {caja.nombre} está abierta por {ocupada.usuario.nombre_completo}", codigo="caja_ocupada"
            )
        sesion = SesionCaja(
            caja_id=caja.id,
            usuario_id=ctx.usuario_id,
            monto_inicial=datos.monto_inicial,
            observaciones_apertura=datos.observaciones,
            fecha_apertura=ahora_utc(),
        )
        session.add(sesion)
        await session.flush()
        _auditar(
            session, ctx, sesion, "ABRIR", f"Abrió la {caja.nombre} con S/ {datos.monto_inicial:.2f}",
            monto_inicial=str(datos.monto_inicial),
        )
        return sesion.id

    return await transacciones.ejecutar(
        session, accion, usuario_id=ctx.usuario_id, operacion="abrir_caja", clave=clave
    )


async def registrar_movimiento(
    session: AsyncSession, ctx: ContextoUsuario, datos: MovimientoCajaEntrada, clave: str | None
) -> int:
    async def accion() -> int:
        sesion = await exigir_turno(session, ctx, bloqueo="exclusivo")
        if datos.tipo == TipoMovimientoCaja.EGRESO:
            t = await totales(session, sesion, bloquear=True)
            if t["efectivo_esperado"] < datos.monto:
                raise ValidacionNegocio(
                    "No hay tanto efectivo en la caja para ese egreso", codigo="efectivo_insuficiente"
                )
        movimiento = MovimientoCaja(
            sesion_caja_id=sesion.id,
            tipo=datos.tipo,
            monto=datos.monto,
            concepto=datos.concepto,
            usuario_id=ctx.usuario_id,
        )
        session.add(movimiento)
        await session.flush()
        texto = "Ingreso" if datos.tipo == TipoMovimientoCaja.INGRESO else "Egreso"
        _auditar(session, ctx, sesion, datos.tipo.value, f"{texto} de S/ {datos.monto:.2f}: {datos.concepto}")
        return movimiento.id

    return await transacciones.ejecutar(
        session, accion, usuario_id=ctx.usuario_id, operacion="movimiento_caja", clave=clave
    )


async def cerrar(
    session: AsyncSession, ctx: ContextoUsuario, sesion_id: int, datos: CierreEntrada, clave: str | None
) -> int:
    async def accion() -> int:
        sesion = await _cargar(session, sesion_id, bloquear=True)
        if sesion.estado == EstadoSesionCaja.CERRADA:
            raise Conflicto("Este turno de caja ya está cerrado", codigo="caja_ya_cerrada")
        if sesion.usuario_id != ctx.usuario_id:
            # Cerrar el turno de otro (ej. el cajero se fue) solo con permiso de ver todas las cajas
            if not ctx.tiene(VER_TODAS) or sesion.caja.sucursal_id != ctx.sucursal_id:
                raise PermisoDenegado("Solo puede cerrar su propia caja", codigo="caja_ajena")

        validas = set(await denominaciones(session))
        arqueo: list[ArqueoDenominacion] = []
        contado = CERO
        for c in datos.arqueo:
            if c.denominacion not in validas:
                raise ValidacionNegocio(f"S/ {c.denominacion} no es un billete o moneda válido", codigo="denominacion")
            if c.cantidad == 0:
                continue
            subtotal = c.denominacion * c.cantidad
            contado += subtotal
            arqueo.append(
                ArqueoDenominacion(
                    sesion_caja_id=sesion.id,
                    tipo=TipoDenominacion.BILLETE if c.denominacion >= BILLETE_DESDE else TipoDenominacion.MONEDA,
                    denominacion=c.denominacion,
                    cantidad=c.cantidad,
                    subtotal=subtotal,
                )
            )

        t = await totales(session, sesion, bloquear=True)
        declarados = {d.metodo: d.monto for d in datos.declarados}
        resumen = []
        for metodo in MetodoPago:
            ops, monto = t["por_metodo"].get(metodo, (0, CERO))
            if metodo == MetodoPago.EFECTIVO:
                declarado: Decimal | None = contado
            else:
                declarado = declarados.get(metodo)
            if not ops and declarado is None:
                continue
            if metodo == MetodoPago.CREDITO:
                declarado = None  # el fiado no es dinero que entre a la caja
            resumen.append(
                ResumenCierreCaja(
                    sesion_caja_id=sesion.id,
                    metodo=metodo,
                    cantidad_operaciones=ops,
                    monto_sistema=monto,
                    monto_declarado=declarado,
                    diferencia=(declarado - monto) if declarado is not None and metodo != MetodoPago.EFECTIVO
                    else None,
                )
            )

        # Se agregan directo (asignar la colección haría una carga perezosa, que en async no se permite)
        session.add_all([*arqueo, *resumen])
        sesion.monto_esperado = t["efectivo_esperado"]
        sesion.monto_contado = contado
        sesion.diferencia = contado - t["efectivo_esperado"]
        sesion.estado = EstadoSesionCaja.CERRADA
        sesion.fecha_cierre = ahora_utc()
        sesion.observaciones_cierre = datos.observaciones
        # El efectivo del resumen guarda la diferencia del arqueo
        for r in resumen:
            if r.metodo == MetodoPago.EFECTIVO:
                r.diferencia = sesion.diferencia
        propia = sesion.usuario_id == ctx.usuario_id
        _auditar(
            session,
            ctx,
            sesion,
            "CERRAR",
            f"Cerró la {sesion.caja.nombre}"
            + ("" if propia else f" de {sesion.usuario.nombre_completo}")
            + f": contado S/ {contado:.2f}, diferencia S/ {sesion.diferencia:.2f}",
            esperado=str(sesion.monto_esperado),
            contado=str(contado),
            diferencia=str(sesion.diferencia),
            ventas=t["ventas"],
        )
        return sesion.id

    return await transacciones.ejecutar(
        session, accion, usuario_id=ctx.usuario_id, operacion="cerrar_caja", clave=clave
    )


async def cajeros(session: AsyncSession, ctx: ContextoUsuario) -> list[dict[str, Any]]:
    """Usuarios que tuvieron turnos en la sucursal (para el filtro del historial)."""
    filas = await session.execute(
        select(Usuario.id, Usuario.nombre_completo, func.count(SesionCaja.id))
        .join(SesionCaja, SesionCaja.usuario_id == Usuario.id)
        .join(Caja, Caja.id == SesionCaja.caja_id)
        .where(Caja.sucursal_id == ctx.sucursal_id)
        .group_by(Usuario.id, Usuario.nombre_completo)
        .order_by(Usuario.nombre_completo)
    )
    return [{"id": i, "nombre": n, "turnos": c} for i, n, c in filas.tuples()]

