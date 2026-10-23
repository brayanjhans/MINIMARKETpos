"""Inventario: stock inicial, ajustes con aprobación, transferencias con lotes, inventario físico, kardex
inmutable, concurrencia, idempotencia e integridad (stock = kardex = lotes)."""

import asyncio
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.core.database import SessionLocal
from app.models import StockAlmacen
from app.models.enums import TipoMovimientoInventario
from app.services import stock as servicio_stock
from tests.conftest import Sesion, iniciar_sesion
from tests.test_productos import crear_producto


def _clave() -> str:
    return uuid.uuid4().hex


async def _almacenes(admin: Sesion) -> tuple[int, int]:
    """(almacén de venta, segundo almacén de la misma sucursal; se crea si no existe)."""
    lista = (await admin.get("/inventario/almacenes")).json()
    venta = next(a for a in lista if a["es_sucursal_actual"] and a["es_almacen_venta"])
    otro = next((a for a in lista if a["es_sucursal_actual"] and not a["es_almacen_venta"]), None)
    if otro is None:
        async with SessionLocal() as s, s.begin():
            await s.execute(
                text("INSERT INTO almacenes (sucursal_id, nombre, es_almacen_venta) VALUES (:s, 'Depósito', false)"),
                {"s": venta["sucursal_id"]},
            )
        lista = (await admin.get("/inventario/almacenes")).json()
        otro = next(a for a in lista if a["es_sucursal_actual"] and not a["es_almacen_venta"])
    return venta["id"], otro["id"]


async def _cargar(admin: Sesion, producto_id: int, cantidad: str, costo: str = "2.00", **extra) -> dict:
    r = await admin.post(
        "/inventario/stock-inicial",
        json={"items": [{"producto_id": producto_id, "cantidad": cantidad, "costo_unitario": costo, **extra}]},
    )
    assert r.status_code == 200, r.text
    return r.json()


async def _stock(admin: Sesion, producto_id: int, almacen_id: int | None = None) -> Decimal:
    detalle = (await admin.get(f"/productos/{producto_id}")).json()
    if almacen_id is None:
        return Decimal(detalle["stock"])
    fila = next((s for s in detalle["stock_por_almacen"] if s["almacen_id"] == almacen_id), None)
    return Decimal(fila["cantidad"]) if fila else Decimal(0)


async def _integridad_ok(admin: Sesion) -> None:
    r = await admin.get("/inventario/integridad")
    assert r.status_code == 200
    assert r.json()["correcto"], r.json()["problemas"]


@pytest.fixture
async def almacenero(cliente, crear_usuario) -> Sesion:
    usuario, clave = await crear_usuario("Almacenero")
    return Sesion(cliente, await iniciar_sesion(cliente, usuario["username"], clave))


async def _otro_admin(crear_usuario) -> None:
    """Garantiza que exista otro aprobador: así nadie puede aprobar lo suyo."""
    await crear_usuario("Administrador")


# --- Stock inicial -----------------------------------------------------------------------------------------


async def test_stock_inicial_kardex_y_costo(admin: Sesion):
    p = await crear_producto(admin, precio_costo="0")
    resultado = await _cargar(admin, p["id"], "24", "4.50")
    assert resultado["productos"] == 1 and Decimal(resultado["unidades"]) == 24
    assert resultado["valor"] == "108.00"
    assert await _stock(admin, p["id"]) == 24

    detalle = (await admin.get(f"/productos/{p['id']}")).json()
    assert detalle["precio_costo"] == "4.5000"
    assert detalle["tiene_movimientos"] is True

    kardex = (await admin.get("/inventario/kardex", params={"producto_id": p["id"]})).json()
    assert kardex["total"] == 1
    assert kardex["items"][0]["tipo"] == "STOCK_INICIAL"
    assert kardex["items"][0]["stock_nuevo"] == "24.000"

    # Una sola vez por producto y almacén
    r = await admin.post(
        "/inventario/stock-inicial", json={"items": [{"producto_id": p["id"], "cantidad": "1", "costo_unitario": "1"}]}
    )
    assert r.status_code == 422
    assert r.json()["codigo"] == "ya_tiene_movimientos"

    # Con movimientos ya no se puede cambiar la unidad ni el costo a mano
    r = await admin.patch(f"/productos/{p['id']}", json={"version": detalle["version"], "precio_costo": "1"})
    assert r.status_code == 422
    assert r.json()["codigo"] == "producto_con_movimientos"
    await _integridad_ok(admin)


async def test_stock_inicial_idempotente(admin: Sesion):
    p = await crear_producto(admin)
    clave = _clave()
    cuerpo = {"items": [{"producto_id": p["id"], "cantidad": "10", "costo_unitario": "2"}]}
    # Doble clic: las dos peticiones llegan a la vez con la misma clave
    r1, r2 = await asyncio.gather(
        admin.post("/inventario/stock-inicial", json=cuerpo, headers={**admin.headers, "Idempotency-Key": clave}),
        admin.post("/inventario/stock-inicial", json=cuerpo, headers={**admin.headers, "Idempotency-Key": clave}),
    )
    assert r1.status_code == 200 and r2.status_code == 200, (r1.text, r2.text)
    assert await _stock(admin, p["id"]) == 10


async def test_stock_inicial_con_lotes_exige_lote(admin: Sesion):
    p = await crear_producto(admin, maneja_lotes=True)
    r = await admin.post(
        "/inventario/stock-inicial", json={"items": [{"producto_id": p["id"], "cantidad": "5", "costo_unitario": "1"}]}
    )
    assert r.status_code == 422 and r.json()["codigo"] == "lote_requerido"


async def test_cantidad_entera(admin: Sesion):
    p = await crear_producto(admin)
    r = await admin.post(
        "/inventario/stock-inicial",
        json={"items": [{"producto_id": p["id"], "cantidad": "1.5", "costo_unitario": "1"}]},
    )
    assert r.status_code == 422 and r.json()["codigo"] == "cantidad_no_entera"


# --- Ajustes -----------------------------------------------------------------------------------------------


async def _motivo(admin: Sesion, nombre: str) -> int:
    return next(m["id"] for m in (await admin.get("/inventario/motivos-ajuste")).json() if m["nombre"] == nombre)


async def test_ajuste_requiere_aprobacion_de_otra_persona(admin: Sesion, almacenero: Sesion, crear_usuario):
    await _otro_admin(crear_usuario)
    p = await crear_producto(admin)
    await _cargar(admin, p["id"], "20")
    vencido = await _motivo(admin, "Producto vencido")

    r = await almacenero.post(
        "/inventario/ajustes", json={"motivo_id": vencido, "detalles": [{"producto_id": p["id"], "cantidad": "-3"}]}
    )
    assert r.status_code == 201, r.text
    ajuste = r.json()
    assert ajuste["estado"] == "PENDIENTE_APROBACION"
    assert ajuste["valor"] == "-6.00"
    assert await _stock(admin, p["id"]) == 20  # no cambia hasta aprobar

    # El almacenero no tiene permiso de aprobar
    assert (await almacenero.post(f"/inventario/ajustes/{ajuste['id']}/aprobar")).status_code == 403

    r = await admin.post(f"/inventario/ajustes/{ajuste['id']}/aprobar")
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "APLICADO"
    assert await _stock(admin, p["id"]) == 17
    # Aprobar dos veces no descuenta dos veces
    r = await admin.post(f"/inventario/ajustes/{ajuste['id']}/aprobar")
    assert r.status_code == 409 and r.json()["codigo"] == "ya_aplicado"
    assert await _stock(admin, p["id"]) == 17

    resumen = (await admin.get("/inventario/resumen")).json()
    assert Decimal(resumen["mermas_mes"]) >= Decimal("6.00")

    # Quien crea no puede aprobar lo suyo
    r = await admin.post(
        "/inventario/ajustes", json={"motivo_id": vencido, "detalles": [{"producto_id": p["id"], "cantidad": "-1"}]}
    )
    assert r.json()["puede_aprobar"] is False
    r = await admin.post(f"/inventario/ajustes/{r.json()['id']}/aprobar")
    assert r.status_code == 422 and r.json()["codigo"] == "autoaprobacion"
    await _integridad_ok(admin)


async def test_ajuste_revalida_stock_al_aprobar(admin: Sesion, almacenero: Sesion):
    p = await crear_producto(admin)
    await _cargar(admin, p["id"], "5")
    roto = await _motivo(admin, "Producto dañado o roto")
    a1 = (
        await almacenero.post(
            "/inventario/ajustes", json={"motivo_id": roto, "detalles": [{"producto_id": p["id"], "cantidad": "-4"}]}
        )
    ).json()
    a2 = (
        await almacenero.post(
            "/inventario/ajustes", json={"motivo_id": roto, "detalles": [{"producto_id": p["id"], "cantidad": "-4"}]}
        )
    ).json()
    assert (await admin.post(f"/inventario/ajustes/{a1['id']}/aprobar")).status_code == 200
    r = await admin.post(f"/inventario/ajustes/{a2['id']}/aprobar")
    assert r.status_code == 422 and r.json()["codigo"] == "stock_insuficiente"
    assert await _stock(admin, p["id"]) == 1  # nunca queda negativo por un ajuste


async def test_ajuste_signo_segun_motivo_y_borrador(admin: Sesion, almacenero: Sesion):
    p = await crear_producto(admin)
    sobrante = await _motivo(admin, "Sobrante encontrado")
    r = await almacenero.post(
        "/inventario/ajustes", json={"motivo_id": sobrante, "detalles": [{"producto_id": p["id"], "cantidad": "-1"}]}
    )
    assert r.status_code == 422 and r.json()["codigo"] == "signo_invalido"

    r = await almacenero.post(
        "/inventario/ajustes",
        json={"motivo_id": sobrante, "enviar": False, "detalles": [{"producto_id": p["id"], "cantidad": "2"}]},
    )
    borrador = r.json()
    assert borrador["estado"] == "BORRADOR"
    r = await almacenero.put(
        f"/inventario/ajustes/{borrador['id']}",
        json={"motivo_id": sobrante, "detalles": [{"producto_id": p["id"], "cantidad": "3"}]},
    )
    assert r.json()["total_unidades"] == "3.000"
    assert (await almacenero.post(f"/inventario/ajustes/{borrador['id']}/enviar")).json()["estado"] == (
        "PENDIENTE_APROBACION"
    )
    r = await admin.post(f"/inventario/ajustes/{borrador['id']}/rechazar", json={"motivo": "No corresponde"})
    assert r.json()["estado"] == "RECHAZADO"
    assert await _stock(admin, p["id"]) == 0


# --- Lotes y transferencias --------------------------------------------------------------------------------


async def test_transferencia_con_lotes_fefo_y_faltante(admin: Sesion):
    venta, deposito = await _almacenes(admin)
    p = await crear_producto(admin, maneja_lotes=True, precio_costo="0")
    hoy = date.today()
    r = await admin.post(
        "/inventario/stock-inicial",
        json={
            "items": [
                {
                    "producto_id": p["id"],
                    "cantidad": "10",
                    "costo_unitario": "5",
                    "numero_lote": "L-tarde",
                    "fecha_vencimiento": str(hoy + timedelta(days=60)),
                },
                {
                    "producto_id": p["id"],
                    "cantidad": "4",
                    "costo_unitario": "5",
                    "numero_lote": "L-pronto",
                    "fecha_vencimiento": str(hoy + timedelta(days=5)),
                },
            ]
        },
    )
    assert r.status_code == 200, r.text

    # Sin indicar lote: sale primero el que vence antes (4 de L-PRONTO + 2 de L-TARDE)
    r = await admin.post(
        "/inventario/transferencias",
        json={"almacen_destino_id": deposito, "detalles": [{"producto_id": p["id"], "cantidad": "6"}]},
    )
    assert r.status_code == 201, r.text
    t = r.json()
    assert t["estado"] == "EN_TRANSITO"
    lineas = sorted((d["lote"], d["cantidad"]) for d in t["detalles"])
    assert lineas == [("L-PRONTO", "4.000"), ("L-TARDE", "2.000")]
    assert await _stock(admin, p["id"], venta) == 8
    resumen = (await admin.get("/inventario/resumen")).json()
    assert resumen["transito_documentos"] >= 1

    # Llegan 3 de L-PRONTO (uno se rompió) y los 2 de L-TARDE
    pronto = next(d for d in t["detalles"] if d["lote"] == "L-PRONTO")
    r = await admin.post(
        f"/inventario/transferencias/{t['id']}/recibir",
        json={"detalles": [{"detalle_id": pronto["id"], "cantidad_recibida": "3", "motivo_faltante": "Roto"}]},
    )
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "RECIBIDA"
    assert await _stock(admin, p["id"], deposito) == 5
    lotes = (await admin.get("/inventario/lotes", params={"almacen_id": deposito, "producto_id": p["id"]})).json()
    assert sorted((lote["numero_lote"], lote["cantidad_actual"]) for lote in lotes) == [
        ("L-PRONTO", "3.000"),
        ("L-TARDE", "2.000"),
    ]
    # Recibir otra vez no suma dos veces
    r = await admin.post(f"/inventario/transferencias/{t['id']}/recibir", json={})
    assert r.status_code == 409
    assert await _stock(admin, p["id"], deposito) == 5
    await _integridad_ok(admin)


async def test_anular_transferencia_devuelve_al_origen(admin: Sesion):
    venta, deposito = await _almacenes(admin)
    p = await crear_producto(admin)
    await _cargar(admin, p["id"], "10")
    t = (
        await admin.post(
            "/inventario/transferencias",
            json={"almacen_destino_id": deposito, "detalles": [{"producto_id": p["id"], "cantidad": "7"}]},
        )
    ).json()
    assert await _stock(admin, p["id"], venta) == 3
    r = await admin.post(f"/inventario/transferencias/{t['id']}/anular")
    assert r.json()["estado"] == "ANULADA"
    assert await _stock(admin, p["id"], venta) == 10
    tipos = [
        m["tipo"] for m in (await admin.get("/inventario/kardex", params={"producto_id": p["id"]})).json()["items"]
    ]
    assert tipos[0] == "TRANSFERENCIA_ANULADA"
    await _integridad_ok(admin)


async def test_transferencias_concurrentes_no_dejan_stock_negativo(admin: Sesion):
    _, deposito = await _almacenes(admin)
    p = await crear_producto(admin)
    await _cargar(admin, p["id"], "10")

    async def transferir():
        return await admin.post(
            "/inventario/transferencias",
            json={"almacen_destino_id": deposito, "detalles": [{"producto_id": p["id"], "cantidad": "3"}]},
        )

    respuestas = await asyncio.gather(*(transferir() for _ in range(6)))
    exitos = [r for r in respuestas if r.status_code == 201]
    assert len(exitos) == 3, [r.text for r in respuestas if r.status_code != 201]
    assert all(r.json()["codigo"] == "stock_insuficiente" for r in respuestas if r.status_code != 201)
    assert await _stock(admin, p["id"]) == 1
    await _integridad_ok(admin)


# --- Venta sin stock de productos con lotes (pendiente de lote) --------------------------------------------


async def test_pendiente_de_lote_se_descuenta_al_ingresar(admin: Sesion, almacenero: Sesion):
    venta, _ = await _almacenes(admin)
    p = await crear_producto(admin, maneja_lotes=True)
    # Una venta autorizada sin stock (Fase 4 la hará el POS): el stock queda en -2 y 2 pendientes de lote
    async with SessionLocal() as s, s.begin():
        bloqueo = await servicio_stock.bloquear(s, [p["id"]], [venta])
        servicio_stock.mover(
            s,
            producto=bloqueo.productos[p["id"]],
            stock=bloqueo.stock(p["id"], venta),
            cantidad=Decimal("-2"),
            tipo=TipoMovimientoInventario.SALIDA_VENTA,
            costo_unitario=Decimal("0"),
            usuario_id=None,
            permitir_negativo=True,
        )
    stock = (
        await admin.get("/inventario/stock", params={"estado": "por_regularizar", "busqueda": p["nombre"]})
    ).json()["items"][0]
    assert stock["cantidad"] == "-2.000" and stock["pendiente_lote"] == "2.000"

    # Llegan 5 en un lote nuevo: 2 cubren lo vendido y en el lote quedan 3
    sobrante = await _motivo(admin, "Bonificación del proveedor")
    aj = (
        await almacenero.post(
            "/inventario/ajustes",
            json={"motivo_id": sobrante, "detalles": [{"producto_id": p["id"], "cantidad": "5", "numero_lote": "B-1"}]},
        )
    ).json()
    assert (await admin.post(f"/inventario/ajustes/{aj['id']}/aprobar")).status_code == 200
    assert await _stock(admin, p["id"]) == 3
    lotes = (await admin.get("/inventario/lotes", params={"producto_id": p["id"]})).json()
    assert [(lote["numero_lote"], lote["cantidad_actual"]) for lote in lotes] == [("B-1", "3.000")]
    await _integridad_ok(admin)


async def test_stock_negativo_solo_con_autorizacion(admin: Sesion):
    venta, _ = await _almacenes(admin)
    p = await crear_producto(admin)
    async with SessionLocal() as s:
        bloqueo = await servicio_stock.bloquear(s, [p["id"]], [venta])
        with pytest.raises(Exception) as error:
            servicio_stock.mover(
                s,
                producto=bloqueo.productos[p["id"]],
                stock=bloqueo.stock(p["id"], venta),
                cantidad=Decimal("-1"),
                tipo=TipoMovimientoInventario.SALIDA_VENTA,
                costo_unitario=Decimal("0"),
                usuario_id=None,
            )
        assert getattr(error.value, "codigo", "") == "stock_insuficiente"
        await s.rollback()


# --- Inventario físico -------------------------------------------------------------------------------------


async def test_inventario_fisico_aplica_solo_la_diferencia(admin: Sesion, almacenero: Sesion):
    p = await crear_producto(admin)
    otro = await crear_producto(admin)
    await _cargar(admin, p["id"], "20")
    await _cargar(admin, otro["id"], "8")

    r = await almacenero.post("/inventario/fisicos", json={"producto_ids": [p["id"], otro["id"]]})
    assert r.status_code == 201, r.text
    inv = r.json()
    linea = next(d for d in inv["detalles"] if d["producto_id"] == p["id"])
    assert linea["stock_sistema"] == "20.000"

    # No se puede abrir otro conteo con los mismos productos
    r = await almacenero.post("/inventario/fisicos", json={"producto_ids": [p["id"]]})
    assert r.status_code == 409 and r.json()["codigo"] == "conteo_abierto"

    # Mientras se cuenta, sale mercadería (aquí un ajuste aprobado de -5)
    roto = await _motivo(admin, "Producto dañado o roto")
    aj = (
        await almacenero.post(
            "/inventario/ajustes", json={"motivo_id": roto, "detalles": [{"producto_id": p["id"], "cantidad": "-5"}]}
        )
    ).json()
    await admin.post(f"/inventario/ajustes/{aj['id']}/aprobar")
    assert await _stock(admin, p["id"]) == 15

    # Se contaron 18 (faltan 2 respecto a lo que había al contar); el otro producto no se contó
    r = await almacenero.put(
        f"/inventario/fisicos/{inv['id']}/conteos", json={"items": [{"detalle_id": linea["id"], "stock_contado": "18"}]}
    )
    assert r.json()["contadas"] == 1
    assert next(d for d in r.json()["detalles"] if d["id"] == linea["id"])["diferencia"] == "-2.000"
    assert (await almacenero.post(f"/inventario/fisicos/{inv['id']}/enviar")).json()["estado"] == (
        "PENDIENTE_APROBACION"
    )
    r = await admin.post(f"/inventario/fisicos/{inv['id']}/aprobar")
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "APLICADO"
    assert await _stock(admin, p["id"]) == 13  # 15 actuales - 2 de diferencia (no se pisa con 18)
    assert await _stock(admin, otro["id"]) == 8  # no contado: no cambia
    await _integridad_ok(admin)


async def test_inventario_fisico_rechazo_vuelve_a_contar(admin: Sesion, almacenero: Sesion):
    p = await crear_producto(admin)
    inv = (await almacenero.post("/inventario/fisicos", json={"producto_ids": [p["id"]]})).json()
    r = await almacenero.post(f"/inventario/fisicos/{inv['id']}/enviar")
    assert r.status_code == 422 and r.json()["codigo"] == "sin_conteo"
    await almacenero.put(
        f"/inventario/fisicos/{inv['id']}/conteos",
        json={"items": [{"detalle_id": inv["detalles"][0]["id"], "stock_contado": "3"}]},
    )
    await almacenero.post(f"/inventario/fisicos/{inv['id']}/enviar")
    r = await admin.post(f"/inventario/fisicos/{inv['id']}/rechazar", json={"motivo": "Recontar"})
    assert r.json()["estado"] == "EN_PROCESO" and r.json()["motivo_rechazo"] == "Recontar"
    assert (await almacenero.post(f"/inventario/fisicos/{inv['id']}/cancelar")).json()["estado"] == "CANCELADO"


# --- Kardex inmutable --------------------------------------------------------------------------------------


async def test_kardex_no_se_puede_modificar_ni_borrar(admin: Sesion):
    p = await crear_producto(admin)
    await _cargar(admin, p["id"], "3")
    async with SessionLocal() as s:
        fila = await s.scalar(text("SELECT id FROM movimientos_inventario WHERE producto_id = :p"), {"p": p["id"]})
        for sentencia in (
            "UPDATE movimientos_inventario SET cantidad = 100 WHERE id = :id",
            "DELETE FROM movimientos_inventario WHERE id = :id",
        ):
            with pytest.raises(DBAPIError) as error:
                await s.execute(text(sentencia), {"id": fila})
            assert error.value.orig.args[0] == 1644
            await s.rollback()


async def test_integridad_detecta_un_descuadre(admin: Sesion):
    p = await crear_producto(admin)
    await _cargar(admin, p["id"], "3")
    venta, _ = await _almacenes(admin)
    async with SessionLocal() as s, s.begin():
        fila = await s.scalar(select(StockAlmacen).where(StockAlmacen.producto_id == p["id"]))
        fila.cantidad = Decimal("99")  # alguien cambia el stock "a mano" sin kardex
    r = (await admin.get("/inventario/integridad")).json()
    assert not r["correcto"]
    assert any(x["tipo"] == "stock_vs_kardex" and x["producto_id"] == p["id"] for x in r["problemas"])
    async with SessionLocal() as s, s.begin():
        fila = await s.scalar(select(StockAlmacen).where(StockAlmacen.producto_id == p["id"]))
        fila.cantidad = Decimal("3")
    await _integridad_ok(admin)


async def test_cajero_no_ajusta_ni_ve_costos_en_inventario(admin: Sesion, cliente, crear_usuario):
    usuario, clave = await crear_usuario("Cajero")
    cajero = Sesion(cliente, await iniciar_sesion(cliente, usuario["username"], clave))
    r = await cajero.get("/inventario/resumen")
    assert r.status_code == 200 and r.json()["valor_total"] is None
    r = await cajero.post(
        "/inventario/ajustes", json={"motivo_id": 1, "detalles": [{"producto_id": 1, "cantidad": "1"}]}
    )
    assert r.status_code == 403
    assert (await cajero.post("/inventario/stock-inicial", json={"items": []})).status_code in (403, 422)
