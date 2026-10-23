"""Autenticación: login, bloqueos, refresh rotativo, cambio de contraseña y de sucursal."""

import asyncio

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal
from app.main import app
from tests.conftest import ADMIN, API, iniciar_sesion

MENSAJE = "Usuario o contraseña incorrectos"
COOKIE = settings.COOKIE_REFRESH_NOMBRE


async def test_login_correcto_entrega_token_y_cookie_segura(cliente):
    r = await cliente.post(f"{API}/auth/login", json={"username": " ADMIN ", "password": ADMIN[1]})
    assert r.status_code == 200
    cuerpo = r.json()
    assert "refresh_token" not in cuerpo  # el refresh solo viaja en la cookie
    assert cuerpo["usuario"]["sucursal_actual"]["nombre"] == "Principal"
    cookie = r.headers["set-cookie"].lower()
    assert f"{COOKIE}=" in cookie and "httponly" in cookie and "samesite=strict" in cookie


async def test_credenciales_incorrectas_no_revelan_si_el_usuario_existe(cliente):
    r1 = await cliente.post(f"{API}/auth/login", json={"username": "admin", "password": "mala"})
    r2 = await cliente.post(f"{API}/auth/login", json={"username": "no.existe", "password": "mala"})
    assert r1.status_code == r2.status_code == 401
    assert r1.json()["detalle"] == r2.json()["detalle"] == MENSAJE


async def test_rutas_protegidas_exigen_token_valido(cliente):
    assert (await cliente.get(f"{API}/auth/me")).json()["codigo"] == "sin_token"
    r = await cliente.get(f"{API}/auth/me", headers={"Authorization": "Bearer abc.def.ghi"})
    assert r.status_code == 401


async def test_bloqueo_tras_cinco_intentos_aunque_luego_acierte(cliente, crear_usuario):
    usuario, clave = await crear_usuario()
    for _ in range(5):
        await cliente.post(f"{API}/auth/login", json={"username": usuario["username"], "password": "Equivocada1"})
    r = await cliente.post(f"{API}/auth/login", json={"username": usuario["username"], "password": clave})
    assert r.status_code == 401 and r.json()["codigo"] == "usuario_bloqueado"


async def test_limite_de_intentos_por_ip_con_usuarios_distintos(cliente):
    sql = "UPDATE parametros_sistema SET valor = :v WHERE clave = 'seguridad.max_intentos_ip'"
    async with SessionLocal() as s, s.begin():
        await s.execute(text(sql), {"v": "3"})
    try:
        for i in range(3):
            r = await cliente.post(f"{API}/auth/login", json={"username": f"inventado{i}", "password": "x"})
            assert r.status_code == 401
        r = await cliente.post(f"{API}/auth/login", json={"username": "admin", "password": ADMIN[1]})
        assert r.status_code == 429 and r.json()["codigo"] == "limite_ip"
    finally:
        async with SessionLocal() as s, s.begin():
            await s.execute(text(sql), {"v": "20"})


async def test_refresh_rota_la_cookie_y_detecta_reutilizacion(cliente):
    await iniciar_sesion(cliente, *ADMIN)
    cookie_1 = cliente.cookies[COOKIE]
    r = await cliente.post(f"{API}/auth/refresh")
    assert r.status_code == 200 and cliente.cookies[COOKIE] != cookie_1

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as otra_pestana:
        # Dentro del periodo de gracia (dos pestañas a la vez) se acepta
        otra_pestana.cookies.set(COOKIE, cookie_1)
        assert (await otra_pestana.post(f"{API}/auth/refresh")).status_code == 200
        # Fuera del periodo de gracia es un robo: se cierran todas las sesiones
        gracia = settings.REFRESH_GRACIA_SEGUNDOS
        settings.REFRESH_GRACIA_SEGUNDOS = 0
        try:
            otra_pestana.cookies.clear()
            otra_pestana.cookies.set(COOKIE, cookie_1)
            r = await otra_pestana.post(f"{API}/auth/refresh")
            assert r.status_code == 401 and r.json()["codigo"] == "sesion_revocada"
        finally:
            settings.REFRESH_GRACIA_SEGUNDOS = gracia
    assert (await cliente.post(f"{API}/auth/refresh")).status_code == 401


async def test_logout_borra_la_cookie_y_cierra_la_sesion(cliente):
    await iniciar_sesion(cliente, *ADMIN)
    r = await cliente.post(f"{API}/auth/logout")
    assert r.status_code == 200 and COOKIE not in cliente.cookies
    assert (await cliente.post(f"{API}/auth/refresh")).status_code == 401


async def test_cambiar_password_invalida_los_tokens_anteriores(cliente, crear_usuario):
    usuario, clave = await crear_usuario()
    headers_viejos = await iniciar_sesion(cliente, usuario["username"], clave)
    await asyncio.sleep(1.1)  # los tokens tienen resolución de segundos
    r = await cliente.post(
        f"{API}/auth/cambiar-password",
        json={"password_actual": clave, "password_nueva": "NuevaClave99"},
        headers=headers_viejos,
    )
    assert r.status_code == 200
    nuevos = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert (await cliente.get(f"{API}/auth/me", headers=headers_viejos)).status_code == 401
    assert (await cliente.get(f"{API}/auth/me", headers=nuevos)).status_code == 200


async def test_password_debil_se_rechaza_en_espanol(cliente, crear_usuario):
    usuario, clave = await crear_usuario()
    headers = await iniciar_sesion(cliente, usuario["username"], clave)
    r = await cliente.post(
        f"{API}/auth/cambiar-password", json={"password_actual": clave, "password_nueva": "1234"}, headers=headers
    )
    assert r.status_code == 422 and "8 caracteres" in r.text


async def test_cambiar_sucursal_solo_a_las_asignadas(admin, db):
    await db.execute(text("INSERT INTO sucursales (codigo, nombre, activo) VALUES ('0077', 'Sucursal Test', 1)"))
    await db.commit()
    id_sur = (await db.execute(text("SELECT id FROM sucursales WHERE codigo = '0077'"))).scalar_one()
    try:
        r = await admin.post("/auth/cambiar-sucursal", json={"sucursal_id": id_sur})
        assert r.status_code == 403

        id_admin = (await admin.get("/auth/me")).json()["id"]
        await db.execute(text(f"INSERT INTO usuario_sucursales VALUES ({id_admin}, {id_sur})"))
        await db.commit()
        r = await admin.post("/auth/cambiar-sucursal", json={"sucursal_id": id_sur})
        assert r.status_code == 200 and r.json()["usuario"]["sucursal_actual"]["nombre"] == "Sucursal Test"
        # El refresh conserva la sucursal elegida
        r = await admin.cliente.post(f"{API}/auth/refresh")
        assert r.json()["usuario"]["sucursal_actual"]["nombre"] == "Sucursal Test"
    finally:
        await db.execute(text(f"DELETE FROM usuario_sucursales WHERE sucursal_id = {id_sur}"))
        await db.execute(text(f"DELETE FROM refresh_tokens WHERE sucursal_id = {id_sur}"))
        await db.execute(text(f"DELETE FROM sucursales WHERE id = {id_sur}"))
        await db.commit()
