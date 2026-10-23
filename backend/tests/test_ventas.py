"""POS y caja: cálculo de totales, venta con stock/lotes/kardex, idempotencia, precios que cambian, pagos mixtos,
autorización del supervisor, anulación, fiado, cierre ciego con arqueo y concurrencia."""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.core.database import SessionLocal
from app.models.enums import TipoAfectacionIGV
from app.services.ventas import LineaCalculo, a_cobrar, calcular
from app.utils.zona_horaria import hoy_local
from tests.conftest import ADMIN, Sesion, iniciar_sesion
from tests.test_inventario import _cargar, _integridad_ok, _stock
from tests.test_productos import crear_producto

D = Decimal


def _clave() -> str:
    return uuid.uuid4().hex


# --- Cálculo puro -----------------------------------------------------------------------------------------


def test_calculo_igv_incluido_exonerado_y_bolsa():
    lineas = [
        LineaCalculo(cantidad=D("2"), precio=D("5.90"), descuento=D("0"), afectacion=TipoAfectacionIGV.GRAVADO),
        LineaCalculo(cantidad=D("1.5"), precio=D("3.00"), descuento=D("0"), afectacion=TipoAfectacionIGV.EXONERADO),
        LineaCalculo(
            cantidad=D("1"), precio=D("0.10"), descuento=D("0"), afectacion=TipoAfectacionIGV.GRAVADO, bolsas=D("1")
        ),
    ]
    c = calcular(lineas, D("0"), D("18"), D("0.50"))
    assert c.total == D("16.90")  # 11.80 + 4.50 + 0.10 + 0.50 de ICBPER
    assert c.op_gravadas == D("10.08")  # 11.80/1.18 = 10.00 ; 0.10/1.18 = 0.08
    assert c.igv == D("1.82")
    assert c.op_exoneradas == D("4.50")
    assert c.icbper == D("0.50")
    assert c.op_gravadas + c.op_exoneradas + c.igv + c.icbper == c.total


def test_calculo_descuento_global_se_reparte_sin_perder_centimos():
    lineas = [
        LineaCalculo(cantidad=D("1"), precio=D("10.00"), descuento=D("0"), afectacion=TipoAfectacionIGV.GRAVADO),
        LineaCalculo(cantidad=D("1"), precio=D("10.00"), descuento=D("0"), afectacion=TipoAfectacionIGV.GRAVADO),
        LineaCalculo(cantidad=D("1"), precio=D("10.00"), descuento=D("1.00"), afectacion=TipoAfectacionIGV.EXONERADO),
    ]
    c = calcular(lineas, D("1.00"), D("18"), D("0.50"))
    assert c.total == D("28.00")  # 30 - 1 (línea) - 1 (global)
    assert c.descuento == D("2.00")
    assert sum(linea.descuento_total for linea in lineas) == D("2.00")


def test_redondeo_a_favor_del_cliente():
    assert a_cobrar(D("16.87"), D("0.10"), True) == D("16.80")
    assert a_cobrar(D("16.87"), D("0.10"), False) == D("16.87")  # con tarjeta no se redondea
    assert a_cobrar(D("16.87"), D("0"), True) == D("16.87")


# --- Fixtures ---------------------------------------------------------------------------------------------


@dataclass
class Turno:
    cajero: Sesion
    caja_id: int
    sesion_id: int


async def _nueva_caja(admin: Sesion) -> int:
    sucursal_id = (await admin.get("/sucursales")).json()[0]["id"]
    async with SessionLocal() as s, s.begin():
        r = await s.execute(
            text("INSERT INTO cajas (sucursal_id, nombre) VALUES (:s, :n)"),
            {"s": sucursal_id, "n": f"Caja {uuid.uuid4().hex[:6]}"},
        )
        return r.lastrowid


async def _abrir_turno(cliente, crear_usuario, admin: Sesion, rol: str = "Cajero", monto: str = "100.00") -> Turno:
    usuario, clave = await crear_usuario(rol)
    cajero = Sesion(cliente, await iniciar_sesion(cliente, usuario["username"], clave))
    caja_id = await _nueva_caja(admin)
    r = await cajero.post("/caja/abrir", json={"caja_id": caja_id, "monto_inicial": monto})
    assert r.status_code == 201, r.text
    return Turno(cajero, caja_id, r.json()["id"])


@pytest.fixture
async def turno(cliente, crear_usuario, admin) -> Turno:
    return await _abrir_turno(cliente, crear_usuario, admin)


async def _producto_con_stock(admin: Sesion, cantidad: str = "10", **extra) -> dict:
    p = await crear_producto(admin, precio_venta="5.50", precio_costo="0", **extra)
    if D(cantidad) > 0:
        await _cargar(admin, p["id"], cantidad, "3.00")
    return p


def _venta(items: list[tuple[dict, str]], pagos: list[dict], total: str, **extra) -> dict:
    return {
        "items": [
            {"producto_id": p["id"], "cantidad": c, "precio_unitario": p.get("precio_pos", p["precio_venta"])}
            for p, c in items
        ],
        "pagos": pagos,
        "total": total,
        **extra,
    }


async def _vender(sesion: Sesion, venta: dict, clave: str | None = None):
    return await sesion.post("/ventas", json=venta, headers={"Idempotency-Key": clave or _clave()})


async def _autorizar(sesion: Sesion, permiso: str, usuario=ADMIN) -> str:
    datos = {"username": usuario[0], "password": usuario[1], "permiso": permiso}
    r = await sesion.post("/ventas/autorizar", json=datos)
    assert r.status_code == 200, r.text
    return r.json()["token"]


# --- Caja -------------------------------------------------------------------------------------------------


async def test_no_se_vende_sin_caja_abierta(cliente, crear_usuario, admin):
    usuario, clave = await crear_usuario("Cajero")
    cajero = Sesion(cliente, await iniciar_sesion(cliente, usuario["username"], clave))
    p = await _producto_con_stock(admin)
    r = await _vender(cajero, _venta([(p, "1")], [{"metodo": "EFECTIVO", "monto": "5.50"}], "5.50"))
    assert r.status_code == 422 and r.json()["codigo"] == "caja_cerrada"
    assert (await cajero.get("/caja/actual")).json()["sesion"] is None


async def test_una_caja_por_cajero_y_caja_ocupada(cliente, crear_usuario, admin, turno: Turno):
    otra = await _nueva_caja(admin)
    r = await turno.cajero.post("/caja/abrir", json={"caja_id": otra, "monto_inicial": "0"})
    assert r.status_code == 409 and r.json()["codigo"] == "ya_tiene_caja"
    # La misma caja otra vez (doble clic): devuelve el mismo turno
    r = await turno.cajero.post("/caja/abrir", json={"caja_id": turno.caja_id, "monto_inicial": "100"})
    assert r.status_code == 201 and r.json()["id"] == turno.sesion_id

    usuario, clave = await crear_usuario("Cajero")
    otro = Sesion(cliente, await iniciar_sesion(cliente, usuario["username"], clave))
    r = await otro.post("/caja/abrir", json={"caja_id": turno.caja_id, "monto_inicial": "0"})
    assert r.status_code == 409 and r.json()["codigo"] == "caja_ocupada"


# --- Venta ------------------------------------------------------------------------------------------------


async def test_venta_efectivo_con_vuelto_stock_y_kardex(admin, turno: Turno):
    p = await _producto_con_stock(admin)
    r = await _vender(
        turno.cajero, _venta([(p, "3")], [{"metodo": "EFECTIVO", "monto": "16.50", "monto_recibido": "20"}], "16.50")
    )
    assert r.status_code == 201, r.text
    v = r.json()
    assert v["comprobante"].startswith("T001-") and v["estado"] == "COMPLETADA"
    assert v["total"] == "16.50" and v["vuelto"] == "3.50"
    assert D(v["op_gravadas"]) + D(v["igv"]) == D("16.50")
    assert v["empresa"]["ruc"] and v["detalles"][0]["descripcion"] == p["nombre"]
    assert await _stock(admin, p["id"]) == 7

    kardex = (await admin.get("/inventario/kardex", params={"producto_id": p["id"]})).json()["items"]
    salida = next(m for m in kardex if m["tipo"] == "SALIDA_VENTA")
    assert D(salida["cantidad"]) == -3 and D(salida["stock_nuevo"]) == 7
    await _integridad_ok(admin)


async def test_venta_idempotente(admin, turno: Turno):
    p = await _producto_con_stock(admin)
    venta = _venta([(p, "2")], [{"metodo": "EFECTIVO", "monto": "11.00"}], "11.00")
    clave = _clave()
    primera, segunda = await asyncio.gather(_vender(turno.cajero, venta, clave), _vender(turno.cajero, venta, clave))
    assert primera.status_code == segunda.status_code == 201
    assert primera.json()["id"] == segunda.json()["id"]
    assert await _stock(admin, p["id"]) == 8

    r = await turno.cajero.post("/ventas", json=venta)  # sin clave: rechazada
    assert r.status_code == 422 and r.json()["codigo"] == "sin_clave"


async def test_precio_cambiado_y_total_distinto(admin, turno: Turno):
    p = await _producto_con_stock(admin)
    r = await _vender(turno.cajero, _venta([({**p, "precio_venta": "5.00"}, "1")], [
        {"metodo": "EFECTIVO", "monto": "5.00"}], "5.00"))
    assert r.status_code == 409 and r.json()["codigo"] == "precio_cambiado"
    assert r.json()["datos"]["precio"] == "5.50"

    r = await _vender(turno.cajero, _venta([(p, "1")], [{"metodo": "EFECTIVO", "monto": "5.00"}], "5.00"))
    assert r.status_code == 409 and r.json()["codigo"] == "total_distinto"
    assert await _stock(admin, p["id"]) == 10  # no se vendió nada


async def test_pago_mixto_y_pagos_que_no_cuadran(admin, turno: Turno):
    p = await _producto_con_stock(admin)
    r = await _vender(turno.cajero, _venta([(p, "3")], [
        {"metodo": "EFECTIVO", "monto": "10.00"}, {"metodo": "YAPE", "monto": "5.00"}], "16.50"))
    assert r.status_code == 422 and r.json()["codigo"] == "pagos_no_cuadran"

    r = await _vender(turno.cajero, _venta([(p, "3")], [
        {"metodo": "EFECTIVO", "monto": "10.00", "monto_recibido": "20.00"},
        {"metodo": "YAPE", "monto": "6.50", "referencia": "OP 123"},
    ], "16.50"))
    assert r.status_code == 201, r.text
    assert r.json()["vuelto"] == "10.00"
    assert {pg["metodo"] for pg in r.json()["pagos"]} == {"EFECTIVO", "YAPE"}


async def test_presentacion_descuenta_unidades_base(admin, turno: Turno):
    p = await crear_producto(
        admin, precio_venta="3.00", precio_costo="0",
        presentaciones=[{"nombre": "Six pack", "factor": "6", "precio_venta": "16.00"}],
    )
    await _cargar(admin, p["id"], "24", "2.00")
    detalle = (await admin.get(f"/productos/{p['id']}")).json()
    six = detalle["presentaciones"][0]
    venta = {
        "items": [{"producto_id": p["id"], "presentacion_id": six["id"], "cantidad": "2", "precio_unitario": "16.00"}],
        "pagos": [{"metodo": "TARJETA", "monto": "32.00"}],
        "total": "32.00",
    }
    r = await _vender(turno.cajero, venta)
    assert r.status_code == 201, r.text
    assert r.json()["detalles"][0]["descripcion"].endswith("Six pack")
    assert await _stock(admin, p["id"]) == 12


# --- Autorización del supervisor --------------------------------------------------------------------------


async def test_vender_sin_stock_con_clave_del_supervisor(admin, turno: Turno):
    p = await _producto_con_stock(admin, "1")
    venta = _venta([(p, "3")], [{"metodo": "EFECTIVO", "monto": "16.50"}], "16.50")
    r = await _vender(turno.cajero, venta)
    assert r.status_code == 403 and r.json()["codigo"] == "stock_insuficiente"
    assert r.json()["datos"]["autorizable"] is True

    r = await turno.cajero.post(
        "/ventas/autorizar", json={"username": ADMIN[0], "password": "mala", "permiso": "pos.vender_sin_stock"}
    )
    assert r.status_code == 401

    token = await _autorizar(turno.cajero, "pos.vender_sin_stock")
    r = await _vender(turno.cajero, {**venta, "autorizaciones": [token]})
    assert r.status_code == 201, r.text
    assert await _stock(admin, p["id"]) == -2

    # La misma autorización no sirve dos veces
    r = await _vender(turno.cajero, {**venta, "autorizaciones": [token]})
    assert r.status_code == 422 and r.json()["codigo"] == "autorizacion_usada"

    auditoria = (await admin.get("/auditoria", params={"modulo": "ventas"})).json()["items"]
    assert any(a["accion"] == "AUTORIZAR" and "pos.vender_sin_stock" in a["descripcion"] for a in auditoria)
    await _integridad_ok(admin)


async def test_autorizacion_es_solo_para_quien_la_pidio(cliente, crear_usuario, admin, turno: Turno):
    token = await _autorizar(turno.cajero, "pos.vender_sin_stock")
    otro = await _abrir_turno(cliente, crear_usuario, admin)
    p = await _producto_con_stock(admin, "0")
    venta = _venta([(p, "1")], [{"metodo": "EFECTIVO", "monto": "5.50"}], "5.50", autorizaciones=[token])
    r = await _vender(otro.cajero, venta)
    assert r.status_code == 422 and r.json()["codigo"] == "autorizacion_invalida"

    # Un cajero no puede autorizar (no tiene el permiso)
    usuario, clave = await crear_usuario("Cajero")
    r = await turno.cajero.post(
        "/ventas/autorizar", json={"username": usuario["username"], "password": clave, "permiso": "pos.anular_venta"}
    )
    assert r.status_code == 403 and r.json()["codigo"] == "supervisor_sin_permiso"


async def test_descuento_mayor_al_permitido(admin, turno: Turno):
    p = await _producto_con_stock(admin, "20")
    # 10 x 5.50 = 55.00; 5.00 de descuento = 9.1 % (permitido hasta 10 %)
    r = await _vender(turno.cajero, _venta([(p, "10")], [{"metodo": "TARJETA", "monto": "50.00"}], "50.00",
                                           descuento="5.00"))
    assert r.status_code == 201, r.text
    assert r.json()["descuento"] == "5.00"

    venta = _venta([(p, "1")], [{"metodo": "TARJETA", "monto": "4.00"}], "4.00", descuento="1.50")  # 27 %
    r = await _vender(turno.cajero, venta)
    assert r.status_code == 403 and r.json()["codigo"] == "descuento_no_autorizado"
    token = await _autorizar(turno.cajero, "pos.aplicar_descuento")
    r = await _vender(turno.cajero, {**venta, "autorizaciones": [token]})
    assert r.status_code == 201, r.text


# --- Lotes ------------------------------------------------------------------------------------------------


async def test_venta_por_lotes_fefo_sin_vencidos(admin, turno: Turno):
    p = await crear_producto(admin, precio_venta="5.50", precio_costo="0", maneja_lotes=True)
    hoy = hoy_local()
    await _cargar(admin, p["id"], "4", "3.00", numero_lote="V-1", fecha_vencimiento=str(hoy + timedelta(days=30)))
    # El stock inicial es uno por producto: los otros dos lotes (uno ya vencido) se agregan directo en la BD
    async with SessionLocal() as s, s.begin():
        consulta = text("SELECT almacen_id FROM lotes WHERE producto_id = :p")
        almacen = (await s.execute(consulta, {"p": p["id"]})).scalar()
        for numero, cantidad, dias in (("V-2", 5, 10), ("V-3", 3, -1)):
            await s.execute(
                text("INSERT INTO lotes (producto_id, almacen_id, numero_lote, fecha_vencimiento, cantidad_inicial, "
                     "cantidad_actual, costo_unitario) VALUES (:p, :a, :n, :f, :c, :c, 3)"),
                {"p": p["id"], "a": almacen, "n": numero, "f": hoy + timedelta(days=dias), "c": cantidad},
            )
        await s.execute(
            text("INSERT INTO movimientos_inventario (producto_id, almacen_id, tipo, cantidad, stock_anterior, "
                 "stock_nuevo, costo_unitario) VALUES (:p, :a, 'AJUSTE_ENTRADA', 8, 4, 12, 3)"),
            {"p": p["id"], "a": almacen},
        )
        await s.execute(text("UPDATE stock_almacen SET cantidad = 12 WHERE producto_id = :p"), {"p": p["id"]})

    # Hay 12, pero 3 están vencidos (V-3): se venden 6 -> 5 de V-2 (vence antes) y 1 de V-1
    r = await _vender(turno.cajero, _venta([(p, "6")], [{"metodo": "EFECTIVO", "monto": "33.00"}], "33.00"))
    assert r.status_code == 201, r.text
    lotes = {
        lt["numero_lote"]: D(lt["cantidad_actual"])
        for lt in (await admin.get("/inventario/lotes", params={"producto_id": p["id"]})).json()
    }
    assert lotes.get("V-2", D(0)) == 0 and lotes["V-1"] == 3 and lotes["V-3"] == 3

    # Quedan 3 vigentes: vender 4 necesita autorización (el vencido no cuenta)
    r = await _vender(turno.cajero, _venta([(p, "4")], [{"metodo": "EFECTIVO", "monto": "22.00"}], "22.00"))
    assert r.status_code == 403 and r.json()["codigo"] == "stock_insuficiente"
    await _integridad_ok(admin)


# --- Anulación --------------------------------------------------------------------------------------------


async def test_anular_devuelve_stock_y_sale_del_arqueo(admin, turno: Turno):
    p = await _producto_con_stock(admin)
    v = (await _vender(turno.cajero, _venta([(p, "4")], [{"metodo": "EFECTIVO", "monto": "22.00"}], "22.00"))).json()
    assert await _stock(admin, p["id"]) == 6

    r = await turno.cajero.post(f"/ventas/{v['id']}/anular", json={"motivo": "Cliente se arrepintió"})
    assert r.status_code == 403 and r.json()["codigo"] == "anulacion_no_autorizada"

    token = await _autorizar(turno.cajero, "pos.anular_venta")
    anulacion = {"motivo": "Cliente se arrepintió", "autorizacion": token}
    r = await turno.cajero.post(f"/ventas/{v['id']}/anular", json=anulacion)
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "ANULADA" and "autorizó" in r.json()["motivo_anulacion"]
    assert await _stock(admin, p["id"]) == 10

    r = await admin.post(f"/ventas/{v['id']}/anular", json={"motivo": "Otra vez por error"})
    assert r.status_code == 409 and r.json()["codigo"] == "ya_anulada"

    actual = (await admin.get(f"/caja/sesiones/{turno.sesion_id}")).json()
    assert actual["ventas"] == 0 and actual["anuladas"] == 1
    assert actual["efectivo_esperado"] == "100.00"
    await _integridad_ok(admin)


async def test_anular_venta_sin_stock_de_producto_con_lotes(admin, turno: Turno):
    p = await crear_producto(admin, precio_venta="5.50", precio_costo="0", maneja_lotes=True)
    token = await _autorizar(turno.cajero, "pos.vender_sin_stock")
    v = (await _vender(turno.cajero, _venta([(p, "2")], [{"metodo": "EFECTIVO", "monto": "11.00"}], "11.00",
                                            autorizaciones=[token]))).json()
    assert await _stock(admin, p["id"]) == -2
    r = await admin.post(f"/ventas/{v['id']}/anular", json={"motivo": "Venta de prueba"})
    assert r.status_code == 200, r.text
    assert await _stock(admin, p["id"]) == 0
    await _integridad_ok(admin)


# --- Fiado ------------------------------------------------------------------------------------------------


async def test_fiado_con_limite(admin, turno: Turno):
    r = await admin.post("/clientes", json={
        "tipo_documento": "DNI", "numero_documento": str(uuid.uuid4().int)[:8], "nombre": "Vecina Rosa",
        "permite_credito": True, "limite_credito": "20.00",
    })
    assert r.status_code == 201, r.text
    cliente_id = r.json()["id"]
    p = await _producto_con_stock(admin)
    venta = _venta([(p, "3")], [{"metodo": "CREDITO", "monto": "16.50"}], "16.50", cliente_id=cliente_id)

    r = await _vender(turno.cajero, {**venta, "cliente_id": None})
    assert r.status_code == 422 and r.json()["codigo"] == "cliente_requerido"
    r = await _vender(turno.cajero, venta)
    assert r.status_code == 201, r.text
    assert r.json()["es_credito"] and r.json()["cliente"] == "Vecina Rosa"

    r = await _vender(turno.cajero, venta)
    assert r.status_code == 422 and r.json()["codigo"] == "limite_credito"
    buscados = (await turno.cajero.get("/clientes/buscar", params={"texto": "rosa vecina"})).json()
    assert any(c["id"] == cliente_id and c["deuda"] == "16.50" for c in buscados)


# --- Cierre ciego -----------------------------------------------------------------------------------------


async def test_cierre_ciego_con_arqueo(admin, turno: Turno):
    p = await _producto_con_stock(admin)
    await _vender(turno.cajero, _venta([(p, "3")], [{"metodo": "EFECTIVO", "monto": "16.50", "monto_recibido": "50"}],
                                       "16.50"))
    await _vender(turno.cajero, _venta([(p, "2")], [{"metodo": "YAPE", "monto": "11.00"}], "11.00"))
    r = await turno.cajero.post("/caja/movimientos", json={"tipo": "INGRESO", "monto": "20", "concepto": "Sencillo"})
    assert r.status_code == 201, r.text
    r = await turno.cajero.post("/caja/movimientos", json={"tipo": "EGRESO", "monto": "500", "concepto": "Proveedor"})
    assert r.status_code == 422 and r.json()["codigo"] == "efectivo_insuficiente"
    await turno.cajero.post("/caja/movimientos", json={"tipo": "EGRESO", "monto": "6.50", "concepto": "Hielo"})

    # El cajero no ve cuánto debería haber (cierre ciego); el administrador sí
    actual = (await turno.cajero.get("/caja/actual")).json()["sesion"]
    assert actual["efectivo_esperado"] is None and actual["total_vendido"] is None and actual["ventas"] == 2
    assert (await admin.get(f"/caja/sesiones/{turno.sesion_id}")).json()["efectivo_esperado"] == "130.00"

    # Esperado: 100 + 16.50 + 20 - 6.50 = 130.00. Cuenta 129.80 (falta 0.20)
    arqueo = [{"denominacion": "100", "cantidad": 1}, {"denominacion": "20", "cantidad": 1},
              {"denominacion": "5", "cantidad": 1}, {"denominacion": "2", "cantidad": 2},
              {"denominacion": "0.50", "cantidad": 1}, {"denominacion": "0.10", "cantidad": 3}]
    r = await turno.cajero.post(f"/caja/sesiones/{turno.sesion_id}/cerrar", json={
        "arqueo": arqueo, "declarados": [{"metodo": "YAPE", "monto": "11.00"}]})
    assert r.status_code == 200, r.text
    cierre = r.json()
    assert cierre["estado"] == "CERRADA"
    assert cierre["efectivo_esperado"] == "130.00" and cierre["monto_contado"] == "129.80"
    assert cierre["diferencia"] == "-0.20"
    yape = next(m for m in cierre["metodos"] if m["metodo"] == "YAPE")
    assert yape["monto_sistema"] == "11.00" and yape["diferencia"] == "0.00"

    r = await turno.cajero.post(f"/caja/sesiones/{turno.sesion_id}/cerrar", json={"arqueo": []})
    assert r.status_code == 409
    r = await _vender(turno.cajero, _venta([(p, "1")], [{"metodo": "EFECTIVO", "monto": "5.50"}], "5.50"))
    assert r.status_code == 422 and r.json()["codigo"] == "caja_cerrada"

    historial = (await turno.cajero.get("/caja/sesiones")).json()
    assert historial["total"] == 1 and historial["items"][0]["diferencia"] == "-0.20"


async def test_turno_cerrado_no_se_anula(admin, turno: Turno):
    p = await _producto_con_stock(admin)
    v = (await _vender(turno.cajero, _venta([(p, "1")], [{"metodo": "EFECTIVO", "monto": "5.50"}], "5.50"))).json()
    await turno.cajero.post(f"/caja/sesiones/{turno.sesion_id}/cerrar", json={"arqueo": []})
    r = await admin.post(f"/ventas/{v['id']}/anular", json={"motivo": "Tarde"})
    assert r.status_code == 422 and r.json()["codigo"] == "turno_cerrado"


# --- Concurrencia -----------------------------------------------------------------------------------------


async def test_dos_cajas_y_la_ultima_unidad(cliente, crear_usuario, admin):
    a = await _abrir_turno(cliente, crear_usuario, admin)
    b = await _abrir_turno(cliente, crear_usuario, admin)
    p = await _producto_con_stock(admin, "1")
    venta = _venta([(p, "1")], [{"metodo": "EFECTIVO", "monto": "5.50"}], "5.50")
    r1, r2 = await asyncio.gather(_vender(a.cajero, venta), _vender(b.cajero, venta))
    assert sorted([r1.status_code, r2.status_code]) == [201, 403]
    assert await _stock(admin, p["id"]) == 0
    await _integridad_ok(admin)


async def test_numeracion_correlativa_sin_huecos_en_paralelo(cliente, crear_usuario, admin):
    turnos = [await _abrir_turno(cliente, crear_usuario, admin) for _ in range(3)]
    p = await _producto_con_stock(admin, "30")
    venta = _venta([(p, "1")], [{"metodo": "EFECTIVO", "monto": "5.50"}], "5.50")
    respuestas = await asyncio.gather(*[_vender(t.cajero, venta) for t in turnos for _ in range(3)])
    assert all(r.status_code == 201 for r in respuestas), [r.text for r in respuestas if r.status_code != 201]
    numeros = sorted(int(r.json()["comprobante"].split("-")[1]) for r in respuestas)
    assert numeros == list(range(numeros[0], numeros[0] + 9))
    assert await _stock(admin, p["id"]) == 21
