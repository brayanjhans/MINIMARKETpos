"""Gestión de usuarios: validaciones, permisos, protecciones y resumen."""

from tests.conftest import API, iniciar_sesion


async def test_crear_usuario_normaliza_el_username(admin, crear_usuario):
    usuario, _ = await crear_usuario(username="Ana.Prueba1")
    assert usuario["username"] == "ana.prueba1"
    assert usuario["sucursales"][0]["nombre"] == "Principal"


async def test_validaciones_al_crear(admin, crear_usuario):
    usuario, _ = await crear_usuario()
    base = {
        "nombre_completo": "Otra Persona",
        "rol_id": usuario["rol"]["id"],
        "sucursal_ids": [usuario["sucursales"][0]["id"]],
        "password": "Clave2026x",
    }
    r = await admin.post("/usuarios", json={**base, "username": "con espacio"})
    assert r.status_code == 422
    r = await admin.post("/usuarios", json={**base, "username": usuario["username"]})
    assert r.status_code == 409 and "ya existe" in r.json()["detalle"]
    r = await admin.post("/usuarios", json={**base, "username": "nuevo.x", "campo_raro": 1})
    assert r.status_code == 422
    r = await admin.post("/usuarios", json={**base, "username": "nuevo.y", "sucursal_ids": []})
    assert r.status_code == 422


async def test_listado_paginado_con_busqueda(admin, crear_usuario):
    usuario, _ = await crear_usuario()
    r = await admin.get("/usuarios", params={"busqueda": usuario["username"], "tamanio": 5, "orden": "-creado"})
    datos = r.json()
    assert r.status_code == 200 and datos["total"] == 1 and datos["tamanio"] == 5
    assert (await admin.get("/usuarios", params={"tamanio": 500})).status_code == 422


async def test_un_cajero_no_puede_ver_usuarios(cliente, crear_usuario):
    usuario, clave = await crear_usuario(rol="Cajero")
    headers = await iniciar_sesion(cliente, usuario["username"], clave)
    r = await cliente.get(f"{API}/usuarios", headers=headers)
    assert r.status_code == 403


async def test_protecciones_del_administrador(admin):
    yo = (await admin.get("/auth/me")).json()
    roles = (await admin.get("/roles")).json()
    cajero = next(r["id"] for r in roles if r["nombre"] == "Cajero")
    assert (await admin.patch(f"/usuarios/{yo['id']}", json={"activo": False})).status_code == 422
    r = await admin.patch(f"/usuarios/{yo['id']}", json={"rol_id": cajero})
    assert r.status_code == 422


async def test_quitar_acceso_cierra_sus_sesiones(admin, cliente, crear_usuario):
    usuario, clave = await crear_usuario()
    await iniciar_sesion(cliente, usuario["username"], clave)
    assert (await admin.patch(f"/usuarios/{usuario['id']}", json={"activo": False})).status_code == 200
    assert (await cliente.post(f"{API}/auth/refresh")).status_code == 401
    r = await cliente.post(f"{API}/auth/login", json={"username": usuario["username"], "password": clave})
    assert r.status_code == 401 and r.json()["codigo"] == "usuario_inactivo"


async def test_desbloquear(admin, cliente, crear_usuario):
    usuario, clave = await crear_usuario()
    for _ in range(5):
        await cliente.post(f"{API}/auth/login", json={"username": usuario["username"], "password": "Mala12345"})
    r = await admin.post(f"/usuarios/{usuario['id']}/desbloquear")
    assert r.status_code == 200 and r.json()["bloqueado_hasta"] is None
    await iniciar_sesion(cliente, usuario["username"], clave)


async def test_resumen_de_usuarios(admin, crear_usuario):
    antes = (await admin.get("/usuarios/resumen")).json()
    usuario, _ = await crear_usuario()
    await admin.patch(f"/usuarios/{usuario['id']}", json={"activo": False})
    despues = (await admin.get("/usuarios/resumen")).json()
    assert despues["sin_acceso"] == antes["sin_acceso"] + 1
    assert despues["con_acceso"] == antes["con_acceso"]
    assert despues["ingresaron_hoy"] >= 1
