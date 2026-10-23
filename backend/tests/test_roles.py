"""Roles y permisos."""

import uuid


async def test_catalogo_de_permisos(admin):
    r = await admin.get("/roles/permisos")
    modulos = r.json()
    assert r.status_code == 200 and len(modulos) == 16
    assert sum(len(m["permisos"]) for m in modulos) == 61


async def test_crear_editar_y_eliminar_rol(admin):
    nombre = f"Supervisor {uuid.uuid4().hex[:4]}"
    r = await admin.post("/roles", json={"nombre": nombre, "permisos": ["no.existe"]})
    assert r.status_code == 422
    r = await admin.post("/roles", json={"nombre": nombre, "permisos": ["pos.vender", "caja.ver"]})
    assert r.status_code == 201
    rol = r.json()
    assert (await admin.post("/roles", json={"nombre": nombre})).status_code == 409

    r = await admin.patch(f"/roles/{rol['id']}", json={"permisos": ["pos.vender"]})
    assert r.status_code == 200 and r.json()["permisos"] == ["pos.vender"]
    assert (await admin.delete(f"/roles/{rol['id']}")).status_code == 200


async def test_roles_del_sistema_protegidos(admin):
    roles = {r["nombre"]: r for r in (await admin.get("/roles")).json()}
    administrador = roles["Administrador"]
    assert administrador["total_permisos"] == 61
    assert (await admin.patch(f"/roles/{administrador['id']}", json={"permisos": []})).status_code == 422
    assert (await admin.delete(f"/roles/{roles['Cajero']['id']}")).status_code == 422
    r = await admin.patch(f"/roles/{roles['Cajero']['id']}", json={"nombre": "Otro nombre"})
    assert r.status_code == 422


async def test_no_se_elimina_un_rol_con_usuarios(admin, crear_usuario):
    r = await admin.post("/roles", json={"nombre": f"Temporal {uuid.uuid4().hex[:4]}", "permisos": []})
    rol = r.json()
    await crear_usuario(rol=rol["nombre"])
    r = await admin.delete(f"/roles/{rol['id']}")
    assert r.status_code == 409 and "usuario" in r.json()["detalle"]
