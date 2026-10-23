"""Auditoría: registro de eventos y resumen."""

from datetime import date

from tests.conftest import API


async def test_registra_ingresos_fallos_y_cambios(admin, cliente, crear_usuario):
    usuario, _ = await crear_usuario()
    await cliente.post(f"{API}/auth/login", json={"username": usuario["username"], "password": "Mala12345"})
    r = await admin.get("/auditoria", params={"tamanio": 100})
    acciones = {x["accion"] for x in r.json()["items"]}
    assert {"LOGIN", "LOGIN_FALLIDO", "CREAR"} <= acciones


async def test_resumen_del_dia_y_persona_a_revisar(admin, cliente, crear_usuario):
    usuario, _ = await crear_usuario()
    for _ in range(2):
        await cliente.post(f"{API}/auth/login", json={"username": usuario["username"], "password": "Mala12345"})
    hoy = date.today().isoformat()
    r = await admin.get("/auditoria/resumen", params={"desde": hoy, "hasta": hoy})
    datos = r.json()
    assert r.status_code == 200 and datos["fallos"] >= 2
    assert datos["revisar"]["usuario_id"] == usuario["id"]
    assert datos["total"] >= datos["ingresos"] + datos["fallos"] + datos["cambios"]


async def test_filtros_por_modulo(admin):
    r = await admin.get("/auditoria", params={"modulo": "auth"})
    assert r.status_code == 200 and all(x["modulo"] == "auth" for x in r.json()["items"])
